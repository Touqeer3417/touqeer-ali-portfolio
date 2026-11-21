"""Concurrent Dense + BM25 retrieval with LangChain weighted RRF."""

from __future__ import annotations

import logging
import json
from functools import lru_cache
from time import perf_counter
from typing import Any

from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, PrivateAttr

from app.config import settings
from app.retrieval.dense import build_dense_retriever
from app.retrieval.document_awareness import get_earlier_user_turns, plan_scope
from app.retrieval.reranker import rerank_documents
from app.retrieval.sparse import get_bm25_index, get_bm25_retriever
from app.retrieval.trace import set_retrieval_trace


logger = logging.getLogger("rag")


class TimedEnsembleRetriever(EnsembleRetriever):
    """LangChain ensemble with a timer around only the local RRF step."""

    _candidate_stats: dict[str, int] = PrivateAttr(default_factory=dict)

    def weighted_reciprocal_rank(self, doc_lists: list[list[Document]]) -> list[Document]:
        started = perf_counter()
        try:
            id_key = self.id_key
            source_names = ("dense", "bm25")
            ranks: dict[str, dict[str, int]] = {}
            scores: dict[str, float] = {}
            component_scores: dict[str, dict[str, float | None]] = {}
            for source_index, document_list in enumerate(doc_lists):
                source = source_names[source_index] if source_index < len(source_names) else f"retriever_{source_index}"
                weight = self.weights[source_index]
                for rank, document in enumerate(document_list, start=1):
                    identity = str(document.metadata.get(id_key) if id_key else document.page_content)
                    ranks.setdefault(identity, {})[source] = rank
                    scores[identity] = scores.get(identity, 0.0) + weight / (rank + self.c)
                    component_scores.setdefault(identity, {})["dense_score"] = document.metadata.get("dense_score")
                    component_scores[identity]["bm25_score"] = document.metadata.get("bm25_score")

            fused = super().weighted_reciprocal_rank(doc_lists)
            self._candidate_stats = {
                "dense_candidate_count": len(doc_lists[0]) if doc_lists else 0,
                "bm25_candidate_count": len(doc_lists[1]) if len(doc_lists) > 1 else 0,
                "fused_candidate_count": len(fused),
            }
            annotated: list[Document] = []
            for hybrid_rank, document in enumerate(fused, start=1):
                identity = str(document.metadata.get(id_key) if id_key else document.page_content)
                metadata = dict(document.metadata)
                metadata.update(
                    {
                        "initial_dense_rank": ranks.get(identity, {}).get("dense"),
                        "initial_bm25_rank": ranks.get(identity, {}).get("bm25"),
                        "initial_hybrid_rank": hybrid_rank,
                        "rrf_score": scores.get(identity),
                        # Current retriever APIs return documents without raw dense scores.
                        "dense_score": component_scores.get(identity, {}).get("dense_score"),
                        "bm25_score": component_scores.get(identity, {}).get("bm25_score"),
                    }
                )
                annotated.append(Document(page_content=document.page_content, metadata=metadata))
            return annotated
        finally:
            logger.info(
                "rag_stage stage=rrf_fusion duration_ms=%.1f",
                (perf_counter() - started) * 1000,
            )


def _unique_documents(documents: list[Document]) -> list[Document]:
    unique: list[Document] = []
    seen: set[str] = set()
    for document in documents:
        chunk_id = str(document.metadata.get("chunk_id") or document.page_content)
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        unique.append(document)
    return unique


def _build_ensemble(project_id: str | None = None) -> TimedEnsembleRetriever:
    if settings.dense_weight + settings.bm25_weight <= 0:
        raise ValueError("At least one hybrid retrieval weight must be greater than zero")
    index = get_bm25_index()
    dense_retriever = build_dense_retriever(index, project_id=project_id)
    sparse_retriever = get_bm25_retriever(project_id=project_id)
    return TimedEnsembleRetriever(
        retrievers=[dense_retriever, sparse_retriever],
        weights=[settings.dense_weight, settings.bm25_weight],
        c=settings.rrf_k,
        id_key="chunk_id",
    )


def _scope_stats(ensemble: Any, reason: str, fallback: bool) -> dict[str, Any]:
    """Candidate counts plus why the search was (not) restricted to one project."""
    return {
        **getattr(ensemble, "_candidate_stats", {}),
        "scope_reason": reason,
        "scope_fallback": fallback,
    }


class HybridRRFRetriever(BaseRetriever):
    """Apply LangChain EnsembleRetriever's weighted reciprocal rank fusion."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    def _trace_document(document: Document, rank: int, selected: bool = False) -> dict[str, Any]:
        metadata = document.metadata
        return {
            "chunk_id": metadata.get("chunk_id"),
            "document_id": metadata.get("document_id"),
            "source_filename": metadata.get("source_filename") or metadata.get("file_name") or metadata.get("source"),
            "project_id": metadata.get("project_id"),
            "project_name": metadata.get("project_name"),
            "section_heading": metadata.get("section_heading"),
            "initial_dense_rank": metadata.get("initial_dense_rank"),
            "initial_bm25_rank": metadata.get("initial_bm25_rank"),
            "initial_hybrid_rank": metadata.get("initial_hybrid_rank", rank),
            "dense_score": metadata.get("dense_score"),
            "bm25_score": metadata.get("bm25_score"),
            "rrf_score": metadata.get("rrf_score"),
            "reranker_score": metadata.get("reranker_score"),
            "reranked_position": rank,
            "selected_final_top_k": selected,
        }

    def _finish(
        self,
        query: str,
        documents: list[Document],
        *,
        project: tuple[str, str] | None = None,
        candidate_stats: dict[str, Any] | None = None,
    ) -> list[Document]:
        # Retriever instances may return cached BM25 Document objects. Copy their
        # metadata before attaching request-specific ranks or reranker scores.
        documents = [
            Document(page_content=document.page_content, metadata=dict(document.metadata))
            for document in documents
        ]
        documents = _unique_documents(documents)
        before_reranking = [self._trace_document(document, rank) for rank, document in enumerate(documents, start=1)]
        documents = rerank_documents(query, documents)
        for rank, document in enumerate(documents, start=1):
            document.metadata["reranked_position"] = rank
        selected = documents[: settings.rrf_limit]
        context_started = perf_counter()
        for rank, document in enumerate(selected, start=1):
            document.metadata["hybrid_rank"] = rank
            document.metadata["final_rank"] = rank
        reranker_status = (
            "disabled"
            if not settings.reranker_enabled
            else "success"
            if documents and all("reranker_score" in document.metadata for document in documents[: settings.reranker_candidate_k])
            else "failed_fallback"
        )
        expected_project_id, expected_project_name = project or (None, None)
        relevant_candidates = sum(document.metadata.get("project_id") == expected_project_id for document in documents) if expected_project_id else None
        relevant_final = sum(document.metadata.get("project_id") == expected_project_id for document in selected) if expected_project_id else None
        incorrect_project_final = sum(
            bool(document.metadata.get("project_id"))
            and document.metadata.get("project_id") != expected_project_id
            for document in selected
        ) if expected_project_id else None
        after_reranking = [
            self._trace_document(document, rank, selected=document in selected)
            for rank, document in enumerate(documents, start=1)
        ]
        trace = {
            **(candidate_stats or {}),
            "unique_candidate_count": len(before_reranking),
            "final_top_k": len(selected),
            "project_filter": {"project_id": expected_project_id, "project_name": expected_project_name} if project else None,
            "project_relevant_candidate_count": relevant_candidates,
            "project_relevant_final_count": relevant_final,
            "incorrect_project_final_count": incorrect_project_final,
            "reranker_enabled": settings.reranker_enabled,
            "reranker_status": reranker_status,
            "reranker_candidates_scored": min(len(documents), settings.reranker_candidate_k) if reranker_status == "success" else 0,
            "before_reranking": before_reranking,
            "after_reranking": after_reranking,
        }
        set_retrieval_trace(trace)
        logger.info("rag_retrieval_trace %s", json.dumps(trace, ensure_ascii=False, separators=(",", ":")))
        logger.info(
            "rag_stage stage=final_context_selection duration_ms=%.1f chunks=%d",
            (perf_counter() - context_started) * 1000,
            len(selected),
        )
        return selected

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        started = perf_counter()
        set_retrieval_trace(None)
        index = get_bm25_index()
        plan = plan_scope(query, get_earlier_user_turns(), index.snapshot().documents)
        project, fallback = plan.project, False
        ensemble = _build_ensemble(project_id=project[0] if project else None)
        documents = ensemble.invoke(plan.query)
        if project and not documents:
            # Scoped search found nothing: retry once without the project filter.
            project, fallback = None, True
            ensemble = _build_ensemble(project_id=None)
            documents = ensemble.invoke(plan.query)
        result = self._finish(
            plan.query,
            documents,
            project=project,
            candidate_stats=_scope_stats(ensemble, plan.reason, fallback),
        )
        logger.info("rag_stage stage=hybrid_retrieval duration_ms=%.1f", (perf_counter() - started) * 1000)
        return result

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> list[Document]:
        started = perf_counter()
        set_retrieval_trace(None)
        index = get_bm25_index()
        plan = plan_scope(query, get_earlier_user_turns(), index.snapshot().documents)
        project, fallback = plan.project, False
        ensemble = _build_ensemble(project_id=project[0] if project else None)
        # EnsembleRetriever.ainvoke concurrently awaits each retriever's ainvoke.
        documents = await ensemble.ainvoke(plan.query)
        if project and not documents:
            # Scoped search found nothing: retry once without the project filter.
            project, fallback = None, True
            ensemble = _build_ensemble(project_id=None)
            documents = await ensemble.ainvoke(plan.query)
        result = self._finish(
            plan.query,
            documents,
            project=project,
            candidate_stats=_scope_stats(ensemble, plan.reason, fallback),
        )
        logger.info("rag_stage stage=hybrid_retrieval duration_ms=%.1f", (perf_counter() - started) * 1000)
        return result


@lru_cache(maxsize=1)
def get_hybrid_retriever() -> HybridRRFRetriever:
    """Return a cached hybrid retriever; per-request index snapshots refresh by mtime."""
    return HybridRRFRetriever()
