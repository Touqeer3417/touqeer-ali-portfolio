"""Run the existing question set once through the RAG pipeline and report latency."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.latency import LatencyRecord, aggregate_latency, last_completed_latency
from evaluation.dataset import load_dataset
from evaluation.pipeline_adapter import run_existing_pipeline


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = BACKEND_DIR / "evaluation" / "reports" / "6.json"
REPORTS_DIR = BACKEND_DIR / "latency_reports"
logger = logging.getLogger("rag_latency_benchmark")


def _content_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _baseline_samples(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        logger.warning("Baseline report not found; output comparisons will be unavailable: %s", path)
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(sample["id"]): sample
        for sample in data.get("samples", [])
        if isinstance(sample, dict) and sample.get("id") is not None
    }


async def run_benchmark(baseline_path: Path = DEFAULT_BASELINE) -> dict[str, Any]:
    """Measure one real pipeline execution per dataset question; no RAGAS calls."""
    baseline = _baseline_samples(baseline_path)
    rows: list[dict[str, Any]] = []
    records: list[LatencyRecord] = []

    for case in load_dataset():
        logger.info("Latency query %s", case.case_id)
        output = await run_existing_pipeline(case.user_input)
        timing = last_completed_latency()
        if timing is not None:
            records.append(timing)
        prior = baseline.get(case.case_id)
        rows.append(
            {
                "id": case.case_id,
                "status": output.status,
                "latency_ms": asdict(timing) if timing is not None else None,
                "output_comparison_to_baseline": {
                    "baseline_report": str(baseline_path) if prior is not None else None,
                    "retrieved_contexts_unchanged": (
                        _content_hash(output.retrieved_contexts)
                        == _content_hash(prior.get("retrieved_contexts"))
                        if prior is not None
                        else None
                    ),
                    "generated_response_unchanged": (
                        _content_hash(output.response) == _content_hash(prior.get("response"))
                        if prior is not None
                        else None
                    ),
                },
            }
        )

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_queries": len(rows),
        "aggregate_latency_ms": aggregate_latency(records),
        "timing_semantics": {
            "total_ms": "From stream_answer entry through completion of the full streamed response.",
            "embedding_ms": "Existing query-embedding call duration; nested inside retrieval_ms.",
            "retrieval_ms": "Existing retriever duration, including embedding, dense/BM25 retrieval, fusion and reranking.",
            "reranking_ms": "Existing Cross-Encoder scoring/reordering duration; nested inside retrieval_ms.",
            "llm_ms": "Existing streamed LLM duration until its stream is exhausted; excludes final note formatting.",
            "ttft_ms": "Request start to first nonempty generated token; null when no generated token is produced.",
            "percentiles": "Nearest-rank percentiles. Unavailable component samples are excluded from that component's statistics.",
        },
        "samples": rows,
    }


def save_report(report: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = REPORTS_DIR / f"latency_{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Prior RAG report used only to compare retrieved contexts and answers.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for name in ("rag", "httpx", "httpx2"):
        logging.getLogger(name).setLevel(logging.WARNING)
    report = asyncio.run(run_benchmark(args.baseline))
    path = save_report(report)
    print(json.dumps({
        "report": str(path),
        "total_queries": report["total_queries"],
        "aggregate_latency_ms": report["aggregate_latency_ms"],
        "response_match_count": sum(
            sample["output_comparison_to_baseline"]["generated_response_unchanged"] is True
            for sample in report["samples"]
        ),
        "context_match_count": sum(
            sample["output_comparison_to_baseline"]["retrieved_contexts_unchanged"] is True
            for sample in report["samples"]
        ),
    }, indent=2))


if __name__ == "__main__":
    main()
