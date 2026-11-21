import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app import warmup
from app.config import settings
from app.embedding_cache import QueryEmbeddingCache, query_embedding_cache
from app.latency import RequestLatency
from app.retrieval.dense import TimedEmbeddings


class CacheTests(unittest.TestCase):
    def test_lru_evicts_oldest_and_refreshes_on_get(self):
        cache = QueryEmbeddingCache(2)
        cache.put("m", "a", [1.0])
        cache.put("m", "b", [2.0])
        cache.get("m", "a")  # a is now most recent
        cache.put("m", "c", [3.0])  # evicts b
        self.assertIsNotNone(cache.get("m", "a"))
        self.assertIsNone(cache.get("m", "b"))
        self.assertEqual(len(cache), 2)

    def test_case_spacing_and_trailing_punctuation_share_an_entry(self):
        cache = QueryEmbeddingCache(4)
        cache.put("m1", "What  has   he built? ", [1.0])
        self.assertEqual(cache.get("m1", " what HAS he built"), [1.0])
        self.assertEqual(cache.get("m1", "What has he built?!"), [1.0])

    def test_different_words_or_models_never_collide(self):
        cache = QueryEmbeddingCache(4)
        cache.put("m1", "What has he built?", [1.0])
        self.assertIsNone(cache.get("m2", "What has he built?"))
        self.assertIsNone(cache.get("m1", "What has she built?"))
        self.assertIsNone(cache.get("m1", "What has he built in AI?"))

    def test_returns_copies_and_zero_size_disables(self):
        cache = QueryEmbeddingCache(2)
        cache.put("m", "q", [1.0, 2.0])
        cache.get("m", "q").append(9.0)
        self.assertEqual(cache.get("m", "q"), [1.0, 2.0])
        off = QueryEmbeddingCache(0)
        off.put("m", "q", [1.0])
        self.assertIsNone(off.get("m", "q"))


class TimedEmbeddingsCacheTests(unittest.TestCase):
    def setUp(self):
        query_embedding_cache.clear()

    def tearDown(self):
        query_embedding_cache.clear()

    def test_second_identical_query_is_a_flagged_hit_and_skips_the_api(self):
        inner = MagicMock()
        inner.embed_query.return_value = [0.1, 0.2]
        request = RequestLatency(started_at=0.0)
        emb = TimedEmbeddings(inner, request)
        self.assertEqual(emb.embed_query("hello there"), [0.1, 0.2])
        self.assertNotIn("embedding_cache_hit", request.flags)
        self.assertEqual(emb.embed_query("hello   there"), [0.1, 0.2])
        self.assertTrue(request.flags["embedding_cache_hit"])
        inner.embed_query.assert_called_once()

    def test_async_path_uses_the_same_cache(self):
        inner = SimpleNamespace(aembed_query=AsyncMock(return_value=[0.5]))
        emb = TimedEmbeddings(inner, None)

        async def run():
            await emb.aembed_query("q")
            return await emb.aembed_query("q")

        self.assertEqual(asyncio.run(run()), [0.5])
        inner.aembed_query.assert_awaited_once()


class WarmupTests(unittest.TestCase):
    def setUp(self):
        query_embedding_cache.clear()

    def tearDown(self):
        query_embedding_cache.clear()

    def test_bm25_prebuilds_global_and_every_project(self):
        docs = [Document(page_content="x", metadata={"project_id": p}) for p in ("a", "b", "a")]
        docs.append(Document(page_content="y", metadata={}))
        built = []
        index = SimpleNamespace(
            snapshot=lambda: SimpleNamespace(documents=docs),
            retriever=lambda project_id=None: built.append(project_id),
        )
        with patch.object(warmup, "get_bm25_index", return_value=index):
            self.assertEqual(warmup._warm_bm25(), 3)
        self.assertEqual(built, [None, "a", "b"])

    def test_starter_questions_are_pre_embedded_in_one_batched_call(self):
        inner = MagicMock()
        inner.embed_documents.return_value = [[1.0], [2.0]]
        with patch.object(warmup, "get_embeddings", return_value=inner), patch.object(
            settings, "warmup_queries", ["one", "two"]
        ):
            warmup._warm_embeddings()
            warmup._warm_embeddings()  # everything cached: no second API call
        inner.embed_documents.assert_called_once_with(["one", "two"])
        self.assertEqual(query_embedding_cache.get(settings.embed_model, "two"), [2.0])

    def test_a_failing_step_never_raises(self):
        async def run():
            with patch.object(warmup, "_warm_bm25", side_effect=RuntimeError("boom")), patch.object(
                warmup, "_warm_embeddings", return_value=0
            ), patch.object(warmup, "_warm_qdrant", return_value=True), patch.object(
                warmup, "_warm_llm", new=AsyncMock()
            ):
                await warmup.warm_up()

        with self.assertLogs("rag", level="WARNING"):
            asyncio.run(run())

    def test_lifespan_starts_warmup_in_background_and_health_still_answers(self):
        from app.main import app

        started = []

        async def fake():
            started.append(1)

        with patch("app.main.warm_up", fake):
            with TestClient(app) as client:
                self.assertEqual(client.get("/health").status_code, 200)
        self.assertEqual(started, [1])

    def test_lifespan_respects_disabled_flag(self):
        from app.main import app

        fake = AsyncMock()
        with patch("app.main.warm_up", fake), patch.object(settings, "warmup_enabled", False):
            with TestClient(app) as client:
                client.get("/health")
        fake.assert_not_called()


if __name__ == "__main__":
    unittest.main()
