"""Persisted BM25 sparse retrieval over the active corpus snapshot."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from time import perf_counter
from typing import Any

from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.callbacks import AsyncCallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict
from qdrant_client.http import models

from app.config import settings
from app.database import qdrant_client
from app.ingestion.state import IndexSnapshot, read_snapshot, write_snapshot


logger = logging.getLogger("rag")


def _metadata(payload: dict[str, Any]) -> dict[str, Any]:
    nested = payload.get("metadata")
    flattened = {key: value for key, value in payload.items() if key not in {"text", "metadata"}}
    if isinstance(nested, dict):
        flattened.update(nested)
    return flattened


def bootstrap_snapshot_from_qdrant() -> IndexSnapshot:
    """Seed a local BM25 source snapshot from the already-indexed Qdrant data."""
    client = qdrant_client()
    if not client.collection_exists(settings.hybrid_collection):
        return IndexSnapshot(documents=[], source_hashes={}, legacy_sources=set())

    documents: list[Document] = []
    legacy_sources: set[str] = set()
    offset = None
    seen_offsets: set[str] = set()
    while True:
        points, next_offset = client.scroll(
            collection_name=settings.hybrid_collection,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            content = payload.get("text")
            if not isinstance(content, str) or not content.strip():
                continue
            metadata = _metadata(payload)
            source = metadata.get("source")
            if not isinstance(source, str) or not source:
                source = f"legacy/{point.id}"
            metadata.update(
                {
                    "source": source,
                    "qdrant_id": str(point.id),
                    "chunk_id": str(metadata.get("chunk_id") or point.id),
                }
            )
            documents.append(Document(page_content=content, metadata=metadata))
            if not metadata.get("document_hash"):
                legacy_sources.add(source)

        # Qdrant returns None when the final page has been reached. Always stop
        # here; otherwise the next request with offset=None restarts at page one.
        if next_offset is None:
            break
        cursor = repr(next_offset)
        if cursor in seen_offsets or next_offset == offset:
            raise RuntimeError("Qdrant scroll returned a repeated pagination cursor")
        seen_offsets.add(cursor)
        offset = next_offset

    snapshot = IndexSnapshot(
        documents=documents,
        source_hashes={},
        legacy_sources=legacy_sources,
        generation=0,
    )
    write_snapshot(snapshot)
    logger.info("Bootstrapped local BM25 corpus from Qdrant chunks=%d", len(documents))
    return snapshot


class EmptyRetriever(BaseRetriever):
    """A valid LangChain retriever used when the Knowledge Base is empty."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        return []


class TimedBM25Retriever(BaseRetriever):
    """Time BM25 retrieval while preserving its LangChain async interface."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    delegate: Any

    def _with_scores(self, query: str, documents: list[Document]) -> list[Document]:
        corpus_scores = self.delegate.vectorizer.get_scores(
            self.delegate.preprocess_func(query)
        )
        scores_by_id = {
            str(document.metadata.get("chunk_id")): float(score)
            for document, score in zip(self.delegate.docs, corpus_scores)
        }
        return [
            Document(
                page_content=document.page_content,
                metadata={
                    **document.metadata,
                    "bm25_score": scores_by_id.get(str(document.metadata.get("chunk_id"))),
                    "retrieval_method": "bm25",
                },
            )
            for document in documents
        ]

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        started = perf_counter()
        try:
            return self._with_scores(query, self.delegate.invoke(query))
        finally:
            logger.info("rag_stage stage=bm25_retrieval duration_ms=%.1f", (perf_counter() - started) * 1000)

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> list[Document]:
        started = perf_counter()
        try:
            documents = await self.delegate.ainvoke(query)
            return self._with_scores(query, documents)
        finally:
            logger.info("rag_stage stage=bm25_retrieval duration_ms=%.1f", (perf_counter() - started) * 1000)


class BM25Index:
    """Reload the persisted BM25 corpus only when its snapshot changes."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.bm25_index_path
        self._lock = threading.RLock()
        self._mtime_ns: int | None = None
        self._snapshot: IndexSnapshot | None = None
        self._retrievers: dict[str | None, BaseRetriever] = {}

    def snapshot(self, *, force: bool = False) -> IndexSnapshot:
        with self._lock:
            mtime = self.path.stat().st_mtime_ns if self.path.exists() else None
            if self._snapshot is None or force or mtime != self._mtime_ns:
                snapshot = read_snapshot(self.path)
                if snapshot is None:
                    snapshot = bootstrap_snapshot_from_qdrant()
                self._snapshot = snapshot
                self._mtime_ns = self.path.stat().st_mtime_ns if self.path.exists() else None
                self._retrievers.clear()
            return self._snapshot

    def retriever(self, project_id: str | None = None) -> BaseRetriever:
        with self._lock:
            snapshot = self.snapshot()
            if project_id not in self._retrievers:
                documents = [
                    document
                    for document in snapshot.documents
                    if project_id is None or document.metadata.get("project_id") == project_id
                ]
                if not documents:
                    self._retrievers[project_id] = EmptyRetriever()
                else:
                    started = perf_counter()
                    retriever = BM25Retriever.from_documents(documents)
                    retriever.k = settings.bm25_top_k
                    self._retrievers[project_id] = TimedBM25Retriever(delegate=retriever)
                    logger.info(
                        "rag_stage stage=bm25_index_load duration_ms=%.1f documents=%d project_id=%s",
                        (perf_counter() - started) * 1000,
                        len(documents),
                        project_id or "all",
                    )
            return self._retrievers[project_id]


_bm25_index = BM25Index()


def get_bm25_index() -> BM25Index:
    return _bm25_index


def get_bm25_retriever(project_id: str | None = None) -> BaseRetriever:
    return _bm25_index.retriever(project_id)
