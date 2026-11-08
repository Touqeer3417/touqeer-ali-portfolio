
"""Build a separate dense + BM25 hybrid index in Qdrant."""

import re
from pathlib import Path

from qdrant_client import models
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings
from app.providers import embed_documents
from app.rag import qdrant


KB_DIR = Path(__file__).resolve().parent.parent / "knowledge"
MAX_CHARS = 1100


def clean(text: str) -> str:
    """Remove HTML comments and surrounding whitespace."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()


def pack(section: str) -> list[str]:
    """Split a section into chunks without exceeding MAX_CHARS."""
    if len(section) <= MAX_CHARS:
        return [section]

    chunks: list[str] = []
    buffer = ""

    for paragraph in section.split("\n\n"):
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # Split unusually long paragraphs into smaller pieces.
        if len(paragraph) > MAX_CHARS:
            if buffer:
                chunks.append(buffer.strip())
                buffer = ""

            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            for sentence in sentences:
                if len(sentence) <= MAX_CHARS:
                    if buffer and len(buffer) + len(sentence) + 1 > MAX_CHARS:
                        chunks.append(buffer.strip())
                        buffer = ""
                    buffer += sentence + " "
                else:
                    if buffer:
                        chunks.append(buffer.strip())
                        buffer = ""

                    # Hard split only when a single sentence is too long.
                    for start in range(0, len(sentence), MAX_CHARS):
                        chunks.append(sentence[start:start + MAX_CHARS])

            continue

        if buffer and len(buffer) + len(paragraph) + 2 > MAX_CHARS:
            chunks.append(buffer.strip())
            buffer = ""

        buffer += paragraph + "\n\n"

    if buffer.strip():
        chunks.append(buffer.strip())

    return chunks


def chunk_file(path: Path) -> list[str]:
    """Create heading-aware chunks from a Markdown file."""
    text = clean(path.read_text(encoding="utf-8"))

    if not text:
        return []

    title = text.splitlines()[0].lstrip("# ").strip()
    chunks: list[str] = []

    for section in re.split(r"\n(?=## )", text):
        for piece in pack(section.strip()):
            if piece and not (
                piece.startswith("# ") and "\n" not in piece
            ):
                chunks.append(
                    piece if piece.startswith("# ")
                    else f"{title} - {piece}"
                )

    return chunks


def main() -> None:
    files = sorted(KB_DIR.glob("*.md"))

    if not files:
        raise RuntimeError("No Markdown knowledge files found.")

    # Prepare documents with source and chunk metadata.
    chunks: list[dict] = []

    for file in files:
        file_chunks = chunk_file(file)

        for index, chunk in enumerate(file_chunks):
            chunks.append(
                {
                    "text": chunk,
                    "source": file.name,
                    "chunk_index": index,
                    "total_chunks": len(file_chunks),
                }
            )

    if not chunks:
        raise RuntimeError("No text chunks generated.")

    print(
        f"Generating embeddings for {len(chunks)} chunks "
        f"from {len(files)} files..."
    )

    # Generate dense vectors through LangChain.
    vectors = embed_documents([chunk["text"] for chunk in chunks])

    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding count does not match chunk count.")

    if not vectors or not vectors[0]:
        raise RuntimeError("No valid embeddings generated.")

    client = qdrant()

    # Only rebuild our dedicated hybrid collection.
    # The original portfolio_kb collection remains untouched.
    if client.collection_exists(settings.hybrid_collection):
        print("Replacing existing hybrid collection...")
        client.delete_collection(settings.hybrid_collection)

    print("Creating hybrid collection...")

    client.create_collection(
        collection_name=settings.hybrid_collection,
        vectors_config=VectorParams(
            size=len(vectors[0]),
            distance=Distance.COSINE,
        ),
    )

    # Enable genuine BM25 scoring on the stored text payload.
    print("Creating BM25 full-text index...")

    client.create_payload_index(
        collection_name=settings.hybrid_collection,
        field_name="text",
        field_schema=models.TextIndexParams(
            type=models.TextIndexType.TEXT,
            scoring=True,
        ),
        wait=True,
    )

    print("Uploading documents and dense embeddings...")

    client.upsert(
        collection_name=settings.hybrid_collection,
        wait=True,
        points=[
            PointStruct(
                id=index,
                vector=vector,
                payload=chunk,
            )
            for index, (vector, chunk) in enumerate(
                zip(vectors, chunks)
            )
        ],
    )

    print("\nHybrid indexing successful!")
    print(f"Documents: {len(chunks)} chunks")
    print(f"Source files: {len(files)}")
    print(f"Collection: {settings.hybrid_collection}")
    print("Dense search: Enabled")
    print("BM25 full-text search: Enabled")
    print("RRF: Ready")


if __name__ == "__main__":
    main()
