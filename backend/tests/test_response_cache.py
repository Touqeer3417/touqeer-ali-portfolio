"""Response cache behaviour: keys, TTL, invalidation and pipeline integration.

Covers, without calling OpenAI or Qdrant:
  * LRU eviction, TTL expiry, normalized keys and the counters behind
    ``/cache/stats``,
  * re-indexing the knowledge base retires cached answers through the key,
  * a repeated first-turn question skips retrieval AND generation and replays
    the previous answer byte for byte, notes included,
  * nothing is cached for errors, the no-context reply, partial streams or any
    turn that has conversation history,
  * ``bypass_response_cache`` keeps evaluation and benchmark runs honest.

Run from ``backend``: ``python -m unittest tests.test_response_cache -v``
"""

from __future__ import annotations

import asyncio
import unittest
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.config import settings
from app.latency import get_record, use_request_id
from app.main import app
from app.rag import cacheable_question, stream_answer
from app.response_cache import (
    ResponseCache,
    bypass_response_cache,
    cache_key,
    knowledge_base_version,
    response_cache,
)


DOCUMENT = Document(
    page_content="Touqeer builds RAG systems.",
    metadata={"source_filename": "about.md"},
)
NOTE_DOCUMENT = Document(
    page_content="Touqeer builds RAG systems.\n\nNote: the demo runs locally only.",
    metadata={"source_filename": "projects.md"},
)


class ResponseCacheUnitTests(unittest.TestCase):
    """The cache container on its own, with an injected clock."""

    def test_lru_evicts_oldest_and_refreshes_on_get(self):
        cache = ResponseCache(2, ttl_seconds=60)
        a, b, c = (cache_key(q) for q in ("a", "b", "c"))
        cache.put(a, "answer a")
        cache.put(b, "answer b")
        cache.get(a)  # a is now most recent
        cache.put(c, "answer c")  # evicts b
        self.assertEqual(cache.get(a), "answer a")
        self.assertIsNone(cache.get(b))
        self.assertEqual(len(cache), 2)
        self.assertEqual(cache.stats()["evictions"], 1)

    def test_case_spacing_and_trailing_punctuation_share_an_entry(self):
        cache = ResponseCache(4, ttl_seconds=60)
        cache.put(cache_key("What are your skills? "), "Python, RAG.")
        self.assertEqual(cache.get(cache_key("what ARE your   skills")), "Python, RAG.")
        self.assertEqual(cache.get(cache_key("What are your skills?!")), "Python, RAG.")

    def test_different_questions_or_models_never_collide(self):
        cache = ResponseCache(8, ttl_seconds=60)
        cache.put(cache_key("What are your skills?"), "skills")
        self.assertIsNone(cache.get(cache_key("What are your projects?")))
        self.assertIsNone(cache.get(cache_key("What are your top skills?")))
        with patch.object(settings, "chat_model", "some-other-model"):
            self.assertIsNone(cache.get(cache_key("What are your skills?")))

    def test_entry_expires_once_the_ttl_has_elapsed(self):
        now = [1000.0]
        cache = ResponseCache(4, ttl_seconds=30, clock=lambda: now[0])
        key = cache_key("What are your skills?")
        cache.put(key, "skills")

        now[0] += 29.9
        self.assertEqual(cache.get(key), "skills", "expired before its TTL")
        now[0] += 0.2
        self.assertIsNone(cache.get(key), "served after its TTL")
        self.assertEqual(len(cache), 0, "expired entry was not dropped")
        self.assertEqual(cache.stats()["expirations"], 1)

    def test_zero_size_or_zero_ttl_disables_the_cache(self):
        key = cache_key("q")
        for cache in (ResponseCache(0, ttl_seconds=60), ResponseCache(4, ttl_seconds=0)):
            cache.put(key, "answer")
            self.assertFalse(cache.enabled)
            self.assertIsNone(cache.get(key))
            self.assertEqual(len(cache), 0)

    def test_blank_answers_are_never_stored(self):
        cache = ResponseCache(4, ttl_seconds=60)
        key = cache_key("q")
        cache.put(key, "   \n ")
        self.assertIsNone(cache.get(key))
        self.assertEqual(cache.stats()["stores"], 0)

    def test_stats_report_hits_misses_and_hit_rate(self):
        cache = ResponseCache(4, ttl_seconds=60)
        key = cache_key("q")
        self.assertIsNone(cache.stats()["hit_rate"], "no lookups yet")
        cache.put(key, "answer")
        cache.get(key)
        cache.get(cache_key("other"))
        stats = cache.stats()
        self.assertEqual((stats["hits"], stats["misses"], stats["stores"]), (1, 1, 1))
        self.assertEqual(stats["hit_rate"], 0.5)
        self.assertEqual(stats["entries"], 1)


class KnowledgeBaseInvalidationTests(unittest.TestCase):
    """Re-indexing must retire answers built from the previous corpus."""

    def test_rewriting_the_snapshot_changes_the_key_and_retires_entries(self):
        with TemporaryDirectory() as directory:
            snapshot = Path(directory) / "bm25-documents.json"
            snapshot.write_text('{"generation": 1}', encoding="utf-8")
            with patch.object(settings, "bm25_index_path", snapshot):
                cache = ResponseCache(4, ttl_seconds=3600)
                question = "What are your skills?"
                cache.put(cache_key(question), "answer from generation 1")
                self.assertEqual(cache.get(cache_key(question)), "answer from generation 1")

                # ingestion.sync republishes this file for every generation.
                snapshot.write_text('{"generation": 2, "documents": []}', encoding="utf-8")
                self.assertIsNone(
                    cache.get(cache_key(question)),
                    "a re-indexed knowledge base still served the old answer",
                )

    def test_a_missing_snapshot_is_reported_without_raising(self):
        with TemporaryDirectory() as directory:
            missing = Path(directory) / "does-not-exist.json"
            with patch.object(settings, "bm25_index_path", missing):
                self.assertEqual(knowledge_base_version(), "absent")


class CacheableQuestionTests(unittest.TestCase):
    """Only a visitor's first turn may be cached."""

    def test_a_single_user_turn_is_cacheable(self):
        self.assertEqual(
            cacheable_question([{"role": "user", "content": " What are your skills? "}]),
            "What are your skills?",
        )

    def test_any_conversation_history_makes_it_uncacheable(self):
        self.assertIsNone(
            cacheable_question(
                [
                    {"role": "user", "content": "Tell me about Corrective RAG."},
                    {"role": "assistant", "content": "It uses LangGraph."},
                    {"role": "user", "content": "What are your skills?"},
                ]
            ),
            "a follow-up turn was treated as cacheable",
        )

    def test_blank_or_non_user_turns_are_uncacheable(self):
        self.assertIsNone(cacheable_question([{"role": "user", "content": "   "}]))
        self.assertIsNone(cacheable_question([{"role": "assistant", "content": "hi"}]))
        self.assertIsNone(cacheable_question([]))

    def test_bypass_makes_everything_uncacheable(self):
        messages = [{"role": "user", "content": "What are your skills?"}]
        with bypass_response_cache():
            self.assertIsNone(cacheable_question(messages))
        self.assertIsNotNone(cacheable_question(messages), "bypass leaked past its block")


def run_pipeline(
    messages: list[dict],
    documents: list[Document] | None = None,
    tokens: tuple[str, ...] = ("Answer", " text"),
    fail_after: int | None = None,
    request_id: str | None = None,
) -> tuple[str, dict[str, int]]:
    """Drive ``stream_answer`` with fake retrieval and a fake model.

    Returns the streamed text and how many times retrieval and generation ran,
    which is how these tests prove a cache hit skipped both. Pass ``request_id``
    to look the timings up afterwards with ``get_record``, the way ``/latency``
    does; ``asyncio.run`` copies the context, so the context-local
    ``last_completed_latency`` is not readable from the caller.
    """
    calls = {"retrieval": 0, "generation": 0}

    async def retrieve(_query: str):
        calls["retrieval"] += 1
        return documents if documents is not None else [DOCUMENT]

    class FakeChain:
        async def astream(self, _inputs):
            calls["generation"] += 1
            for index, token in enumerate(tokens):
                if fail_after is not None and index == fail_after:
                    raise RuntimeError("simulated upstream failure")
                yield SimpleNamespace(content=token)

    class FakePrompt:
        def __or__(self, _model):
            return FakeChain()

    async def run() -> str:
        with use_request_id(request_id) if request_id else nullcontext():
            return "".join([part async for part in stream_answer(messages)])

    with patch("app.rag.aretrieve_documents", side_effect=retrieve), patch(
        "app.rag.PROMPT", FakePrompt()
    ), patch("app.rag.get_chat_model", return_value=object()):
        return asyncio.run(run()), calls


class PipelineResponseCacheTests(unittest.TestCase):
    """stream_answer with the real module-level cache."""

    def setUp(self):
        response_cache.clear()
        response_cache.reset_stats()

    tearDown = setUp

    def test_a_repeated_question_skips_retrieval_and_generation(self):
        question = [{"role": "user", "content": "What are your skills?"}]
        first, first_calls = run_pipeline(question)
        second, second_calls = run_pipeline(question)

        self.assertEqual(first, "Answer text")
        self.assertEqual(second, first, "the cached answer differed from the original")
        self.assertEqual(first_calls, {"retrieval": 1, "generation": 1})
        self.assertEqual(
            second_calls,
            {"retrieval": 0, "generation": 0},
            "a cache hit still ran retrieval or the LLM",
        )
        self.assertEqual(response_cache.stats()["hits"], 1)

    def test_a_cosmetic_variant_of_the_question_also_hits(self):
        run_pipeline([{"role": "user", "content": "What are your skills?"}])
        answer, calls = run_pipeline([{"role": "user", "content": "what are  YOUR skills"}])
        self.assertEqual(answer, "Answer text")
        self.assertEqual(calls["generation"], 0)

    def test_a_different_question_is_generated_fresh(self):
        run_pipeline([{"role": "user", "content": "What are your skills?"}])
        answer, calls = run_pipeline(
            [{"role": "user", "content": "Tell me about your projects."}],
            tokens=("Projects", " answer"),
        )
        self.assertEqual(answer, "Projects answer")
        self.assertEqual(calls, {"retrieval": 1, "generation": 1})

    def test_cached_replay_includes_the_appended_source_notes(self):
        question = [{"role": "user", "content": "What are your skills?"}]
        first, _ = run_pipeline(question, documents=[NOTE_DOCUMENT])
        second, calls = run_pipeline(question, documents=[NOTE_DOCUMENT])

        self.assertIn("Note: the demo runs locally only. [Source: projects.md]", first)
        self.assertEqual(second, first, "the replay dropped or duplicated the notes")
        self.assertEqual(calls["generation"], 0)

    def test_a_failed_generation_is_never_cached(self):
        question = [{"role": "user", "content": "What are your skills?"}]
        first, _ = run_pipeline(question, fail_after=1)
        self.assertIn("Sorry, something went wrong", first)
        self.assertEqual(len(response_cache), 0, "an error response was cached")

        second, calls = run_pipeline(question)
        self.assertEqual(second, "Answer text")
        self.assertEqual(calls, {"retrieval": 1, "generation": 1})

    def test_the_no_context_reply_is_never_cached(self):
        question = [{"role": "user", "content": "What are your skills?"}]
        answer, _ = run_pipeline(question, documents=[])
        self.assertIn("could not find that information", answer)
        self.assertEqual(len(response_cache), 0, "the no-context reply was cached")

    def test_an_abandoned_stream_caches_nothing(self):
        async def run():
            async def retrieve(_query: str):
                return [DOCUMENT]

            class FakeChain:
                async def astream(self, _inputs):
                    for token in ("Partial", " answer", " never finished"):
                        yield SimpleNamespace(content=token)

            class FakePrompt:
                def __or__(self, _model):
                    return FakeChain()

            with patch("app.rag.aretrieve_documents", side_effect=retrieve), patch(
                "app.rag.PROMPT", FakePrompt()
            ), patch("app.rag.get_chat_model", return_value=object()):
                stream = stream_answer([{"role": "user", "content": "What are your skills?"}])
                self.assertEqual(await anext(stream), "Partial")
                await stream.aclose()  # visitor pressed Stop

        asyncio.run(run())
        self.assertEqual(len(response_cache), 0, "a partial answer was cached")

    def test_a_follow_up_turn_is_never_served_from_cache(self):
        question = "What are your skills?"
        run_pipeline([{"role": "user", "content": question}])

        answer, calls = run_pipeline(
            [
                {"role": "user", "content": "Tell me about Corrective RAG."},
                {"role": "assistant", "content": "It uses LangGraph."},
                {"role": "user", "content": question},
            ],
            tokens=("Fresh", " answer"),
        )
        self.assertEqual(answer, "Fresh answer", "a follow-up was answered from cache")
        self.assertEqual(calls, {"retrieval": 1, "generation": 1})

    def test_bypass_forces_a_real_run_and_stores_nothing(self):
        question = [{"role": "user", "content": "What are your skills?"}]
        run_pipeline(question)
        self.assertEqual(len(response_cache), 1)

        with bypass_response_cache():
            answer, calls = run_pipeline(question, tokens=("Measured", " run"))

        self.assertEqual(answer, "Measured run", "the bypass still served a cached answer")
        self.assertEqual(calls, {"retrieval": 1, "generation": 1})
        self.assertEqual(
            response_cache.get(cache_key("What are your skills?")),
            "Answer text",
            "the bypassed run overwrote the cached answer",
        )

    def test_a_hit_is_flagged_and_records_no_retrieval_or_llm_time(self):
        question = [{"role": "user", "content": "What are your skills?"}]
        run_pipeline(question, request_id="miss-under-test")
        run_pipeline(question, request_id="hit-under-test")

        miss = get_record("miss-under-test")
        self.assertIsNotNone(miss)
        self.assertFalse(miss.flags.get("response_cache_hit"), "the first run was a hit")
        self.assertIsNotNone(miss.llm_ms, "the first run reported no LLM time")

        record = get_record("hit-under-test")
        self.assertIsNotNone(record)
        self.assertTrue(record.flags.get("response_cache_hit"), "the hit was not flagged")
        self.assertIsNone(record.llm_ms, "a cache hit reported LLM time")
        self.assertIsNone(record.retrieval_ms, "a cache hit reported retrieval time")
        self.assertIsNotNone(record.ttft_ms, "a cache hit reported no time to first token")


class CacheStatsEndpointTests(unittest.TestCase):
    def setUp(self):
        app.state.limiter.reset()
        self.client = TestClient(app)

    def test_counters_are_returned_to_an_authenticated_caller(self):
        response = self.client.get("/cache/stats", headers={"x-api-key": settings.shared_secret})
        self.assertEqual(response.status_code, 200)
        stats = response.json()["response_cache"]
        for field in ("enabled", "entries", "hits", "misses", "hit_rate", "ttl_seconds"):
            self.assertIn(field, stats)

    def test_a_bad_secret_is_rejected(self):
        response = self.client.get("/cache/stats", headers={"x-api-key": "wrong"})
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
