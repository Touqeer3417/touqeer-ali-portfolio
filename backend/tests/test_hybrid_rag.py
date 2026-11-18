from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.callbacks import AsyncCallbackManagerForRetrieverRun, CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, Field
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.ingestion.loader import load_markdown_documents
from app.ingestion.splitter import split_source
from app.ingestion.state import IndexSnapshot, read_snapshot, write_snapshot
from app.retrieval.hybrid import HybridRRFRetriever, TimedEnsembleRetriever
from app.retrieval.dense import _normalize_documents, build_dense_retriever
from app.retrieval.sparse import BM25Index, bootstrap_snapshot_from_qdrant
from app.ingestion import sync as ingestion_sync
from app.main import app
from app.config import settings
from app.rag import _context_notes


class DelayedRetriever(BaseRetriever):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    results: list[Document] = Field(default_factory=list)
    delay: float = 0.03
    started: list[str] = Field(default_factory=list, exclude=True)
    label: str

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:
        return self.results

    async def _aget_relevant_documents(self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun) -> list[Document]:
        self.started.append(self.label)
        await asyncio.sleep(self.delay)
        return self.results


class FixedEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0]


class HybridRagTests(unittest.IsolatedAsyncioTestCase):
    def test_retrieved_project_caveats_are_preserved_as_source_notes(self) -> None:
        documents = [
            Document(
                page_content="Project stack.\n\nNote: The source does not confirm public deployment.",
                metadata={"source_filename": "projects.md"},
            ),
            Document(
                page_content="Another chunk.\n\nNote: The source does not confirm public deployment.",
                metadata={"source_filename": "projects.md"},
            ),
        ]
        self.assertEqual(
            _context_notes(documents),
            [("The source does not confirm public deployment.", "projects.md")],
        )

    def test_existing_qdrant_collection_gets_project_payload_index(self) -> None:
        class FakeQdrant:
            def __init__(self):
                self.indexes = []

            def collection_exists(self, name):
                return True

            def get_collection(self, name):
                return SimpleNamespace(payload_schema={"text": object()})

            def create_payload_index(self, **kwargs):
                self.indexes.append(kwargs)

        client = FakeQdrant()
        with patch("app.ingestion.sync.qdrant_client", return_value=client):
            ingestion_sync._ensure_collection()
        self.assertEqual(len(client.indexes), 1)
        self.assertEqual(client.indexes[0]["field_name"], "metadata.project_id")

    def test_ingestion_uses_supported_qdrant_vectorstore_constructor(self) -> None:
        client = QdrantClient(":memory:")
        client.create_collection(
            collection_name=settings.hybrid_collection,
            vectors_config=VectorParams(size=3, distance=Distance.COSINE),
        )
        with patch("app.ingestion.sync._ensure_collection"), patch(
            "app.ingestion.sync.qdrant_client", return_value=client
        ), patch("app.ingestion.sync.get_embeddings", return_value=FixedEmbeddings()):
            store = ingestion_sync._vector_store()
            point_id = "00000000-0000-0000-0000-000000000001"
            ids = store.add_documents(
                [Document(page_content="profile chunk", metadata={"chunk_id": point_id, "source": "about.md"})],
                ids=[point_id],
            )
        self.assertEqual(ids, [point_id])
        result = store.similarity_search("profile", k=1)
        self.assertEqual(result[0].page_content, "profile chunk")

    def test_qdrant_bootstrap_stops_at_final_page(self) -> None:
        class FakeQdrant:
            def __init__(self):
                self.calls = []

            def collection_exists(self, name):
                return True

            def scroll(self, **kwargs):
                self.calls.append(kwargs["offset"])
                page = len(self.calls)
                point = SimpleNamespace(
                    id=page,
                    payload={"text": f"chunk {page}", "source": "projects.md"},
                )
                return [point], (1 if page == 1 else None)

        client = FakeQdrant()
        with patch("app.retrieval.sparse.qdrant_client", return_value=client), patch(
            "app.retrieval.sparse.write_snapshot"
        ):
            snapshot = bootstrap_snapshot_from_qdrant()

        self.assertEqual(client.calls, [None, 1])
        self.assertEqual(len(snapshot.documents), 2)

    def test_sync_cleanup_removes_superseded_chunk_ids_even_when_source_hash_matches(self) -> None:
        class FakeQdrant:
            def __init__(self):
                self.deleted = []

            def collection_exists(self, name):
                return True

            def scroll(self, **kwargs):
                points = [
                    SimpleNamespace(id="active", payload={"text": "current", "metadata": {
                        "source": "projects.md", "document_hash": "same-source-hash", "chunk_id": "active"
                    }}),
                    SimpleNamespace(id="stale", payload={"text": "old split", "metadata": {
                        "source": "projects.md", "document_hash": "same-source-hash", "chunk_id": "stale"
                    }}),
                ]
                return points, None

            def delete(self, **kwargs):
                self.deleted.extend(kwargs["points_selector"].points)

        client = FakeQdrant()
        snapshot = IndexSnapshot(
            documents=[Document(page_content="current", metadata={
                "source": "projects.md", "document_hash": "same-source-hash", "chunk_id": "active"
            })],
            source_hashes={"projects.md": "same-source-hash"},
            legacy_sources=set(),
        )
        with patch("app.ingestion.sync.qdrant_client", return_value=client):
            deleted = ingestion_sync._remove_stale_points(snapshot)

        self.assertEqual(deleted, 1)
        self.assertEqual(client.deleted, ["stale"])

    def test_streaming_chat_api_contract(self) -> None:
        async def fake_stream(messages):
            yield "Touqeer builds RAG systems."

        with patch("app.main.stream_answer", side_effect=fake_stream):
            response = TestClient(app).post(
                "/chat",
                headers={"x-api-key": settings.shared_secret},
                json={
                    "messages": [
                        {"role": "assistant", "content": "Prior answer. " * 60},
                        {"role": "user", "content": "Who is Touqeer?"},
                    ]
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Touqeer builds RAG systems.")

    def test_user_message_limit_is_preserved(self) -> None:
        response = TestClient(app).post(
            "/chat",
            headers={"x-api-key": settings.shared_secret},
            json={"messages": [{"role": "user", "content": "x" * 501}]},
        )
        self.assertEqual(response.status_code, 422)

    def test_recursive_markdown_loading_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "nested").mkdir()
            (root / "nested" / "profile.md").write_text("# Touqeer\n\nPython and RAG.", encoding="utf-8")
            (root / "empty.md").write_text("  ", encoding="utf-8")
            corpus = load_markdown_documents(root)
            self.assertEqual(set(corpus.sources), {"nested/profile.md", "empty.md"})
            profile = corpus.sources["nested/profile.md"]
            self.assertEqual(profile.document.metadata["file_name"], "profile.md")
            self.assertTrue(profile.document.metadata["document_hash"])
            self.assertEqual(corpus.failed_sources, set())
            self.assertEqual(split_source(profile)[0].metadata["source"], "nested/profile.md")

    def test_snapshot_round_trip_and_bm25(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bm25.json"
            docs = [
                Document(page_content="touqeer built vector fusion architecture retrieval", metadata={"chunk_id": "1", "source": "projects.md"}),
                Document(page_content="backend engineering services delivery", metadata={"chunk_id": "2", "source": "services.md"}),
            ]
            write_snapshot(IndexSnapshot(docs, {"projects.md": "hash"}, set(), 4), path)
            loaded = read_snapshot(path)
            self.assertEqual(loaded.generation, 4)
            self.assertEqual(len(loaded.documents), 2)
            index = BM25Index(path)
            result = index.retriever().invoke("vector fusion architecture")
            self.assertEqual({item.metadata["chunk_id"] for item in result}, {"1", "2"})

    def test_dense_legacy_payload_recovers_identity_from_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bm25.json"
            saved = Document(
                page_content="same chunk text",
                metadata={"source": "nested/profile.md", "chunk_id": "42", "qdrant_id": "42"},
            )
            write_snapshot(IndexSnapshot([saved], {}, {"nested/profile.md"}), path)
            index = BM25Index(path)
            dense = Document(page_content="same chunk text", metadata={"_id": 42})
            normalized = _normalize_documents([dense], index)
            self.assertEqual(normalized[0].metadata["source"], "nested/profile.md")
            self.assertEqual(normalized[0].metadata["chunk_id"], "42")

    async def test_ensemble_runs_dense_and_bm25_concurrently_and_fuses(self) -> None:
        dense = DelayedRetriever(
            label="dense",
            results=[Document(page_content="shared", metadata={"chunk_id": "a", "source": "projects.md"}), Document(page_content="dense only", metadata={"chunk_id": "b"})],
        )
        sparse = DelayedRetriever(
            label="bm25",
            results=[Document(page_content="shared", metadata={"chunk_id": "a", "source": "projects.md"}), Document(page_content="sparse only", metadata={"chunk_id": "c"})],
        )
        ensemble = TimedEnsembleRetriever(
            retrievers=[dense, sparse], weights=[0.5, 0.5], c=2, id_key="chunk_id"
        )
        with patch("app.retrieval.hybrid._build_ensemble", return_value=ensemble), patch(
            "app.retrieval.hybrid.rerank_documents", side_effect=lambda query, docs: docs
        ):
            result = await HybridRRFRetriever().ainvoke("shared")
        self.assertCountEqual(dense.started + sparse.started, ["dense", "bm25"])
        self.assertEqual(len({document.metadata["chunk_id"] for document in result}), len(result))
        self.assertEqual({document.metadata["chunk_id"] for document in result}, {"a", "b", "c"})
        self.assertTrue(all("hybrid_rank" in document.metadata for document in result))
        self.assertTrue(all("rrf_score" in document.metadata for document in result))

    def test_dense_retriever_builds_project_metadata_filter(self) -> None:
        client = QdrantClient(":memory:")
        client.create_collection(
            collection_name=settings.hybrid_collection,
            vectors_config=VectorParams(size=3, distance=Distance.COSINE),
        )
        with patch("app.retrieval.dense.qdrant_client", return_value=client), patch(
            "app.retrieval.dense.get_embeddings", return_value=FixedEmbeddings()
        ):
            retriever = build_dense_retriever(BM25Index(Path("missing-test-index.json")), "document-search-rag")
        qdrant_filter = retriever.delegate.search_kwargs["filter"]
        self.assertEqual(qdrant_filter.must[0].key, "metadata.project_id")
        self.assertEqual(qdrant_filter.must[0].match.value, "document-search-rag")

    def test_project_specific_bm25_index_filters_to_document_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bm25.json"
            write_snapshot(
                IndexSnapshot(
                    [
                        Document(page_content="Document Search uses ChromaDB", metadata={"chunk_id": "a", "project_id": "document-search-rag"}),
                        Document(page_content="Corrective RAG uses Qdrant", metadata={"chunk_id": "b", "project_id": "corrective-rag"}),
                    ],
                    {},
                    set(),
                    1,
                ),
                path,
            )
            retriever = BM25Index(path).retriever("document-search-rag")
            result = retriever.invoke("Document Search RAG technologies")
        self.assertEqual([document.metadata["chunk_id"] for document in result], ["a"])
        self.assertIsNotNone(result[0].metadata["bm25_score"])

    def test_project_sections_are_split_and_metadata_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "projects.md"
            source_path.write_text(
                "# Projects\n\n"
                "# 1. Corrective RAG –\n\n## Technology Stack\n\n"
                + ("Corrective technology stack details. " * 45)
                + "\n\n# 2. Document Search RAG – End-to-End System\n\n## Technology Stack\n\n"
                + ("Document Search uses Streamlit and ChromaDB. " * 45),
                encoding="utf-8",
            )
            corpus = load_markdown_documents(root)
            chunks = split_source(corpus.sources["projects.md"])

        corrective = [doc for doc in chunks if doc.metadata.get("project_id") == "corrective-rag"]
        document_search = [doc for doc in chunks if doc.metadata.get("project_id") == "document-search-rag"]
        self.assertTrue(corrective)
        self.assertTrue(document_search)
        self.assertTrue(all(doc.metadata["source_filename"] == "projects.md" for doc in chunks))
        self.assertTrue(all(doc.metadata["document_id"] and doc.metadata["chunk_id"] for doc in chunks))
        self.assertTrue(all(doc.metadata.get("section_heading") for doc in corrective + document_search))
        self.assertTrue(any(doc.metadata["section_heading"] == "Technology Stack" for doc in corrective + document_search))
        self.assertTrue(all("Document Search" not in doc.page_content for doc in corrective))
        self.assertTrue(all("Corrective RAG" not in doc.page_content for doc in document_search))

    def test_project_name_resolver_uses_indexed_metadata(self) -> None:
        from app.retrieval.document_awareness import resolve_project

        indexed_projects = [
            Document(page_content="corrective", metadata={"project_id": "corrective-rag", "project_name": "Corrective RAG"}),
            Document(page_content="document search", metadata={"project_id": "document-search-rag", "project_name": "Document Search RAG"}),
        ]
        self.assertEqual(
            resolve_project("What does the Document Search RAG project use?", indexed_projects),
            ("document-search-rag", "Document Search RAG"),
        )
        self.assertIsNone(resolve_project("What projects has Touqeer built?", indexed_projects))


if __name__ == "__main__":
    unittest.main()
