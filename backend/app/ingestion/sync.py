"""Incrementally synchronize the Knowledge Base into dense Qdrant and BM25."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import models
from qdrant_client.models import Distance, VectorParams

from app.config import settings
from app.database import qdrant_client
from app.ingestion.loader import load_markdown_documents
from app.ingestion.splitter import INDEX_SCHEMA_VERSION, chunking_fingerprint, split_source
from app.ingestion.state import IndexSnapshot, read_snapshot, write_snapshot
from app.providers import get_embeddings
from app.retrieval.dense import TimedEmbeddings


logger = logging.getLogger("rag_ingestion")


def _metadata(payload: dict[str, Any]) -> dict[str, Any]:
    nested = payload.get("metadata")
    metadata = {key: value for key, value in payload.items() if key not in {"text", "metadata"}}
    if isinstance(nested, dict):
        metadata.update(nested)
    return metadata


def _scan_qdrant() -> dict[str, list[tuple[Any, dict[str, Any]]]]:
    client = qdrant_client()
    if not client.collection_exists(settings.hybrid_collection):
        return {}
    points_by_source: dict[str, list[tuple[Any, dict[str, Any]]]] = defaultdict(list)
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=settings.hybrid_collection,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            metadata = _metadata(point.payload or {})
            source = metadata.get("source")
            if isinstance(source, str) and source:
                points_by_source[source].append((point.id, metadata))
        if offset is None:
            break
    return points_by_source


def _ensure_collection() -> None:
    client = qdrant_client()
    if not client.collection_exists(settings.hybrid_collection):
        # Obtain the existing model's vector width once when bootstrapping a missing collection.
        vector_size = len(get_embeddings().embed_query("portfolio knowledge base"))
        client.create_collection(
            collection_name=settings.hybrid_collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        client.create_payload_index(
            collection_name=settings.hybrid_collection,
            field_name="text",
            field_schema=models.TextIndexParams(type=models.TextIndexType.TEXT, scoring=True),
            wait=True,
        )

    # Qdrant requires a keyword payload index to filter nested metadata.project_id.
    # Ensure it for existing collections too; project filtering must not fail on the
    # already-deployed collection when the ingestion schema adds this metadata.
    payload_schema = client.get_collection(settings.hybrid_collection).payload_schema or {}
    if "metadata.project_id" not in payload_schema:
        client.create_payload_index(
            collection_name=settings.hybrid_collection,
            field_name="metadata.project_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
            wait=True,
        )


def _vector_store() -> QdrantVectorStore:
    _ensure_collection()
    return QdrantVectorStore(
        client=qdrant_client(),
        collection_name=settings.hybrid_collection,
        embedding=TimedEmbeddings(get_embeddings()),
        retrieval_mode="dense",
        vector_name="",
        content_payload_key="text",
        metadata_payload_key="metadata",
        validate_collection_config=False,
    )


def _group_documents(documents: list[Document]) -> dict[str, list[Document]]:
    grouped: dict[str, list[Document]] = defaultdict(list)
    for document in documents:
        grouped[str(document.metadata["source"])].append(document)
    return grouped


def _remove_stale_points(snapshot: IndexSnapshot) -> int:
    client = qdrant_client()
    if not client.collection_exists(settings.hybrid_collection):
        return 0

    stale_ids: list[Any] = []
    active_chunk_ids: dict[str, set[str]] = defaultdict(set)
    for document in snapshot.documents:
        source = document.metadata.get("source")
        chunk_id = document.metadata.get("chunk_id")
        if isinstance(source, str) and source and chunk_id is not None:
            active_chunk_ids[source].add(str(chunk_id))

    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=settings.hybrid_collection,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            metadata = _metadata(point.payload or {})
            source = metadata.get("source")
            # Leave foreign or legacy records without ownership metadata untouched.
            if not isinstance(source, str) or not source:
                continue
            document_hash = metadata.get("document_hash")
            expected_hash = snapshot.source_hashes.get(source)
            keep_legacy = (
                source in snapshot.legacy_sources
                and not document_hash
            )
            chunk_id = metadata.get("chunk_id") or str(point.id)
            if (
                expected_hash is not None
                and document_hash == expected_hash
                and str(chunk_id) in active_chunk_ids.get(source, set())
            ):
                continue
            if keep_legacy:
                continue
            stale_ids.append(point.id)
        if offset is None:
            break

    if stale_ids:
        client.delete(
            collection_name=settings.hybrid_collection,
            points_selector=models.PointIdsList(points=stale_ids),
            wait=True,
        )
    return len(stale_ids)


def sync_knowledge_base() -> dict[str, Any]:
    """Incrementally update Qdrant and the persisted BM25 corpus as one generation."""
    # Keep required Qdrant payload indexes current even when the source documents
    # are unchanged and no document needs re-embedding.
    _ensure_collection()
    corpus = load_markdown_documents(settings.knowledge_dir)
    current_snapshot = read_snapshot()
    if current_snapshot is None:
        # First-time migration: preserve the currently deployed Qdrant chunks in BM25
        # until their replacements have been embedded and written successfully.
        logger.info("No BM25 snapshot found; importing the existing Qdrant chunks")
        from app.retrieval.sparse import bootstrap_snapshot_from_qdrant

        current_snapshot = bootstrap_snapshot_from_qdrant()

    previous_docs = _group_documents(current_snapshot.documents)
    source_hashes = dict(current_snapshot.source_hashes)
    legacy_sources = set(current_snapshot.legacy_sources)
    next_docs = dict(previous_docs)
    failed_sources = set(corpus.failed_sources)
    updated_sources: list[str] = []
    unchanged_sources: list[str] = []
    deleted_sources = sorted(
        (set(source_hashes) | legacy_sources) - corpus.discovered_sources
    )

    for source, loaded in corpus.sources.items():
        current_chunks = previous_docs.get(source, [])
        # Chunks built with other chunk settings (or before settings were recorded)
        # are stale even when the source file itself is unchanged.
        fingerprint = chunking_fingerprint()
        metadata_schema_current = not current_chunks or all(
            document.metadata.get("index_schema_version") == INDEX_SCHEMA_VERSION
            and all(document.metadata.get(key) == value for key, value in fingerprint.items())
            for document in current_chunks
        )
        if (
            source_hashes.get(source) == loaded.document_hash
            and source not in legacy_sources
            and metadata_schema_current
        ):
            unchanged_sources.append(source)
            continue

        chunks = split_source(loaded)
        try:
            if chunks:
                logger.info("Indexing source=%s chunks=%d", source, len(chunks))
                store = _vector_store()
                ids = [str(chunk.metadata["chunk_id"]) for chunk in chunks]
                store.add_documents(chunks, ids=ids, batch_size=settings.ingestion_batch_size)
            next_docs[source] = chunks
            source_hashes[source] = loaded.document_hash
            legacy_sources.discard(source)
            updated_sources.append(source)
        except Exception:
            failed_sources.add(source)
            logger.exception("Failed indexing document; preserving previous version: %s", source)

    # Unreadable files retain the prior dense/BM25 version. Missing files are deletions.
    for source in corpus.failed_sources:
        if source in previous_docs:
            next_docs[source] = previous_docs[source]
    for source in deleted_sources:
        next_docs.pop(source, None)
        source_hashes.pop(source, None)
        legacy_sources.discard(source)

    # Keep no stale chunks in the sparse snapshot for sources that have been removed.
    active_sources = set(source_hashes) | legacy_sources
    next_docs = {source: docs for source, docs in next_docs.items() if source in active_sources}
    snapshot = IndexSnapshot(
        documents=[document for docs in next_docs.values() for document in docs],
        source_hashes=source_hashes,
        legacy_sources=legacy_sources,
        generation=current_snapshot.generation + 1,
    )

    # Atomic publication is the consistency boundary: dense results are filtered against
    # this same document_hash map and BM25 is built from these exact chunks.
    write_snapshot(snapshot)
    stale_points = 0
    try:
        stale_points = _remove_stale_points(snapshot)
    except Exception:
        logger.exception("Could not clean superseded Qdrant chunks; active versions remain filtered")

    summary = {
        "knowledge_base": str(settings.knowledge_dir),
        "generation": snapshot.generation,
        "loaded_sources": len(corpus.sources),
        "active_chunks": len(snapshot.documents),
        "updated_sources": updated_sources,
        "unchanged_sources": unchanged_sources,
        "deleted_sources": deleted_sources,
        "failed_sources": sorted(failed_sources),
        "stale_qdrant_points_deleted": stale_points,
        "bm25_snapshot": str(settings.bm25_index_path),
    }
    logger.info("Knowledge Base synchronization complete: %s", summary)
    return summary
