"""Build and save transparent JSON reports for RAGAS runs."""

from __future__ import annotations

import json
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any

from app.latency import LatencyRecord, aggregate_latency
from evaluation.config import METRIC_NAMES, REPORTS_DIR

_LATENCY_KEYS = {item.name for item in fields(LatencyRecord)}
P95_MIN_SAMPLES = 20


def _latency_problems(record: LatencyRecord) -> list[str]:
    """Flag timings that look wrong rather than slow."""
    problems: list[str] = []
    for name in ("total_ms", "embedding_ms", "vector_search_ms", "retrieval_ms", "llm_ms"):
        value = getattr(record, name)
        if value is not None and value <= 0.0:
            problems.append(f"{name}_not_positive")
    if record.overhead_ms is not None:
        if record.overhead_ms < -1.0:
            problems.append("negative_overhead")
        elif record.overhead_ms > max(50.0, 0.05 * record.total_ms):
            problems.append("large_unmeasured_overhead")
    if (
        record.embedding_ms is not None
        and record.vector_search_ms is not None
        and record.retrieval_ms is not None
        and record.embedding_ms + record.vector_search_ms > record.retrieval_ms * 1.05
    ):
        problems.append("embedding_plus_vector_search_exceeds_retrieval")
    return problems


def _latency_summary(results: list[dict[str, Any]], warmup: bool) -> dict[str, Any]:
    """p50/p95/mean per stage from the production pipeline's own timings.

    ``all`` includes every sample. ``warm`` drops the first measured sample (a
    cold start) unless a warm-up request already ran, plus any sample the
    pipeline itself flagged cold (cross-encoder load, BM25 index build).
    """
    entries: list[tuple[Any, LatencyRecord]] = []
    for row in results:
        timing = row.get("latency_ms")
        if isinstance(timing, dict):
            entries.append((row.get("id"), LatencyRecord(**{k: v for k, v in timing.items() if k in _LATENCY_KEYS})))

    warm: list[LatencyRecord] = []
    excluded: list[dict[str, Any]] = []
    for position, (case_id, record) in enumerate(entries):
        reasons = sorted(name for name, active in record.flags.items() if active)
        if position == 0 and not warmup:
            reasons.insert(0, "first_request_no_warmup")
        if reasons:
            excluded.append({"id": case_id, "reasons": reasons})
        else:
            warm.append(record)

    return {
        "units": "milliseconds",
        "stage_semantics": {
            "retrieval_ms": "Contains embedding_ms, vector_search_ms and reranking_ms (nested; dense and BM25 run concurrently, so do not add them).",
            "vector_search_ms": "Derived: dense retriever call minus the query embedding recorded inside it (langchain-qdrant fuses them).",
            "ttft_ms": "From request start to first token (includes retrieval).",
            "llm_ttft_ms": "From the start of the LLM call to first token.",
            "overhead_ms": "total - (retrieval + prompt_build + llm): time not attributed to a stage.",
        },
        "all": aggregate_latency(record for _, record in entries),
        "warm": aggregate_latency(warm),
        "warm_excluded_samples": excluded,
        "p95_reliable": len(warm) >= P95_MIN_SAMPLES,
        "p95_min_samples": P95_MIN_SAMPLES,
        "suspicious_samples": [
            {"id": case_id, "problems": problems}
            for case_id, record in entries
            if (problems := _latency_problems(record))
        ],
    }


def _retrieval_diagnostics(results: list[dict[str, Any]]) -> dict[str, Any]:
    traces = [row["retrieval_trace"] for row in results if isinstance(row.get("retrieval_trace"), dict)]
    named_project = [trace for trace in traces if trace.get("project_filter")]
    enabled = [trace for trace in traces if trace.get("reranker_enabled")]
    reranker_successes = sum(trace.get("reranker_status") == "success" for trace in enabled)
    return {
        "traced_samples": len(traces),
        "samples_with_named_project_filter": len(named_project),
        "mean_dense_candidates": fmean(trace.get("dense_candidate_count", 0) for trace in traces) if traces else None,
        "mean_bm25_candidates": fmean(trace.get("bm25_candidate_count", 0) for trace in traces) if traces else None,
        "mean_fused_candidates": fmean(trace.get("fused_candidate_count", 0) for trace in traces) if traces else None,
        "reranker_enabled_samples": len(enabled),
        "reranker_execution_success_rate": reranker_successes / len(enabled) if enabled else None,
        "project_query_correct_retrieval_rate": (
            sum((trace.get("project_relevant_final_count") or 0) > 0 for trace in named_project) / len(named_project)
            if named_project else None
        ),
        "relevant_project_chunks_in_candidates": sum(trace.get("project_relevant_candidate_count") or 0 for trace in named_project),
        "relevant_project_chunks_in_final_top_k": sum(trace.get("project_relevant_final_count") or 0 for trace in named_project),
        "incorrect_project_chunks_in_final_top_k": sum(trace.get("incorrect_project_final_count") or 0 for trace in named_project),
        "incorrect_project_chunks_per_named_project_query": (
            fmean(trace.get("incorrect_project_final_count") or 0 for trace in named_project)
            if named_project else None
        ),
    }


def build_report(results: list[dict[str, Any]], warmup: bool = False) -> dict[str, Any]:
    """Aggregate only numeric RAGAS results and retain every case outcome."""
    summaries: dict[str, dict[str, float | int | None]] = {}
    for name in METRIC_NAMES:
        values = [
            score for row in results
            if isinstance((score := row.get("metric_scores", {}).get(name)), (int, float))
        ]
        summaries[name] = {
            "mean": fmean(values) if values else None,
            "scored_samples": len(values),
        }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_evaluation_samples": len(results),
        "metric_summary": summaries,
        "retrieval_diagnostics": _retrieval_diagnostics(results),
        "latency_summary": _latency_summary(results, warmup),
        "failed_or_incomplete_samples": [
            row for row in results if row.get("status") != "complete" or row.get("metric_errors")
        ],
        "samples": results,
    }


def save_report(report: dict[str, Any], reports_dir: Path = REPORTS_DIR) -> Path:
    """Write a unique UTF-8 JSON report without replacing earlier runs."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = reports_dir / f"ragas_{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
