"""Load Markdown files from the configured portfolio Knowledge Base."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document


logger = logging.getLogger("rag_ingestion")


@dataclass(frozen=True)
class LoadedSource:
    source: str
    document_hash: str
    document: Document


@dataclass
class LoadedCorpus:
    sources: dict[str, LoadedSource]
    failed_sources: set[str]
    discovered_sources: set[str]


def load_markdown_documents(knowledge_dir: Path) -> LoadedCorpus:
    """Recursively load Markdown documents, reporting file errors independently."""
    if not knowledge_dir.exists() or not knowledge_dir.is_dir():
        raise FileNotFoundError(f"Knowledge Base directory not found: {knowledge_dir}")

    files = sorted(path for path in knowledge_dir.rglob("*.md") if path.is_file())
    sources: dict[str, LoadedSource] = {}
    failed: set[str] = set()
    discovered: set[str] = set()

    for path in files:
        source = path.relative_to(knowledge_dir).as_posix()
        discovered.add(source)
        try:
            raw = path.read_bytes()
            loaded = TextLoader(str(path), encoding="utf-8", autodetect_encoding=True).load()
            if not loaded:
                raise ValueError("Markdown loader returned no documents")
            content = "\n\n".join(document.page_content for document in loaded).strip()
            file_hash = hashlib.sha256(raw).hexdigest()
            document_id = str(uuid5(NAMESPACE_URL, f"portfolio-kb:{source}"))
            metadata = {
                **loaded[0].metadata,
                "source": source,
                "source_filename": path.name,
                "source_path": str(path.resolve()),
                "file_name": path.name,
                "file_type": path.suffix.lower(),
                "document_id": document_id,
                "document_hash": file_hash,
            }
            if not content:
                logger.warning("Empty Knowledge Base document skipped: %s", source)
            sources[source] = LoadedSource(
                source=source,
                document_hash=file_hash,
                document=Document(page_content=content, metadata=metadata),
            )
        except Exception:
            failed.add(source)
            logger.exception("Could not load Knowledge Base document: %s", source)

    logger.info(
        "Knowledge Base scan complete files=%d loaded=%d failed=%d",
        len(files), len(sources), len(failed),
    )
    return LoadedCorpus(sources=sources, failed_sources=failed, discovered_sources=discovered)
