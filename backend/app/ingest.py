"""Build the vector index from knowledge/*.md."""

import re
from pathlib import Path

from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings
from app.rag import embed, qdrant

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge"
MAX_CHARS = 1100


def clean(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()


def pack(section: str) -> list[str]:
    if len(section) <= MAX_CHARS:
        return [section]

    out, buf = [], ""

    for para in section.split("\n\n"):
        if buf and len(buf) + len(para) > MAX_CHARS:
            out.append(buf.strip())
            buf = ""

        buf += para + "\n\n"

    if buf.strip():
        out.append(buf.strip())

    return out


def chunk_file(path: Path) -> list[str]:
    text = clean(path.read_text(encoding="utf-8"))
    title = text.splitlines()[0].lstrip("# ").strip()

    chunks = []

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

    chunks = [
        {"text": chunk, "source": file.name}
        for file in files
        for chunk in chunk_file(file)
    ]

    if not chunks:
        raise RuntimeError("No text chunks generated from knowledge files.")

    print(f"Generating embeddings for {len(chunks)} chunks from {len(files)} files...")

    vectors = embed([chunk["text"] for chunk in chunks])

    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding count does not match chunk count.")

    client = qdrant()

    if client.collection_exists(settings.collection):
        print("Deleting existing collection...")
        client.delete_collection(settings.collection)

    client.create_collection(
        collection_name=settings.collection,
        vectors_config=VectorParams(
            size=len(vectors[0]),
            distance=Distance.COSINE,
        ),
    )

    client.upsert(
        collection_name=settings.collection,
        wait=True,
        points=[
            PointStruct(
                id=i,
                vector=vector,
                payload=chunk,
            )
            for i, (vector, chunk) in enumerate(zip(vectors, chunks))
        ],
    )

    print(f"Success! Indexed {len(chunks)} chunks from {len(files)} files.")
    print("Collection:", settings.collection)


if __name__ == "__main__":
    main()
