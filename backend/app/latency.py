"""Lightweight request-local RAG latency measurements and aggregation."""

from __future__ import annotations

import json
import logging
import math
import uuid
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import asdict, dataclass, field
from math import ceil
from threading import Lock
from time import perf_counter
from typing import Iterable, Iterator


logger = logging.getLogger("rag_latency")
LATENCY_FIELDS = (
    "total_ms",
    "embedding_ms",
    "vector_search_ms",
    "retrieval_ms",
    "reranking_ms",
    "prompt_build_ms",
    "llm_ms",
    "ttft_ms",
    "llm_ttft_ms",
    "overhead_ms",
)

# Stages that may be recorded through record_stage()/timer().
_STAGES = frozenset(
    {
        "embedding_ms",
        "vector_search_ms",
        "retrieval_ms",
        "reranking_ms",
        "prompt_build_ms",
        "llm_ms",
    }
)


@dataclass
class RequestLatency:
    """Mutable timer for one request; values are durations in milliseconds."""

    started_at: float = field(default_factory=perf_counter)
    values: dict[str, float] = field(default_factory=dict)
    ttft_ms: float | None = None
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    llm_started_at: float | None = None
    llm_ttft_ms: float | None = None
    flags: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class LatencyRecord:
    """Completed request timings. Unavailable or unexecuted stages are null.

    Field semantics (all milliseconds):
    - retrieval_ms contains embedding_ms, vector_search_ms and reranking_ms
      (nested, and dense/BM25 retrieval run concurrently, so never add them up).
    - ttft_ms is measured from request start (what the visitor waits).
    - llm_ttft_ms is measured from the start of the LLM call only.
    - overhead_ms = total - (retrieval + prompt_build + llm): unmeasured gap.
    """

    total_ms: float
    embedding_ms: float | None
    retrieval_ms: float | None
    reranking_ms: float | None
    llm_ms: float | None
    ttft_ms: float | None
    # Added fields keep defaults so older callers and reports stay compatible.
    request_id: str | None = None
    vector_search_ms: float | None = None
    prompt_build_ms: float | None = None
    llm_ttft_ms: float | None = None
    overhead_ms: float | None = None
    flags: dict[str, bool] = field(default_factory=dict)


_current_request: ContextVar[RequestLatency | None] = ContextVar(
    "rag_latency_current_request", default=None
)
_last_completed: ContextVar[LatencyRecord | None] = ContextVar(
    "rag_latency_last_completed", default=None
)
_records: deque[LatencyRecord] = deque(maxlen=1000)
_records_lock = Lock()


_pending_request_id: ContextVar[str | None] = ContextVar(
    "rag_latency_pending_request_id", default=None
)


@contextmanager
def use_request_id(request_id: str) -> Iterator[None]:
    """Let the next begin_request() in this context adopt a caller-issued id.

    Keeps ``stream_answer(messages)`` unchanged: the API (and the evaluation
    adapter) choose the id, the pipeline picks it up when its timer starts.
    """
    token = _pending_request_id.set(request_id)
    try:
        yield
    finally:
        _pending_request_id.reset(token)


def begin_request(request_id: str | None = None) -> tuple[RequestLatency, Token]:
    """Start request timing and bind it to the current async context."""
    request_id = request_id or _pending_request_id.get()
    request = RequestLatency(request_id=request_id) if request_id else RequestLatency()
    return request, _current_request.set(request)


def record_stage(stage: str, duration_ms: float) -> None:
    """Accumulate an already-measured component duration without new work."""
    record_stage_for(_current_request.get(), stage, duration_ms)


def current_request_latency() -> RequestLatency | None:
    """Expose the current request timer to wrappers that execute in worker threads."""
    return _current_request.get()


def record_stage_for(request: RequestLatency | None, stage: str, duration_ms: float) -> None:
    """Record into an explicitly captured timer, including from executor threads."""
    if request is None or stage not in _STAGES:
        return
    request.values[stage] = request.values.get(stage, 0.0) + max(0.0, duration_ms)


@contextmanager
def timer(stage: str, request: RequestLatency | None = None) -> Iterator[None]:
    """Time the enclosed block into the current (or given) request.

    Exception-safe: the duration is recorded in ``finally`` so a failing stage
    still reports its partial time. ``await`` inside the block is timed fully.
    The request is captured on entry, so the block may finish in another thread.
    A no-op when no request is active (e.g. command-line callers).
    """
    target = request if request is not None else _current_request.get()
    started = perf_counter()
    try:
        yield
    finally:
        record_stage_for(target, stage, (perf_counter() - started) * 1000)


def set_flag(name: str, value: bool = True) -> None:
    """Mark the current request, e.g. ``cross_encoder_cold`` on a cold model load."""
    request = _current_request.get()
    if request is not None:
        request.flags[name] = value


def mark_llm_start() -> None:
    """Remember when LLM streaming began so llm_ttft_ms excludes retrieval time."""
    request = _current_request.get()
    if request is not None and request.llm_started_at is None:
        request.llm_started_at = perf_counter()


def mark_first_token() -> None:
    """Record first-token latency from request start and, if known, from LLM start."""
    request = _current_request.get()
    if request is None:
        return
    now = perf_counter()
    if request.ttft_ms is None:
        request.ttft_ms = (now - request.started_at) * 1000
    if request.llm_ttft_ms is None and request.llm_started_at is not None:
        request.llm_ttft_ms = (now - request.llm_started_at) * 1000


def finish_request(request: RequestLatency) -> LatencyRecord:
    """Finalize and store the request timing record."""
    total_ms = max(0.0, (perf_counter() - request.started_at) * 1000)
    retrieval_ms = request.values.get("retrieval_ms")
    llm_ms = request.values.get("llm_ms")
    prompt_build_ms = request.values.get("prompt_build_ms")
    # Only defined for full requests; short-circuit paths have no LLM stage.
    overhead_ms = (
        total_ms - (retrieval_ms + (prompt_build_ms or 0.0) + llm_ms)
        if retrieval_ms is not None and llm_ms is not None
        else None
    )
    record = LatencyRecord(
        total_ms=total_ms,
        embedding_ms=request.values.get("embedding_ms"),
        retrieval_ms=retrieval_ms,
        reranking_ms=request.values.get("reranking_ms"),
        llm_ms=llm_ms,
        ttft_ms=request.ttft_ms,
        request_id=request.request_id,
        vector_search_ms=request.values.get("vector_search_ms"),
        prompt_build_ms=prompt_build_ms,
        llm_ttft_ms=request.llm_ttft_ms,
        overhead_ms=overhead_ms,
        flags=dict(request.flags),
    )
    with _records_lock:
        _records.append(record)
    _last_completed.set(record)
    logger.info("rag_latency %s", json.dumps(asdict(record), separators=(",", ":")))
    return record


def reset_request(token: Token) -> None:
    """Restore the previous request context after stream completion."""
    _current_request.reset(token)


def last_completed_latency() -> LatencyRecord | None:
    """Return the completed request record for this async context."""
    return _last_completed.get()


def recent_latency_records() -> list[LatencyRecord]:
    """Return a thread-safe copy of the bounded in-process sample window."""
    with _records_lock:
        return list(_records)


def get_record(request_id: str) -> LatencyRecord | None:
    """Look up a completed request by id (in-process window of the last 1000)."""
    with _records_lock:
        for record in reversed(_records):
            if record.request_id == request_id:
                return record
    return None


def public_latency(record: LatencyRecord) -> dict[str, object]:
    """Client-facing view: rounded to 0.1 ms, stable names, no user content.

    Rounded to one decimal (not whole ms) because prompt_build is sub-millisecond
    and would otherwise read as a suspicious 0.
    """

    def r(value: float | None) -> float | None:
        return None if value is None else round(value, 1)

    return {
        "request_id": record.request_id,
        "embedding": r(record.embedding_ms),
        "vector_search": r(record.vector_search_ms),
        "retrieval_total": r(record.retrieval_ms),
        "rerank": r(record.reranking_ms),
        "prompt_build": r(record.prompt_build_ms),
        "llm_ttft": r(record.llm_ttft_ms),
        "llm_total": r(record.llm_ms),
        "ttft_from_request_start": r(record.ttft_ms),
        "overhead": r(record.overhead_ms),
        "total": r(record.total_ms),
        "flags": dict(record.flags),
    }


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, ceil(percentile * len(ordered)) - 1)]


def aggregate_latency(records: Iterable[LatencyRecord]) -> dict[str, object]:
    """Summarize timings with nearest-rank percentiles; null samples are omitted."""
    rows = list(records)
    summary: dict[str, object] = {"sample_count": len(rows), "percentile_method": "nearest_rank"}
    for field_name in LATENCY_FIELDS:
        values = [
            float(value)
            for row in rows
            if (value := getattr(row, field_name)) is not None
            and math.isfinite(float(value))
        ]
        values.sort()
        summary[field_name] = {
            "count": len(values),
            "average": sum(values) / len(values) if values else None,
            "minimum": values[0] if values else None,
            "maximum": values[-1] if values else None,
            "p50": _percentile(values, 0.50),
            "p95": _percentile(values, 0.95),
            "p99": _percentile(values, 0.99),
        }
    return summary
