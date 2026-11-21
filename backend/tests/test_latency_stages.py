"""Tests for per-stage latency: timer, isolation, derived vector search, API, report."""

from __future__ import annotations

import asyncio
import time
import unittest
from dataclasses import asdict
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.config import settings
from app.latency import (
    begin_request,
    finish_request,
    get_record,
    mark_first_token,
    mark_llm_start,
    public_latency,
    record_stage_for,
    reset_request,
    set_flag,
    timer,
    use_request_id,
)
from app.main import app
from app.rag import stream_answer
from app.retrieval.dense import _vector_search_timer
from evaluation.report import build_report


class TimerTests(unittest.TestCase):
    def test_timer_records_partial_time_when_the_block_raises(self) -> None:
        request, token = begin_request()
        try:
            with self.assertRaises(RuntimeError):
                with timer("prompt_build_ms"):
                    time.sleep(0.01)
                    raise RuntimeError("boom")
            record = finish_request(request)
        finally:
            reset_request(token)
        self.assertGreaterEqual(record.prompt_build_ms, 9.0)

    def test_timer_is_a_noop_without_an_active_request(self) -> None:
        with timer("prompt_build_ms"):
            pass  # must not raise

    def test_vector_search_excludes_embedding_recorded_inside_the_call(self) -> None:
        request, token = begin_request()
        try:
            with _vector_search_timer():
                time.sleep(0.06)
                record_stage_for(request, "embedding_ms", 25.0)  # as TimedEmbeddings does
            record = finish_request(request)
        finally:
            reset_request(token)
        self.assertEqual(record.embedding_ms, 25.0)
        self.assertGreaterEqual(record.vector_search_ms, 30.0)
        self.assertLess(record.vector_search_ms, 55.0)

    def test_concurrent_requests_do_not_share_timings(self) -> None:
        async def one(request_id: str, delay: float) -> tuple[str, float]:
            with use_request_id(request_id):
                request, token = begin_request()
            try:
                await asyncio.sleep(0)
                with timer("llm_ms"):
                    await asyncio.sleep(delay)
                set_flag(f"flag_{request_id}")
                record = finish_request(request)
            finally:
                reset_request(token)
            return record.request_id, record.llm_ms

        async def run():
            return await asyncio.gather(one("aaaa", 0.02), one("bbbb", 0.08))

        (id_a, llm_a), (id_b, llm_b) = asyncio.run(run())
        self.assertEqual((id_a, id_b), ("aaaa", "bbbb"))
        self.assertLess(llm_a, llm_b)
        self.assertEqual(get_record("aaaa").flags, {"flag_aaaa": True})
        self.assertEqual(get_record("bbbb").flags, {"flag_bbbb": True})


class PipelineTimingTests(unittest.TestCase):
    @staticmethod
    def _patches():
        class FakeChain:
            async def astream(self, inputs):
                await asyncio.sleep(0.03)  # time to first token
                yield SimpleNamespace(content="Answer")
                await asyncio.sleep(0.02)
                yield SimpleNamespace(content=" done")

        class FakePrompt:
            def __or__(self, model):
                return FakeChain()

        async def retrieve(query: str):
            await asyncio.sleep(0.02)
            return [Document(page_content="Touqeer builds RAG systems.", metadata={"source_filename": "about.md"})]

        return (
            patch("app.rag.aretrieve_documents", side_effect=retrieve),
            patch("app.rag.PROMPT", FakePrompt()),
            patch("app.rag.get_chat_model", return_value=object()),
        )

    def test_stream_records_every_stage_and_the_sum_matches_total(self) -> None:
        async def run():
            with use_request_id("pipe0001"):
                return "".join([p async for p in stream_answer([{"role": "user", "content": "Who?"}])])

        a, b, c = self._patches()
        with a, b, c:
            text = asyncio.run(run())
        self.assertEqual(text, "Answer done")
        record = get_record("pipe0001")
        self.assertIsNotNone(record)
        self.assertGreater(record.retrieval_ms, 15.0)
        self.assertGreater(record.prompt_build_ms, 0.0)
        self.assertGreater(record.llm_ms, 45.0)
        # TTFT is not total generation time, and llm_ttft is a part of ttft.
        self.assertLess(record.llm_ttft_ms, record.llm_ms)
        self.assertLessEqual(record.llm_ttft_ms, record.ttft_ms)
        self.assertGreater(record.ttft_ms, record.retrieval_ms)
        # Stages account for the total; the remainder is small and not negative.
        self.assertGreaterEqual(record.overhead_ms, -1.0)
        self.assertLess(record.overhead_ms, 25.0)

    def test_api_exposes_request_id_header_and_protected_latency_endpoint(self) -> None:
        client = TestClient(app)
        key = {"x-api-key": settings.shared_secret}
        a, b, c = self._patches()
        with a, b, c:
            response = client.post("/chat", headers=key, json={"messages": [{"role": "user", "content": "Who?"}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Answer done")  # body unchanged
        request_id = response.headers["x-request-id"]

        self.assertEqual(client.get(f"/latency/{request_id}").status_code, 401)
        self.assertEqual(client.get("/latency/doesnotexist", headers=key).status_code, 404)
        found = client.get(f"/latency/{request_id}", headers=key)
        self.assertEqual(found.status_code, 200)
        latency = found.json()["latency_ms"]
        self.assertEqual(latency["request_id"], request_id)
        for name in ("embedding", "vector_search", "rerank", "prompt_build", "llm_ttft", "llm_total", "total"):
            self.assertIn(name, latency)
        self.assertGreater(latency["total"], 0)


class ReportTests(unittest.TestCase):
    @staticmethod
    def _row(case_id: str, total: float, flags: dict | None = None, llm: float = 50.0) -> dict:
        request, token = begin_request()
        try:
            record_stage_for(request, "retrieval_ms", total - llm - 1.0)
            record_stage_for(request, "embedding_ms", 10.0)
            record_stage_for(request, "vector_search_ms", 20.0)
            record_stage_for(request, "prompt_build_ms", 0.5)
            record_stage_for(request, "llm_ms", llm)
            for name in flags or {}:
                set_flag(name)
            mark_llm_start()
            mark_first_token()
            record = finish_request(request)
        finally:
            reset_request(token)
        row = asdict(record)
        row["total_ms"] = total  # deterministic totals for the assertions
        row["overhead_ms"] = total - ((total - llm - 1.0) + 0.5 + llm)
        return {"id": case_id, "status": "complete", "metric_scores": {}, "latency_ms": row}

    def test_summary_separates_cold_samples_and_flags_unreliable_p95(self) -> None:
        rows = [
            self._row("first", 5000.0),
            self._row("cold_model", 4000.0, {"cross_encoder_cold": True}),
            self._row("warm_a", 1000.0),
            self._row("warm_b", 1200.0),
        ]
        summary = build_report(rows)["latency_summary"]
        self.assertEqual(summary["all"]["sample_count"], 4)
        self.assertEqual(summary["warm"]["sample_count"], 2)
        self.assertEqual(summary["warm"]["total_ms"]["p50"], 1000.0)
        self.assertFalse(summary["p95_reliable"])
        reasons = {item["id"]: item["reasons"] for item in summary["warm_excluded_samples"]}
        self.assertEqual(reasons["first"], ["first_request_no_warmup"])
        self.assertEqual(reasons["cold_model"], ["cross_encoder_cold"])

    def test_warmup_run_keeps_the_first_sample_in_the_warm_set(self) -> None:
        rows = [self._row("first", 1000.0), self._row("second", 1100.0)]
        self.assertEqual(build_report(rows, warmup=True)["latency_summary"]["warm"]["sample_count"], 2)

    def test_suspicious_timings_are_reported(self) -> None:
        row = self._row("bad", 1000.0)
        row["latency_ms"]["embedding_ms"] = 0.0
        row["latency_ms"]["overhead_ms"] = 400.0
        problems = build_report([row])["latency_summary"]["suspicious_samples"][0]["problems"]
        self.assertIn("embedding_ms_not_positive", problems)
        self.assertIn("large_unmeasured_overhead", problems)

    def test_public_latency_rounds_and_keeps_units(self) -> None:
        request, token = begin_request()
        try:
            record_stage_for(request, "prompt_build_ms", 0.04)
            record = finish_request(request)
        finally:
            reset_request(token)
        public = public_latency(record)
        self.assertEqual(public["prompt_build"], 0.0)
        self.assertIsNone(public["rerank"])


if __name__ == "__main__":
    unittest.main()
