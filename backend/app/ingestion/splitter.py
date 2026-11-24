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


def chunking_fingerprint() -> dict[str, int | bool]:
    """Chunking settings an indexed chunk was built with (stored in chunk metadata)."""
    return {
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "min_chunk_chars": settings.min_chunk_chars,
        "chunk_context_prefix": settings.chunk_context_prefix,
    }


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


def context_prefix(source_filename: str | None, project_name: str | None, section: str | None) -> str:
    """Human-readable location line stored at the top of a chunk (BM25 and embeddings see it)."""
    parts = []
    if source_filename:
        parts.append(f"Source: {source_filename.rsplit('.', 1)[0]}")
    if project_name:
        parts.append(f"Project: {project_name}")
    if section:
        parts.append(f"Section: {section}")
    return f"[{' | '.join(parts)}]\n" if parts else ""


def absorb_small_chunks(chunks: list[Document], min_chars: int) -> list[Document]:
    """Remove chunks too small to be useful retrieval units.

    A tiny chunk already contained in its neighbour (the splitter's overlap) is
    dropped; otherwise it is merged into the neighbour. A lone tiny chunk that is
    only Markdown headings carries no facts and is dropped.
    """
    if min_chars <= 0:
        return chunks
    result = list(chunks)
    i = 0
    while i < len(result):
        chunk = result[i]
        text = chunk.page_content.strip()
        if len(text) >= min_chars:
            i += 1
            continue
        if len(result) == 1:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if all(line.startswith("#") for line in lines):
                result.pop(i)
            else:
                i += 1
            continue
        following = i + 1 < len(result)
        neighbour = result[i + 1] if following else result[i - 1]
        if text not in neighbour.page_content:
            if following:
                neighbour.page_content = f"{text}\n\n{neighbour.page_content}"
                if "start_index" in chunk.metadata:
                    neighbour.metadata["start_index"] = chunk.metadata["start_index"]
            else:
                neighbour.page_content = f"{neighbour.page_content}\n\n{text}"
        result.pop(i)
    return result


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
        chunks = absorb_small_chunks(
            splitter.split_documents([segment_document]), settings.min_chunk_chars
        )
        chunked_segments.append((segment, segment_text, chunks))

    total_chunks = sum(len(chunks) for _, _, chunks in chunked_segments)
    chunk_index = 0
    for segment, segment_text, chunks in chunked_segments:
        for chunk in chunks:
            local_start = int(chunk.metadata.get("start_index", 0))
            absolute_start = segment.start + local_start
            source_filename = source.document.metadata.get("source_filename") or source.document.metadata.get("file_name")
            heading = section_heading(segment_text, local_start, segment.project_name)
            text = chunk.page_content
            if settings.chunk_context_prefix:
                text = context_prefix(source_filename, segment.project_name, heading) + text
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            metadata = {
                **chunk.metadata,
                "source_filename": source_filename,
                "section_heading": heading,
                "index_schema_version": INDEX_SCHEMA_VERSION,
                **chunking_fingerprint(),
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
            output.append(Document(page_content=text, metadata=metadata))
            chunk_index += 1
    return output


def split_corpus(sources: dict[str, LoadedSource]) -> dict[str, list[Document]]:
    """Return source-grouped chunks, keeping failed sources out of the index update."""
    return {name: split_source(source) for name, source in sources.items()}
