from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.latency import (
    LatencyRecord,
    aggregate_latency,
    begin_request,
    finish_request,
    last_completed_latency,
    mark_first_token,
    record_stage,
    reset_request,
)
from app.rag import stream_answer
from langchain_core.documents import Document


class LatencyMonitoringTests(unittest.TestCase):
    def test_request_timing_records_stages_without_reexecuting_them(self) -> None:
        request, token = begin_request()
        try:
            record_stage("embedding_ms", 12.0)
            record_stage("retrieval_ms", 40.0)
            record_stage("reranking_ms", 8.0)
            record_stage("llm_ms", 25.0)
            mark_first_token()
            record = finish_request(request)
        finally:
            reset_request(token)

        self.assertGreaterEqual(record.total_ms, 0.0)
        self.assertEqual(record.embedding_ms, 12.0)
        self.assertEqual(record.retrieval_ms, 40.0)
        self.assertEqual(record.reranking_ms, 8.0)
        self.assertEqual(record.llm_ms, 25.0)
        self.assertIsNotNone(record.ttft_ms)

    def test_aggregate_includes_average_min_max_and_nearest_rank_percentiles(self) -> None:
        records = [
            LatencyRecord(total_ms=float(value), embedding_ms=None, retrieval_ms=5.0, reranking_ms=None, llm_ms=2.0, ttft_ms=1.0)
            for value in range(1, 101)
        ]
        result = aggregate_latency(records)
        total = result["total_ms"]
        retrieval = result["retrieval_ms"]
        self.assertEqual(result["sample_count"], 100)
        self.assertEqual(total["average"], 50.5)
        self.assertEqual(total["minimum"], 1.0)
        self.assertEqual(total["maximum"], 100.0)
        self.assertEqual(total["p50"], 50.0)
        self.assertEqual(total["p95"], 95.0)
        self.assertEqual(total["p99"], 99.0)
        self.assertEqual(retrieval["count"], 100)
        self.assertEqual(result["embedding_ms"]["count"], 0)

    def test_stream_output_is_unchanged_and_pipeline_stages_run_once(self) -> None:
        calls = {"retrieval": 0, "generation": 0}

        async def retrieve(query: str):
            calls["retrieval"] += 1
            return [Document(page_content="Touqeer builds RAG systems.", metadata={"source_filename": "about.md"})]

        class FakeChain:
            async def astream(self, inputs):
                calls["generation"] += 1
                yield SimpleNamespace(content="Answer")
                yield SimpleNamespace(content=" unchanged")

        class FakePrompt:
            def __or__(self, model):
                return FakeChain()

        async def run():
            return "".join([part async for part in stream_answer([{"role": "user", "content": "Who is Touqeer?"}])])

        with patch("app.rag.aretrieve_documents", side_effect=retrieve), patch(
            "app.rag.PROMPT", FakePrompt()
        ), patch("app.rag.get_chat_model", return_value=object()):
            response = asyncio.run(run())

        self.assertEqual(response, "Answer unchanged")
        self.assertEqual(calls, {"retrieval": 1, "generation": 1})
        record = last_completed_latency()
        self.assertIsNotNone(record)
        self.assertIsNotNone(record.retrieval_ms)
        self.assertIsNotNone(record.llm_ms)
        self.assertIsNotNone(record.ttft_ms)


if __name__ == "__main__":
    unittest.main()
