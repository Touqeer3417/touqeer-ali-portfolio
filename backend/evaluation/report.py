"""Build and save transparent JSON reports for RAGAS runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any

from evaluation.config import METRIC_NAMES, REPORTS_DIR


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


def build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
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
