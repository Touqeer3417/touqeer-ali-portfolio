"""Run offline RAGAS evaluation against the existing portfolio RAG pipeline."""

from __future__ import annotations

import asyncio
import importlib.metadata
import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.rag import generate_answer, retrieve_documents, retrieval_query

logger = logging.getLogger("ragas_evaluation")

PACKAGE_DIR = Path(__file__).resolve().parent
DATASET_PATH = PACKAGE_DIR / "dataset.json"
REPORT_DIR = PACKAGE_DIR / "reports"
MAX_CONCURRENCY = 2
OPERATION_TIMEOUT_SECONDS = 180
METRIC_NAMES = (
    "context_recall",
    "context_precision",
    "answer_relevancy",
    "faithfulness",
)
METRIC_BOUNDS = {
    "context_recall": (0.0, 1.0),
    "context_precision": (0.0, 1.0),
    "answer_relevancy": (-1.0, 1.0),
    "faithfulness": (0.0, 1.0),
}


def load_dataset(path: Path = DATASET_PATH) -> list[dict[str, Any]]:
    """Load and validate references against the real Markdown knowledge base."""
    with path.open("r", encoding="utf-8") as file:
        samples = json.load(file)

    if not isinstance(samples, list) or not samples:
        raise ValueError("Evaluation dataset must be a non-empty JSON list.")

    knowledge_dir = PACKAGE_DIR.parent.parent / "knowledge"
    seen_ids: set[str] = set()
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise ValueError(f"Dataset row {index} must be an object.")
        for field in ("id", "user_input", "reference", "source_files"):
            if field not in sample:
                raise ValueError(f"Dataset row {index} is missing '{field}'.")
        for field in ("id", "user_input", "reference"):
            if not isinstance(sample[field], str) or not sample[field].strip():
                raise ValueError(f"Dataset row {index} has an empty '{field}'.")
        if sample["id"] in seen_ids:
            raise ValueError(f"Duplicate dataset id: {sample['id']}")
        seen_ids.add(sample["id"])
        if not isinstance(sample["source_files"], list) or not sample["source_files"]:
            raise ValueError(f"Dataset row {index} needs source_files.")
        for source_name in sample["source_files"]:
            if (
                not isinstance(source_name, str)
                or Path(source_name).name != source_name
                or not (knowledge_dir / source_name).is_file()
            ):
                raise ValueError(
                    f"Dataset row {index} references missing/invalid knowledge file: "
                    f"{source_name!r}"
                )
    return samples


def build_metric_objects(llm, embeddings) -> dict[str, Any]:
    """Create the four RAGAS Collections API metrics."""
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )

    return {
        "context_recall": ContextRecall(llm=llm),
        "context_precision": ContextPrecision(llm=llm),
        "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
        "faithfulness": Faithfulness(llm=llm),
    }


def build_metrics():
    """Initialize RAGAS judges using the existing OpenAI model settings."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import llm_factory

    llm = llm_factory(settings.chat_model, client=client)
    embeddings = embedding_factory(
        "openai",
        model=settings.embed_model,
        client=client,
    )
    return build_metric_objects(llm, embeddings), client


async def _score_one(metric, inputs: dict[str, Any]) -> float:
    result = await asyncio.wait_for(
        metric.ascore(**inputs),
        timeout=OPERATION_TIMEOUT_SECONDS,
    )
    value = getattr(result, "value", None)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"RAGAS returned a non-numeric score: {value!r}")
    score = float(value)
    if not math.isfinite(score):
        raise ValueError(f"RAGAS returned a non-finite score: {score!r}")
    return score


async def evaluate_sample(
    sample: dict[str, Any],
    metrics: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    """Retrieve once, generate once, and score the exact captured trace."""
    result: dict[str, Any] = {
        "id": sample["id"],
        "question": sample["user_input"],
        "reference": sample["reference"],
        "source_files": sample["source_files"],
        "retrieved_contexts": [],
        "generated_answer": None,
        "scores": {name: None for name in METRIC_NAMES},
        "metric_errors": {},
        "status": "failed",
    }

    async with semaphore:
        messages = [{"role": "user", "content": sample["user_input"]}]
        query = retrieval_query(messages)
        try:
            documents = await asyncio.wait_for(
                asyncio.to_thread(retrieve_documents, query),
                timeout=OPERATION_TIMEOUT_SECONDS,
            )
            # Preserve Qdrant's original hybrid RRF order exactly.
            contexts = [document.page_content for document in documents]
            result["retrieved_contexts"] = contexts

            answer = await asyncio.wait_for(
                asyncio.to_thread(generate_answer, messages, documents),
                timeout=OPERATION_TIMEOUT_SECONDS,
            )
            result["generated_answer"] = answer
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            result["pipeline_error"] = message
            for metric_name in METRIC_NAMES:
                result["metric_errors"][metric_name] = (
                    "Not evaluated because retrieval or answer generation failed."
                )
            logger.exception("RAG pipeline failed for evaluation sample %s", sample["id"])
            return result

        metric_inputs = {
            "context_recall": {
                "user_input": sample["user_input"],
                "retrieved_contexts": contexts,
                "reference": sample["reference"],
            },
            "context_precision": {
                "user_input": sample["user_input"],
                "retrieved_contexts": contexts,
                "reference": sample["reference"],
            },
            "answer_relevancy": {
                "user_input": sample["user_input"],
                "response": answer,
            },
            "faithfulness": {
                "user_input": sample["user_input"],
                "response": answer,
                "retrieved_contexts": contexts,
            },
        }

        for metric_name in METRIC_NAMES:
            try:
                score = await _score_one(
                    metrics[metric_name],
                    metric_inputs[metric_name],
                )
                lower, upper = METRIC_BOUNDS[metric_name]
                if score < lower or score > upper:
                    raise ValueError(
                        f"Score {score} is outside documented range [{lower}, {upper}]."
                    )
                result["scores"][metric_name] = score
            except Exception as exc:
                result["metric_errors"][metric_name] = (
                    f"{type(exc).__name__}: {exc}"
                )
                logger.exception(
                    "Metric %s failed for sample %s", metric_name, sample["id"]
                )

    result["status"] = (
        "success"
        if all(result["scores"][name] is not None for name in METRIC_NAMES)
        else "partial_failure"
    )
    return result


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate only successful numeric values; never substitute zero."""
    averages = {}
    for metric_name in METRIC_NAMES:
        values = [
            row["scores"][metric_name]
            for row in results
            if isinstance(row.get("scores", {}).get(metric_name), (int, float))
        ]
        averages[metric_name] = (
            {
                "score": sum(values) / len(values),
                "percentage": (
                    sum(values) / len(values) * 100
                    if metric_name != "answer_relevancy"
                    else None
                ),
                "successful_scores": len(values),
            }
            if values
            else {
                "score": None,
                "percentage": None,
                "successful_scores": 0,
                "status": "unavailable",
            }
        )

    return {
        "total_samples": len(results),
        "successfully_evaluated_samples": sum(
            row["status"] == "success" for row in results
        ),
        "partially_evaluated_samples": sum(
            row["status"] == "partial_failure" for row in results
        ),
        "failed_samples": sum(row["status"] == "failed" for row in results),
        "average_scores": averages,
    }


async def run_evaluation() -> Path:
    samples = load_dataset()
    metrics, client = build_metrics()
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    try:
        results = await asyncio.gather(
            *(evaluate_sample(sample, metrics, semaphore) for sample in samples)
        )
    finally:
        await client.close()

    report = {
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "ragas_version": importlib.metadata.version("ragas"),
        "evaluator_model": settings.chat_model,
        "embedding_model": settings.embed_model,
        **summarize(results),
        "results": results,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"ragas-evaluation-{timestamp}.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report_path


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    report_path = asyncio.run(run_evaluation())
    report = json.loads(report_path.read_text(encoding="utf-8"))
    print(f"RAGAS report: {report_path}")
    print(json.dumps(report, indent=2, ensure_ascii=False)[:12000])
    if report["successfully_evaluated_samples"] == 0:
        raise SystemExit("No evaluation sample completed all four metrics.")


if __name__ == "__main__":
    main()
