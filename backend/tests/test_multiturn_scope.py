"""Multi-turn regression tests for project-scope handling (finding F1).

A project named in an earlier turn must not hard-filter an unrelated follow-up
(contact / services / skills), while genuinely contextual follow-ups
("What stack does it use?") must keep the project. Dense (in-memory Qdrant),
BM25 (real BM25Index) and the hybrid flow are all exercised offline.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app import rag
from app.config import settings
from app.ingestion.state import IndexSnapshot, write_snapshot
from app.retrieval.dense import build_dense_retriever, reset_collection_cache
from app.retrieval.document_awareness import (
    plan_scope,
    reset_earlier_user_turns,
    set_earlier_user_turns,
)
from app.retrieval.sparse import BM25Index
from app.retrieval.trace import get_retrieval_trace


CRAG = ("corrective-rag", "Corrective RAG")
DSRAG = ("document-search-rag", "Document Search RAG")

# (text, source file, project id, project name)
CORPUS = [
    ("Corrective RAG tech stack: Python, FastAPI, LangGraph, Qdrant and Groq.", "projects.md", *CRAG),
    ("Corrective RAG limitations: the source does not confirm a public deployment.", "projects.md", *CRAG),
    ("Document Search RAG tech stack: ChromaDB, FAISS, BM25 and Streamlit.", "projects.md", *DSRAG),
    ("Contact Touqeer by email or LinkedIn for project inquiries and hiring.", "contact.md", None, None),
    ("Services: custom RAG chatbots, AI assistants and full-stack web development.", "services.md", None, None),
    ("Skills: Python, FastAPI, LangChain, Qdrant, React and Next.js.", "skills.md", None, None),
    ("About Touqeer: BS Software Engineering student at NUML in Pakistan.", "about.md", None, None),
]


def _metadata(index: int, source: str, project_id: str | None, project_name: str | None) -> dict:
    metadata = {
        "source": source,
        "source_filename": source,
        "chunk_id": f"chunk-{index}",
        "chunk_index": index,
        "document_hash": f"hash-{source}",
    }
    if project_id:
        metadata.update({"project_id": project_id, "project_name": project_name})
    return metadata


def corpus_documents() -> list[Document]:
    return [Document(page_content=row[0], metadata=_metadata(i, *row[1:])) for i, row in enumerate(CORPUS)]


class ConstantEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0]


def sources(documents: list[Document]) -> set[str]:
    return {document.metadata.get("source_filename") for document in documents}


def project_ids(documents: list[Document]) -> set[str | None]:
    return {document.metadata.get("project_id") for document in documents}


def conversation(*user_turns: str) -> list[dict]:
    messages: list[dict] = []
    for index, turn in enumerate(user_turns):
        if index:
            messages.append({"role": "assistant", "content": "Earlier answer."})
        messages.append({"role": "user", "content": turn})
    return messages


class PlanScopeTests(unittest.TestCase):
    """Pure decision logic: which query text and which (if any) project filter."""

    def setUp(self) -> None:
        self.docs = corpus_documents()
        self.first = "Tell me about Touqeer's Corrective RAG project"

    def plan(self, *turns: str):
        return plan_scope(turns[-1], list(turns[:-1]), self.docs)

    def test_1_contact_followup_is_unscoped_and_drops_project_text(self) -> None:
        plan = self.plan(self.first, "How can I contact him for a project?")
        self.assertIsNone(plan.project)
        self.assertEqual(plan.reason, "global_topic")
        self.assertNotIn("Corrective", plan.query)

    def test_2_services_followup_is_unscoped(self) -> None:
        plan = self.plan(self.first, "What services does he offer?")
        self.assertIsNone(plan.project)
        self.assertEqual(plan.reason, "global_topic")

    def test_3_skills_followup_is_unscoped(self) -> None:
        plan = self.plan(self.first, "What skills does he have?")
        self.assertIsNone(plan.project)

    def test_4_stack_followup_keeps_project(self) -> None:
        plan = self.plan(self.first, "What stack does it use?")
        self.assertEqual(plan.project, CRAG)
        self.assertEqual(plan.reason, "carried_by_reference")
        self.assertIn("Corrective RAG", plan.query)

    def test_5_limitations_followup_keeps_project(self) -> None:
        self.assertEqual(self.plan(self.first, "What are its limitations?").project, CRAG)
        self.assertEqual(self.plan(self.first, "And the limitations?").project, CRAG)

    def test_6_switching_project_uses_the_newly_named_one(self) -> None:
        # Old behaviour: the longer earlier name ("Document Search RAG") won the tie.
        plan = self.plan("Tell me about the Document Search RAG project", "What about Corrective RAG?")
        self.assertEqual(plan.project, CRAG)
        self.assertEqual(plan.reason, "named_in_question")
        self.assertEqual(plan.query, "What about Corrective RAG?")

    def test_7_standalone_questions_keep_single_turn_behaviour(self) -> None:
        project = plan_scope("What does the Document Search RAG project use?", [], self.docs)
        self.assertEqual(project.project, DSRAG)
        general = plan_scope("What projects has Touqeer built?", [], self.docs)
        self.assertIsNone(general.project)
        self.assertEqual(general.query, "What projects has Touqeer built?")
        self.assertIsNone(plan_scope("How can I contact him?", [], self.docs).project)

    def test_reference_plus_global_topic_is_soft_context_not_a_filter(self) -> None:
        plan = self.plan(self.first, "How can I hire him for something like it?")
        self.assertIsNone(plan.project)
        self.assertEqual(plan.reason, "mixed_soft_context")
        self.assertIn("Corrective RAG", plan.query)

    def test_stack_question_about_him_is_not_carried(self) -> None:
        self.assertIsNone(self.plan(self.first, "What technologies does he use?").project)

    def test_continuation_only_carries_right_after_a_project_turn(self) -> None:
        self.assertEqual(self.plan(self.first, "Tell me more").project, CRAG)
        self.assertIsNone(self.plan(self.first, "How can I contact him?", "Tell me more").project)

    def test_unrelated_followup_falls_back_to_legacy_joined_query(self) -> None:
        plan = self.plan("What are his hobbies?", "What about his projects?")
        self.assertIsNone(plan.project)
        self.assertEqual(plan.query, "What are his hobbies? What about his projects?")


class FilterAndHybridTests(unittest.IsolatedAsyncioTestCase):
    """Dense + BM25 + hybrid flow over an in-memory Qdrant collection and a real BM25 index."""

    def setUp(self) -> None:
        reset_collection_cache()
        documents = corpus_documents()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        hashes = {document.metadata["source"]: document.metadata["document_hash"] for document in documents}
        path = Path(self._tmp.name) / "bm25.json"
        write_snapshot(IndexSnapshot(documents, hashes, set()), path)
        self.index = BM25Index(path)

        self.client = QdrantClient(":memory:")
        self.client.create_collection(
            collection_name=settings.hybrid_collection,
            vectors_config=VectorParams(size=3, distance=Distance.COSINE),
        )
        self.client.upsert(
            collection_name=settings.hybrid_collection,
            points=[
                PointStruct(id=i + 1, vector=[1.0, 0.0, 0.0], payload={"text": d.page_content, "metadata": d.metadata})
                for i, d in enumerate(documents)
            ],
        )
        for target, kwargs in (
            ("app.retrieval.sparse._bm25_index", {"new": self.index}),
            ("app.retrieval.dense.qdrant_client", {"return_value": self.client}),
            ("app.retrieval.dense.get_embeddings", {"return_value": ConstantEmbeddings()}),
        ):
            patcher = patch(target, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)

    async def run_turns(self, *user_turns: str) -> list[Document]:
        """Exactly what stream_answer does around retrieval."""
        current, earlier = rag.split_conversation(conversation(*user_turns))
        token = set_earlier_user_turns(earlier)
        try:
            return await rag.aretrieve_documents(current)
        finally:
            reset_earlier_user_turns(token)

    # -- dense and BM25 filters, each on their own ---------------------------------
    async def test_dense_filter_scopes_to_project_and_unscoped_includes_global(self) -> None:
        scoped = await build_dense_retriever(self.index, "corrective-rag").ainvoke("contact")
        self.assertEqual(project_ids(scoped), {"corrective-rag"})
        self.assertNotIn("contact.md", sources(scoped))
        unscoped = await build_dense_retriever(self.index, None).ainvoke("contact")
        self.assertIn("contact.md", sources(unscoped))

    async def test_bm25_filter_scopes_to_project_and_unscoped_includes_global(self) -> None:
        scoped = await self.index.retriever("corrective-rag").ainvoke("contact email")
        self.assertEqual(project_ids(scoped), {"corrective-rag"})
        unscoped = await self.index.retriever(None).ainvoke("contact email")
        self.assertEqual(unscoped[0].metadata["source_filename"], "contact.md")

    # -- the seven required multi-turn scenarios through the hybrid flow ------------
    first = "Tell me about Touqeer's Corrective RAG project"

    async def test_1_project_then_contact_retrieves_contact_md(self) -> None:
        documents = await self.run_turns(self.first, "How can I contact him for a project?")
        self.assertIn("contact.md", sources(documents))
        self.assertEqual(get_retrieval_trace()["scope_reason"], "global_topic")

    async def test_2_project_then_services_retrieves_services_md(self) -> None:
        self.assertIn("services.md", sources(await self.run_turns(self.first, "What services does he offer?")))

    async def test_3_project_then_skills_retrieves_skills_md(self) -> None:
        self.assertIn("skills.md", sources(await self.run_turns(self.first, "What skills does he have?")))

    async def test_4_project_then_stack_keeps_project_context(self) -> None:
        documents = await self.run_turns(self.first, "What stack does it use?")
        self.assertEqual(project_ids(documents), {"corrective-rag"})
        self.assertTrue(any("tech stack" in d.page_content for d in documents))
        self.assertEqual(get_retrieval_trace()["project_filter"]["project_id"], "corrective-rag")

    async def test_5_project_then_limitations_keeps_project_retrieval(self) -> None:
        documents = await self.run_turns(self.first, "What are its limitations?")
        self.assertEqual(project_ids(documents), {"corrective-rag"})
        self.assertTrue(any("limitations" in d.page_content for d in documents))

    async def test_6_switching_projects_retrieves_the_new_project(self) -> None:
        documents = await self.run_turns("Tell me about the Document Search RAG project", "What about Corrective RAG?")
        self.assertEqual(project_ids(documents), {"corrective-rag"})

    async def test_7_standalone_project_question_is_scoped_as_before(self) -> None:
        documents = await self.run_turns("What does the Document Search RAG project use?")
        self.assertEqual(project_ids(documents), {"document-search-rag"})
        self.assertEqual(get_retrieval_trace()["scope_reason"], "named_in_question")
        self.assertFalse(get_retrieval_trace()["scope_fallback"])

    # -- fallback ---------------------------------------------------------------------
    async def test_empty_scoped_search_falls_back_to_one_unscoped_retry(self) -> None:
        from app.retrieval import hybrid

        real_build = hybrid._build_ensemble
        calls: list[str | None] = []

        class Empty:
            _candidate_stats: dict = {}

            async def ainvoke(self, query: str):
                return []

        def build(project_id: str | None = None):
            calls.append(project_id)
            return Empty() if project_id else real_build(project_id=None)

        with patch("app.retrieval.hybrid._build_ensemble", side_effect=build):
            documents = await self.run_turns("What does the Corrective RAG project use?")
        self.assertEqual(calls, ["corrective-rag", None])  # exactly one retry, no more
        self.assertTrue(documents)
        trace = get_retrieval_trace()
        self.assertTrue(trace["scope_fallback"])
        self.assertIsNone(trace["project_filter"])

    async def test_no_fallback_retry_when_scoped_search_succeeds(self) -> None:
        from app.retrieval import hybrid

        real_build = hybrid._build_ensemble
        calls: list[str | None] = []

        def build(project_id: str | None = None):
            calls.append(project_id)
            return real_build(project_id=project_id)

        with patch("app.retrieval.hybrid._build_ensemble", side_effect=build):
            await self.run_turns(self.first, "What stack does it use?")
        self.assertEqual(calls, ["corrective-rag"])


if __name__ == "__main__":
    unittest.main()
