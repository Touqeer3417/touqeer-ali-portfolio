"""Unit tests for the isolated offline RAGAS evaluation runner."""

import importlib.util
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# Settings are loaded at app import time; provide test-only placeholders.
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key-not-used")
os.environ.setdefault("QDRANT_URL", "https://qdrant.invalid")
os.environ.setdefault("QDRANT_API_KEY", "test-qdrant-key-not-used")
os.environ.setdefault("SHARED_SECRET", "test-shared-secret-at-least-24")

from app.evaluation import runner


def sample():
    return {
        "id": "unit_01",
        "user_input": "What is Touqeer studying?",
        "reference": "Touqeer is studying BS Software Engineering at NUML University.",
        "source_files": ["about.md"],
    }


class FakeMetric:
    def __init__(self, value=0.8, error=None):
        self.value = value
        self.error = error
        self.inputs = []

    async def ascore(self, **kwargs):
        self.inputs.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(value=self.value)


class DatasetTests(unittest.TestCase):
    def test_dataset_is_valid_and_references_existing_knowledge_files(self):
        dataset = runner.load_dataset()
        self.assertGreaterEqual(len(dataset), 15)
        self.assertEqual(len({item["id"] for item in dataset}), len(dataset))
        self.assertTrue(all(item["reference"].strip() for item in dataset))

    def test_missing_source_file_is_rejected(self):
        invalid = [sample()]
        invalid[0]["source_files"] = ["not-a-real-knowledge-file.md"]
        import tempfile
        import json
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dataset.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaises(ValueError):
                runner.load_dataset(path)


class MetricFactoryTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("ragas"), "RAGAS evaluation extra is not installed")
    def test_collections_metric_classes_are_importable(self):
        from ragas.metrics.collections import (
            AnswerRelevancy,
            ContextPrecision,
            ContextRecall,
            Faithfulness,
        )

        self.assertTrue(all(callable(metric) for metric in (
            AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness
        )))

    @unittest.skipUnless(importlib.util.find_spec("ragas"), "RAGAS evaluation extra is not installed")
    def test_all_four_metric_constructors_are_called(self):
        from ragas import metrics as _metrics  # noqa: F401
        from ragas.metrics import collections

        names = ("ContextRecall", "ContextPrecision", "AnswerRelevancy", "Faithfulness")
        patches = [patch.object(collections, name) for name in names]
        mocks = [item.start() for item in patches]
        try:
            result = runner.build_metric_objects(object(), object())
            self.assertEqual(set(result), set(runner.METRIC_NAMES))
            for metric_mock in mocks:
                metric_mock.assert_called_once()
        finally:
            for item in patches:
                item.stop()


class EvaluationTraceTests(unittest.IsolatedAsyncioTestCase):
    async def test_retrieves_once_preserves_order_and_scores_exact_trace(self):
        docs = [
            SimpleNamespace(page_content="first retrieved passage"),
            SimpleNamespace(page_content="second retrieved passage"),
        ]
        metric_map = {name: FakeMetric(0.7) for name in runner.METRIC_NAMES}
        with (
            patch.object(runner, "retrieve_documents", return_value=docs) as retrieve,
            patch.object(runner, "generate_answer", return_value="Generated answer grounded in context.") as generate,
        ):
            result = await runner.evaluate_sample(
                sample(), metric_map, runner.asyncio.Semaphore(1)
            )

        retrieve.assert_called_once()
        generate.assert_called_once()
        self.assertEqual(
            result["retrieved_contexts"],
            ["first retrieved passage", "second retrieved passage"],
        )
        self.assertEqual(result["generated_answer"], "Generated answer grounded in context.")
        self.assertEqual(result["status"], "success")
        self.assertEqual(
            metric_map["context_recall"].inputs[0]["reference"],
            sample()["reference"],
        )
        self.assertEqual(
            metric_map["context_precision"].inputs[0]["retrieved_contexts"],
            ["first retrieved passage", "second retrieved passage"],
        )
        self.assertEqual(
            metric_map["answer_relevancy"].inputs[0]["response"],
            "Generated answer grounded in context.",
        )
        self.assertEqual(
            metric_map["faithfulness"].inputs[0]["retrieved_contexts"],
            ["first retrieved passage", "second retrieved passage"],
        )

    async def test_metric_failure_is_reported_not_replaced_with_zero(self):
        docs = [SimpleNamespace(page_content="retrieved context")]
        metric_map = {name: FakeMetric(0.6) for name in runner.METRIC_NAMES}
        metric_map["faithfulness"] = FakeMetric(error=RuntimeError("judge unavailable"))
        with (
            patch.object(runner, "retrieve_documents", return_value=docs),
            patch.object(runner, "generate_answer", return_value="Generated answer"),
        ):
            result = await runner.evaluate_sample(
                sample(), metric_map, runner.asyncio.Semaphore(1)
            )
        self.assertEqual(result["status"], "partial_failure")
        self.assertIsNone(result["scores"]["faithfulness"])
        self.assertIn("judge unavailable", result["metric_errors"]["faithfulness"])

    async def test_pipeline_failure_marks_metrics_unavailable(self):
        metric_map = {name: FakeMetric() for name in runner.METRIC_NAMES}
        with patch.object(
            runner, "retrieve_documents", side_effect=RuntimeError("Qdrant unavailable")
        ):
            result = await runner.evaluate_sample(
                sample(), metric_map, runner.asyncio.Semaphore(1)
            )
        self.assertEqual(result["status"], "failed")
        self.assertIn("Qdrant unavailable", result["pipeline_error"])
        self.assertTrue(all(not metric.inputs for metric in metric_map.values()))

    async def test_scores_outside_metric_range_are_not_clamped(self):
        docs = [SimpleNamespace(page_content="retrieved context")]
        metric_map = {name: FakeMetric(0.5) for name in runner.METRIC_NAMES}
        metric_map["context_recall"] = FakeMetric(1.4)
        with (
            patch.object(runner, "retrieve_documents", return_value=docs),
            patch.object(runner, "generate_answer", return_value="Generated answer"),
        ):
            result = await runner.evaluate_sample(
                sample(), metric_map, runner.asyncio.Semaphore(1)
            )
        self.assertIsNone(result["scores"]["context_recall"])
        self.assertIn("outside documented range", result["metric_errors"]["context_recall"])


class RagCompatibilityTests(unittest.TestCase):
    def test_existing_streaming_generator_still_streams_one_retrieval_trace(self):
        import app.rag as rag

        document = SimpleNamespace(
            page_content="Portfolio knowledge passage",
            metadata={"source": "about.md", "chunk_index": 0},
        )
        chain = MagicMock()
        chain.stream.return_value = iter([SimpleNamespace(content="streamed text")])
        messages = [{"role": "user", "content": "Tell me about Touqeer."}]

        with (
            patch.object(rag, "retrieve_documents", return_value=[document]) as retrieve,
            patch.object(rag, "build_answer_chain", return_value=chain) as build_chain,
        ):
            chunks = list(rag.stream_answer(messages))

        self.assertEqual(chunks, ["streamed text"])
        retrieve.assert_called_once()
        build_chain.assert_called_once()
        chain.stream.assert_called_once()
        inputs = chain.stream.call_args.args[0]
        self.assertIn("Portfolio knowledge passage", inputs["context"])
        self.assertIn("about.md", inputs["sources"])
        self.assertEqual(inputs["history"][-1].content, "Tell me about Touqeer.")


class ReportTests(unittest.TestCase):
    def test_averages_only_available_scores(self):
        results = [
            {"status": "success", "scores": {name: 0.8 for name in runner.METRIC_NAMES}},
            {"status": "partial_failure", "scores": {
                "context_recall": None,
                "context_precision": 0.4,
                "answer_relevancy": 0.2,
                "faithfulness": None,
            }},
        ]
        summary = runner.summarize(results)
        self.assertEqual(summary["average_scores"]["context_recall"]["score"], 0.8)
        self.assertEqual(summary["average_scores"]["context_precision"]["score"], 0.6)
        self.assertEqual(summary["average_scores"]["faithfulness"]["successful_scores"], 1)
        self.assertEqual(summary["successfully_evaluated_samples"], 1)
        self.assertEqual(summary["partially_evaluated_samples"], 1)


if __name__ == "__main__":
    unittest.main()
