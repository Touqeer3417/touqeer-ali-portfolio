import unittest
from unittest.mock import patch

from app.http_clients import openai_http_kwargs, qdrant_http_kwargs
from app.retrieval import dense


def _pool_expiry(http_client):
    pool = http_client._transport._pool
    return pool._keepalive_expiry


class KeepAliveTests(unittest.TestCase):
    def test_qdrant_limits_applied_to_real_client(self):
        from qdrant_client import QdrantClient

        with patch.object(__import__("app.config", fromlist=["settings"]).settings, "http_keepalive_expiry", 60.0):
            client = QdrantClient(url="https://example.invalid:6333", api_key="x", timeout=30, **qdrant_http_kwargs())
        http = client._client.http.collections_api.api_client._client
        self.assertEqual(_pool_expiry(http), 60.0)

    def test_disabled_returns_no_overrides(self):
        from app.config import settings

        with patch.object(settings, "http_keepalive_expiry", 0.0):
            self.assertEqual(qdrant_http_kwargs(), {})
            self.assertEqual(openai_http_kwargs(), {})

    def test_openai_clients_use_long_keepalive(self):
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings

        from app.config import settings

        with patch.object(settings, "http_keepalive_expiry", 60.0):
            kwargs = openai_http_kwargs()
            chat = ChatOpenAI(model="gpt-4o-mini", api_key="x", **kwargs)
            emb = OpenAIEmbeddings(model="text-embedding-3-small", api_key="x", **openai_http_kwargs())
        self.assertEqual(_pool_expiry(chat.root_client._client), 60.0)
        self.assertEqual(_pool_expiry(chat.root_async_client._client), 60.0)
        self.assertEqual(_pool_expiry(emb.client._client._client), 60.0)


class CollectionCacheTests(unittest.TestCase):
    def setUp(self):
        dense.reset_collection_cache()

    def tearDown(self):
        dense.reset_collection_cache()

    def test_positive_answer_is_cached(self):
        calls = []

        class Client:
            def collection_exists(self, name):
                calls.append(name)
                return True

        client = Client()
        self.assertTrue(dense._collection_exists(client, "c"))
        self.assertTrue(dense._collection_exists(client, "c"))
        self.assertEqual(calls, ["c"])

    def test_negative_answer_never_cached(self):
        answers = iter([False, False, True, True])
        calls = []

        class Client:
            def collection_exists(self, name):
                calls.append(name)
                return next(answers)

        client = Client()
        self.assertFalse(dense._collection_exists(client, "c"))
        self.assertFalse(dense._collection_exists(client, "c"))
        self.assertTrue(dense._collection_exists(client, "c"))
        self.assertTrue(dense._collection_exists(client, "c"))
        self.assertEqual(len(calls), 3)

    def test_other_client_is_not_trusted(self):
        class Yes:
            def collection_exists(self, name):
                return True

        class No:
            def collection_exists(self, name):
                return False

        self.assertTrue(dense._collection_exists(Yes(), "c"))
        self.assertFalse(dense._collection_exists(No(), "c"))


if __name__ == "__main__":
    unittest.main()
