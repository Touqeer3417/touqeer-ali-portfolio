"""Command-line entry point for incremental Knowledge Base synchronization."""

from __future__ import annotations

import logging

from app.ingestion.sync import sync_knowledge_base


def main() -> None:
    """Synchronize Markdown sources into the existing dense and BM25 indexes."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    print("Starting Knowledge Base synchronization...", flush=True)
    summary = sync_knowledge_base()
    print("Knowledge Base synchronization complete")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
