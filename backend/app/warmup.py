"""Background start-up warm-up so the first visitor does not pay cold-start costs.

Runs after the server is already accepting requests (``/health`` is never
delayed). Every step is best-effort: a failure is logged and never raised.
"""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter

from app.config import settings
from app.database import qdrant_client
from app.embedding_cache import query_embedding_cache
from app.providers import get_chat_model, get_embeddings
from app.retrieval.dense import _collection_exists
from app.retrieval.sparse import get_bm25_index


logger = logging.getLogger("rag")


def _warm_bm25() -> int:
    """Build the global and per-project BM25 retrievers now, not on a visitor's request."""
    index = get_bm25_index()
    documents = index.snapshot().documents
    project_ids = sorted(
        {str(d.metadata["project_id"]) for d in documents if d.metadata.get("project_id")}
    )
    index.retriever(None)
    for project_id in project_ids:
        index.retriever(project_id)
    return 1 + len(project_ids)


def _warm_embeddings() -> int:
    """Pre-embed the starter questions in ONE batched request (one round trip, not N)."""
    embeddings = get_embeddings()
    model = settings.embed_model
    missing = [q for q in settings.warmup_queries if query_embedding_cache.get(model, q) is None]
    if missing:
        for query, vector in zip(missing, embeddings.embed_documents(missing)):
            query_embedding_cache.put(model, query, vector)
    elif not settings.warmup_queries:
        embeddings.embed_query("warm-up")  # still opens the connection
    return len(settings.warmup_queries)


def _warm_qdrant() -> bool:
    """Open the Qdrant connection and prime the collection-exists cache."""
    return _collection_exists(qdrant_client(), settings.hybrid_collection)


async def _warm_llm() -> None:
    """One one-token completion opens the (async) OpenAI chat connection."""
    await get_chat_model().bind(max_tokens=1).ainvoke("ping")


async def _step(name: str, awaitable) -> None:
    started = perf_counter()
    try:
        result = await awaitable
        logger.info("warmup step=%s ok duration_ms=%.1f result=%s", name, (perf_counter() - started) * 1000, result)
    except asyncio.CancelledError:
        raise
    except Exception:  # noqa: BLE001 - warm-up must never take the app down
        logger.warning("warmup step=%s failed", name, exc_info=True)


async def warm_up() -> None:
    started = perf_counter()
    steps = [
        _step("bm25", asyncio.to_thread(_warm_bm25)),
        _step("embeddings", asyncio.to_thread(_warm_embeddings)),
        _step("qdrant", asyncio.to_thread(_warm_qdrant)),
    ]
    if settings.warmup_llm:
        steps.append(_step("llm", _warm_llm()))
    await asyncio.gather(*steps)
    logger.info("warmup done duration_ms=%.1f", (perf_counter() - started) * 1000)
