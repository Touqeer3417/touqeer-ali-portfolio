"""Lightweight request-local RAG latency measurements and aggregation."""

from __future__ import annotations

import json
import logging
import math
from collections import deque
from contextvars import ContextVar, Token
from dataclasses import asdict, dataclass, field
from math import ceil
from threading import Lock
from time import perf_counter
from typing import Iterable


logger = logging.getLogger("rag_latency")
LATENCY_FIELDS = (
    "total_ms",
    "embedding_ms",
    "retrieval_ms",
    "reranking_ms",
    "llm_ms",
    "ttft_ms",
)


@dataclass
class RequestLatency:
    """Mutable timer for one request; values are durations in milliseconds."""

    started_at: float = field(default_factory=perf_counter)
    values: dict[str, float] = field(default_factory=dict)
    ttft_ms: float | None = None


@dataclass(frozen=True)
class LatencyRecord:
    """Completed request timings. Unavailable or unexecuted stages are null."""

    total_ms: float
    embedding_ms: float | None
    retrieval_ms: float | None
    reranking_ms: float | None
    llm_ms: float | None
    ttft_ms: float | None


_current_request: ContextVar[RequestLatency | None] = ContextVar(
    "rag_latency_current_request", default=None
)
_last_completed: ContextVar[LatencyRecord | None] = ContextVar(
    "rag_latency_last_completed", default=None
)
_records: deque[LatencyRecord] = deque(maxlen=1000)
_records_lock = Lock()


def begin_request() -> tuple[RequestLatency, Token]:
    """Start request timing and bind it to the current async context."""
    request = RequestLatency()
    return request, _current_request.set(request)


def record_stage(stage: str, duration_ms: float) -> None:
    """Accumulate an already-measured component duration without new work."""
    record_stage_for(_current_request.get(), stage, duration_ms)


def current_request_latency() -> RequestLatency | None:
    """Expose the current request timer to wrappers that execute in worker threads."""
    return _current_request.get()


def record_stage_for(request: RequestLatency | None, stage: str, duration_ms: float) -> None:
    """Record into an explicitly captured timer, including from executor threads."""
    if request is None or stage not in {
        "embedding_ms",
        "retrieval_ms",
        "reranking_ms",
        "llm_ms",
    }:
        return
    request.values[stage] = request.values.get(stage, 0.0) + max(0.0, duration_ms)


def mark_first_token() -> None:
    """Record time from request start to the first nonempty generated token."""
    request = _current_request.get()
    if request is not None and request.ttft_ms is None:
        request.ttft_ms = (perf_counter() - request.started_at) * 1000


def finish_request(request: RequestLatency) -> LatencyRecord:
    """Finalize and store the request timing record."""
    record = LatencyRecord(
        total_ms=max(0.0, (perf_counter() - request.started_at) * 1000),
        embedding_ms=request.values.get("embedding_ms"),
        retrieval_ms=request.values.get("retrieval_ms"),
        reranking_ms=request.values.get("reranking_ms"),
        llm_ms=request.values.get("llm_ms"),
        ttft_ms=request.ttft_ms,
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
