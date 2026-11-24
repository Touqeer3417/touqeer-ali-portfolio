"""Run the dataset through the existing RAG assistant and score it with RAGAS."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from evaluation.dataset import load_dataset
from evaluation.metrics import score_sample
from evaluation.pipeline_adapter import run_existing_pipeline
from evaluation.report import build_report, save_report


logger = logging.getLogger("rag_evaluation")


async def evaluate_dataset(warmup: bool = False, dataset_path: Path | None = None) -> dict[str, Any]:
    """Evaluate cases sequentially to isolate capture and avoid API bursts.

    With ``warmup`` one throwaway pipeline call runs first (not scored, not in
    the report) so model/index/connection start-up cost does not land on the
    first real sample's latency.
    """
    cases = load_dataset(dataset_path) if dataset_path else load_dataset()
    results: list[dict[str, Any]] = []
    metrics = None

    if warmup:
        logger.info("Warm-up request (excluded from results): %s", cases[0].case_id)
        await run_existing_pipeline(cases[0].user_input)

    for index, case in enumerate(cases, start=1):
        logger.info("Evaluating case %d/%d: %s", index, len(cases), case.case_id)
        try:
            output = await run_existing_pipeline(case.user_input)
            row: dict[str, Any] = {
                "id": case.case_id,
                "user_input": case.user_input,
                "reference": case.reference,
                "retrieved_contexts": output.retrieved_contexts,
                "retrieval_trace": output.retrieval_trace,
                "response": output.response,
                "status": output.status,
                "latency_ms": output.latency,
                "metric_scores": {},
                "metric_errors": {},
            }
            if case.reference is None and output.status == "complete":
                row["status"] = "incomplete"
                row["error"] = "Ground-truth reference is missing; reference-based metrics were not evaluated."
            if output.status != "complete":
                row["error"] = output.error
            else:
                if metrics is None:
                    from evaluation.metrics import build_metrics

                    metrics = build_metrics()
                scores, errors = await score_sample(
                    user_input=case.user_input,
                    response=output.response,
                    retrieved_contexts=output.retrieved_contexts,
                    reference=case.reference,
                    metrics=metrics,
                )
                row["metric_scores"] = scores
                row["metric_errors"] = errors
                if errors and case.reference is not None:
                    row["status"] = "completed_with_metric_errors"
            results.append(row)
        except Exception as exc:
            logger.exception("Evaluation case failed: %s", case.case_id)
            results.append({
                "id": case.case_id,
                "user_input": case.user_input,
                "reference": case.reference,
                "retrieved_contexts": [],
                "retrieval_trace": None,
                "response": None,
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "latency_ms": None,
                "metric_scores": {},
                "metric_errors": {},
            })

    return build_report(results, warmup=warmup)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warmup",
        action="store_true",
        help="Run one unscored request first so the first sample is not a cold start.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help="Dataset JSON to evaluate (default: datasets/evaluation_dataset.json). "
        "Use datasets/evaluation_dataset_extended.json for the larger set.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    report = asyncio.run(evaluate_dataset(warmup=args.warmup, dataset_path=args.dataset))
    path = save_report(report)
    print(json.dumps({"report": str(path), "total_evaluation_samples": report["total_evaluation_samples"], "metric_summary": report["metric_summary"], "latency_summary": report["latency_summary"], "failed_or_incomplete_count": len(report["failed_or_incomplete_samples"])}, indent=2))


if __name__ == "__main__":
    main()
