"""Chunk loaded Markdown documents while retaining source metadata."""

from __future__ import annotations

import hashlib
from uuid import UUID, uuid5

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.ingestion.loader import LoadedSource
from app.ingestion.metadata import ContentSegment, content_segments, section_heading


INDEX_SCHEMA_VERSION = 2


def make_splitter() -> RecursiveCharacterTextSplitter:
    """Create the configured recursive character splitter."""
    if settings.chunk_overlap >= settings.chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
        separators=["\n\n", "\n", " ", ""],
    )


def split_source(source: LoadedSource) -> list[Document]:
    """Split one source into deterministic chunks for dense and sparse indexes."""
    if not source.document.page_content.strip():
        return []

    output: list[Document] = []
    document_id = source.document.metadata["document_id"]
    content = source.document.page_content
    splitter = make_splitter()
    segments = content_segments(content)
    chunked_segments: list[tuple[ContentSegment, str, list[Document]]] = []

    for segment in segments:
        segment_text = content[segment.start : segment.end]
        segment_document = Document(
            page_content=segment_text,
            metadata={
                **source.document.metadata,
                **({
                    "project_id": segment.project_id,
                    "project_name": segment.project_name,
                } if segment.project_id else {}),
            },
        )
        chunks = splitter.split_documents([segment_document])
        chunked_segments.append((segment, segment_text, chunks))

    total_chunks = sum(len(chunks) for _, _, chunks in chunked_segments)
    chunk_index = 0
    for segment, segment_text, chunks in chunked_segments:
        for chunk in chunks:
            local_start = int(chunk.metadata.get("start_index", 0))
            absolute_start = segment.start + local_start
            content_hash = hashlib.sha256(chunk.page_content.encode("utf-8")).hexdigest()
            metadata = {
                **chunk.metadata,
                "source_filename": source.document.metadata.get("source_filename")
                or source.document.metadata.get("file_name"),
                "section_heading": section_heading(
                    segment_text, local_start, segment.project_name
                ),
                "index_schema_version": INDEX_SCHEMA_VERSION,
                "chunk_id": str(
                    uuid5(
                        UUID(document_id),
                        f"{source.document_hash}:{chunk_index}:{content_hash}",
                    )
                ),
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "start_index": absolute_start,
            }
            output.append(Document(page_content=chunk.page_content, metadata=metadata))
            chunk_index += 1
    return output


def split_corpus(sources: dict[str, LoadedSource]) -> dict[str, list[Document]]:
    """Return source-grouped chunks, keeping failed sources out of the index update."""
    return {name: split_source(source) for name, source in sources.items()}
