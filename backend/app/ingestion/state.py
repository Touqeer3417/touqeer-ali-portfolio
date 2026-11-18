"""Persist the shared dense/BM25 corpus snapshot used for synchronization."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from app.config import settings


SCHEMA_VERSION = 1


@dataclass
class IndexSnapshot:
    documents: list[Document]
    source_hashes: dict[str, str]
    legacy_sources: set[str]
    generation: int = 0


def read_snapshot(path: Path | None = None) -> IndexSnapshot | None:
    target = path or settings.bm25_index_path
    if not target.exists():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported BM25 snapshot schema in {target}")
    documents = [
        Document(page_content=row["page_content"], metadata=row.get("metadata", {}))
        for row in payload.get("documents", [])
    ]
    return IndexSnapshot(
        documents=documents,
        source_hashes={str(key): str(value) for key, value in payload.get("source_hashes", {}).items()},
        legacy_sources=set(payload.get("legacy_sources", [])),
        generation=int(payload.get("generation", 0)),
    )


def write_snapshot(snapshot: IndexSnapshot, path: Path | None = None) -> None:
    """Atomically publish the active document version used by both retrievers."""
    target = path or settings.bm25_index_path
    target.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generation": snapshot.generation,
        "source_hashes": snapshot.source_hashes,
        "legacy_sources": sorted(snapshot.legacy_sources),
        "documents": [
            {"page_content": document.page_content, "metadata": document.metadata}
            for document in snapshot.documents
        ],
    }
    fd, temporary_name = tempfile.mkstemp(prefix="bm25-", suffix=".json", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
