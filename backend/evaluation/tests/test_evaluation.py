from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from langchain_core.documents import Document
from langchain_core.messages import AIMessageChunk

from evaluation.config import METRIC_NAMES
from evaluation.dataset import EvaluationCase, load_dataset
from evaluation.evaluator import evaluate_dataset
from evaluation.metrics import score_sample
from evaluation.pipeline_adapter import PipelineOutput, run_existing_pipeline
from evaluation.report import build_report, save_report


class FakeChain:
    async def astream(self, values):
        assert "retrieved profile context" in values["context"]
        yield AIMessageChunk(content="Touqeer is a software engineering student.")


class FakePrompt:
    def __or__(self, llm):
        return FakeChain()


class FakeMetric:
    def __init__(self, value=0.75, error=None):
        self.value = value
        self.error = error
        self.inputs = None

    async def ascore(self, **kwargs):
        self.inputs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(value=self.value)


class EvaluationTests(unittest.IsolatedAsyncioTestCase):
    def test_dataset_has_grounded_cases_for_all_topics(self):
        cases = load_dataset()
        self.assertGreaterEqual(len(cases), 10)
        self.assertEqual(len({case.case_id for case in cases}), len(cases))
        self.assertTrue(all(case.user_input and case.reference for case in cases))

    def test_dataset_keeps_missing_reference_as_incomplete_case_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "cases.json"
            path.write_text(json.dumps([
                {"id": "known", "user_input": "Known question", "reference": "Known answer"},
                {"id": "unknown", "user_input": "Question without reference", "reference": " "},
            ]), encoding="utf-8")
            cases = load_dataset(path)
        self.assertEqual([case.reference for case in cases], ["Known answer", None])

    async def test_adapter_uses_existing_stream_and_captures_actual_context(self):
        documents = [Document(page_content="retrieved profile context", metadata={"source": "about.md"})]
        with patch("app.rag.aretrieve_documents", new=AsyncMock(return_value=documents)), patch(
            "app.rag.PROMPT", FakePrompt()
        ), patch("app.rag.get_chat_model", return_value=object()):
            output = await run_existing_pipeline("Who is Touqeer?")
        self.assertEqual(output.status, "complete")
        self.assertEqual(output.retrieved_contexts, ["retrieved profile context"])
        self.assertEqual(output.response, "Touqeer is a software engineering student.")

    async def test_ragas_receives_correct_fields_and_keeps_failures_null(self):
        metrics = {name: FakeMetric() for name in METRIC_NAMES}
        metrics["faithfulness"] = FakeMetric(error=RuntimeError("judge unavailable"))
        scores, errors = await score_sample(
            user_input="Question",
            response="Answer",
            retrieved_contexts=["actual chunk"],
            reference="Verified answer",
            metrics=metrics,
        )
        self.assertEqual(scores["answer_correctness"], 0.75)
        self.assertIsNone(scores["faithfulness"])
        self.assertIn("faithfulness", errors)
        self.assertEqual(metrics["context_recall"].inputs["reference"], "Verified answer")
        self.assertEqual(metrics["context_precision"].inputs["retrieved_contexts"], ["actual chunk"])
        self.assertEqual(metrics["answer_relevancy"].inputs["response"], "Answer")

    async def test_missing_reference_skips_only_reference_metrics(self):
        metrics = {name: FakeMetric() for name in METRIC_NAMES}
        scores, errors = await score_sample(
            user_input="Question",
            response="Answer",
            retrieved_contexts=["actual chunk"],
            reference=None,
            metrics=metrics,
        )
        self.assertIsNone(scores["answer_correctness"])
        self.assertIsNone(scores["context_recall"])
        self.assertIsNone(scores["context_precision"])
        self.assertEqual(scores["answer_relevancy"], 0.75)
        self.assertEqual(scores["faithfulness"], 0.75)
        self.assertIn("missing", errors["context_recall"])
        self.assertIsNone(metrics["context_recall"].inputs)

    async def test_evaluator_marks_missing_reference_incomplete_and_continues(self):
        cases = [
            EvaluationCase("missing-ref", "No reference", None),
            EvaluationCase("with-ref", "Has reference", "Verified"),
        ]
        pipeline_outputs = [
            PipelineOutput("Answer A", ["Context A"]),
            PipelineOutput("Answer B", ["Context B"]),
        ]
        async def pipeline(_question):
            return pipeline_outputs.pop(0)

        async def scorer(**kwargs):
            requires_reference = {"answer_correctness", "context_recall", "context_precision"}
            return ({
                name: (None if name in requires_reference and not kwargs["reference"] else 0.75)
                for name in METRIC_NAMES
            }, {})

        with patch("evaluation.evaluator.load_dataset", return_value=cases), patch(
            "evaluation.evaluator.run_existing_pipeline", side_effect=pipeline
        ), patch("evaluation.evaluator.score_sample", side_effect=scorer), patch(
            "evaluation.metrics.build_metrics", return_value=object()
        ):
            report = await evaluate_dataset()

        self.assertEqual(len(report["samples"]), 2)
        self.assertEqual(report["samples"][0]["status"], "incomplete")
        self.assertIsNone(report["samples"][0]["metric_scores"]["context_recall"])
        self.assertEqual(report["samples"][1]["status"], "complete")
        self.assertEqual(report["metric_summary"]["faithfulness"]["scored_samples"], 2)
        self.assertEqual(report["metric_summary"]["answer_correctness"]["scored_samples"], 1)

    def test_report_aggregates_only_real_scores_and_saves(self):
        rows = [
            {"id": "a", "status": "complete", "metric_scores": {"answer_correctness": 0.8}},
            {"id": "b", "status": "completed_with_metric_errors", "metric_scores": {"answer_correctness": None}, "metric_errors": {"faithfulness": "failed"}},
        ]
        report = build_report(rows)
        self.assertEqual(report["metric_summary"]["answer_correctness"]["mean"], 0.8)
        self.assertEqual(report["metric_summary"]["answer_correctness"]["scored_samples"], 1)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = save_report(report, Path(temp_dir))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["total_evaluation_samples"], 2)

    def test_report_aggregates_retrieval_and_project_diagnostics(self):
        trace = {
            "dense_candidate_count": 10,
            "bm25_candidate_count": 10,
            "fused_candidate_count": 14,
            "project_filter": {"project_id": "document-search-rag", "project_name": "Document Search RAG"},
            "project_relevant_candidate_count": 4,
            "project_relevant_final_count": 3,
            "incorrect_project_final_count": 0,
            "reranker_enabled": True,
            "reranker_status": "success",
        }
        report = build_report([{"id": "doc-search", "status": "complete", "metric_scores": {}, "retrieval_trace": trace}])
        diagnostics = report["retrieval_diagnostics"]
        self.assertEqual(diagnostics["mean_fused_candidates"], 14)
        self.assertEqual(diagnostics["reranker_execution_success_rate"], 1.0)
        self.assertEqual(diagnostics["project_query_correct_retrieval_rate"], 1.0)
        self.assertEqual(diagnostics["relevant_project_chunks_in_final_top_k"], 3)


if __name__ == "__main__":
    unittest.main()
