"""Dense retrieval over the existing unnamed-vector Qdrant collection."""

from __future__ import annotations

import hashlib
import logging
from contextlib import contextmanager
from time import perf_counter
from typing import Any, Iterator

from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_qdrant import QdrantVectorStore
from pydantic import ConfigDict, Field
from qdrant_client import models

from app.config import settings
from app.database import qdrant_client
from app.embedding_cache import query_embedding_cache
from app.latency import RequestLatency, current_request_latency, record_stage_for
from app.providers import get_embeddings
from app.retrieval.sparse import BM25Index, EmptyRetriever, get_bm25_index


logger = logging.getLogger("rag")


class TimedEmbeddings(Embeddings):
    """Timing adapter around the application's existing cached embedding model."""

    def __init__(self, embeddings: Embeddings, latency_request: RequestLatency | None = None) -> None:
        self.embeddings = embeddings
        self.latency_request = latency_request

    def _cached(self, text: str) -> list[float] | None:
        vector = query_embedding_cache.get(settings.embed_model, text)
        if vector is not None and self.latency_request is not None:
            self.latency_request.flags["embedding_cache_hit"] = True
        return vector

    def embed_query(self, text: str) -> list[float]:
        started = perf_counter()
        try:
            vector = self._cached(text)
            if vector is None:
                vector = self.embeddings.embed_query(text)
                query_embedding_cache.put(settings.embed_model, text, vector)
            return vector
        finally:
            duration_ms = (perf_counter() - started) * 1000
            record_stage_for(self.latency_request, "embedding_ms", duration_ms)
            logger.info("rag_stage stage=query_embedding duration_ms=%.1f", duration_ms)

    async def aembed_query(self, text: str) -> list[float]:
        started = perf_counter()
        try:
            vector = self._cached(text)
            if vector is None:
                if hasattr(self.embeddings, "aembed_query"):
                    vector = await self.embeddings.aembed_query(text)
                else:
                    vector = self.embeddings.embed_query(text)
                query_embedding_cache.put(settings.embed_model, text, vector)
            return vector
        finally:
            duration_ms = (perf_counter() - started) * 1000
            record_stage_for(self.latency_request, "embedding_ms", duration_ms)
            logger.info("rag_stage stage=query_embedding duration_ms=%.1f", duration_ms)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        if hasattr(self.embeddings, "aembed_documents"):
            return await self.embeddings.aembed_documents(texts)
        return self.embeddings.embed_documents(texts)


@contextmanager
def _vector_search_timer() -> Iterator[None]:
    """Record vector_search_ms = (delegate call) - (query embedding inside it).

    langchain-qdrant embeds the query and calls ``client.query_points`` in one
    synchronous method, so the two cannot be timed separately without changing
    the call. TimedEmbeddings already records embedding_ms during this window;
    subtracting it leaves the Qdrant search, its network round trip and the
    executor hop. The request is captured on entry (embedding may be recorded
    from a worker thread).
    """
    request = current_request_latency()
    embedded_before = request.values.get("embedding_ms", 0.0) if request else 0.0
    started = perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (perf_counter() - started) * 1000
        embedded_ms = (request.values.get("embedding_ms", 0.0) - embedded_before) if request else 0.0
        record_stage_for(request, "vector_search_ms", elapsed_ms - max(0.0, embedded_ms))


def _normalize_documents(documents: list[Document], index: BM25Index) -> list[Document]:
    snapshot = index.snapshot()
    by_content: dict[str, list[dict[str, Any]]] = {}
    by_point_id: dict[str, dict[str, Any]] = {}
    for saved in snapshot.documents:
        by_content.setdefault(saved.page_content, []).append(saved.metadata)
        for identity in (saved.metadata.get("qdrant_id"), saved.metadata.get("chunk_id")):
            if identity is not None:
                by_point_id[str(identity)] = saved.metadata

    normalized: list[Document] = []
    for document in documents:
        metadata = dict(document.metadata)
        source = metadata.get("source")
        point_id = metadata.get("_id")
        point_match = by_point_id.get(str(point_id)) if point_id is not None else None
        matches = [point_match] if point_match else by_content.get(document.page_content, [])
        if not isinstance(source, str) or not source:
            if matches:
                metadata = {**matches[0], **metadata}
                source = metadata.get("source")
        if not isinstance(source, str) or not source:
            continue

        expected_hash = snapshot.source_hashes.get(source)
        actual_hash = metadata.get("document_hash")
        if source in snapshot.legacy_sources:
            if actual_hash:
                # Ignore partially upserted new-version chunks until their snapshot commits.
                continue
        elif expected_hash is not None and actual_hash != expected_hash:
            matching = next(
                (
                    item for item in matches
                    if item.get("source") == source
                    and item.get("document_hash") == expected_hash
                ),
                None,
            )
            if matching is None:
                continue
            metadata = {**metadata, **matching, "document_hash": expected_hash}
        elif expected_hash is None:
            # Suppress stale chunks from deleted documents and interrupted updates.
            continue

        # Old indexed points may lack nested metadata; recover their exact stable
        # chunk identity from the shared snapshot so RRF deduplication still works.
        matching = next(
            (
                item for item in matches
                if item.get("source") == source
                and (expected_hash is None or item.get("document_hash") == expected_hash)
            ),
            None,
        )
        if matching:
            for key, value in matching.items():
                metadata.setdefault(key, value)

        metadata.setdefault("chunk_id", hashlib.sha256(
            f"{source}\0{document.page_content}".encode("utf-8")
        ).hexdigest())
        metadata["retrieval_method"] = "dense"
        normalized.append(Document(page_content=document.page_content, metadata=metadata))
    return normalized


class StableDenseRetriever(BaseRetriever):
    """Add stable chunk identity and active-version filtering around a vector-store retriever."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    delegate: Any = Field(exclude=True)
    index: Any = Field(exclude=True)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        started = perf_counter()
        try:
            with _vector_search_timer():
                documents = self.delegate.invoke(query)
            return _normalize_documents(documents, self.index)
        finally:
            logger.info("rag_stage stage=dense_retrieval duration_ms=%.1f", (perf_counter() - started) * 1000)

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> list[Document]:
        started = perf_counter()
        try:
            with _vector_search_timer():
                documents = await self.delegate.ainvoke(query)
            return _normalize_documents(documents, self.index)
        finally:
            logger.info("rag_stage stage=dense_retrieval duration_ms=%.1f", (perf_counter() - started) * 1000)


# collection name -> client that already confirmed it exists. Only positive
# answers are kept, so a missing collection is re-checked on every request.
_confirmed_collections: dict[str, Any] = {}


def _collection_exists(client: Any, name: str) -> bool:
    """`collection_exists` with a cached positive answer (saves one round trip per request)."""
    if _confirmed_collections.get(name) is client:
        return True
    if client.collection_exists(name):
        _confirmed_collections[name] = client
        return True
    return False


def reset_collection_cache() -> None:
    """Forget confirmed collections (use after dropping or recreating one in-process)."""
    _confirmed_collections.clear()


def build_dense_retriever(index: BM25Index, project_id: str | None = None) -> BaseRetriever:
    """Build a LangChain Qdrant vector-store retriever over the existing collection."""
    client = qdrant_client()
    if not _collection_exists(client, settings.hybrid_collection):
        return EmptyRetriever()

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.hybrid_collection,
        embedding=TimedEmbeddings(get_embeddings(), current_request_latency()),
        retrieval_mode="dense",
        vector_name="",
        content_payload_key="text",
        metadata_payload_key="metadata",
        validate_collection_config=False,
    )
    search_kwargs: dict[str, Any] = {"k": settings.dense_top_k}
    if project_id:
        search_kwargs["filter"] = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.project_id",
                    match=models.MatchValue(value=project_id),
                )
            ]
        )
    delegate = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )
    return StableDenseRetriever(delegate=delegate, index=index)
