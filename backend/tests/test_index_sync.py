"""Index/config drift detection in ``sync_knowledge_base`` (no Qdrant or OpenAI calls).

Run from ``backend``: ``python -m unittest tests.test_index_sync -v``
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.config import settings
from app.ingestion import sync
from app.ingestion.loader import load_markdown_documents
from app.ingestion.splitter import chunking_fingerprint, split_source
from app.ingestion.state import IndexSnapshot

SAMPLE = "# About\n\n" + "\n\n".join(f"Paragraph {i}. " + "word " * 60 for i in range(12))


class IndexSyncDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.kb = Path(self._tmp.name)
        (self.kb / "about.md").write_text(SAMPLE, encoding="utf-8")
        self.corpus = load_markdown_documents(self.kb)
        self.loaded = self.corpus.sources["about.md"]

    def _run_sync(self, snapshot: IndexSnapshot):
        store = MagicMock()
        written: list[IndexSnapshot] = []
        with patch.object(sync, "_ensure_collection"), \
             patch.object(sync, "_vector_store", return_value=store), \
             patch.object(sync, "load_markdown_documents", return_value=self.corpus), \
             patch.object(sync, "read_snapshot", return_value=snapshot), \
             patch.object(sync, "write_snapshot", side_effect=written.append), \
             patch.object(sync, "_remove_stale_points", return_value=0):
            summary = sync.sync_knowledge_base()
        return summary, store, written

    def _snapshot(self, chunks):
        return IndexSnapshot(
            documents=chunks,
            source_hashes={"about.md": self.loaded.document_hash},
            legacy_sources=set(),
            generation=3,
        )

    def test_chunks_record_their_chunking_settings(self) -> None:
        for chunk in split_source(self.loaded):
            self.assertEqual(chunk.metadata["chunk_size"], settings.chunk_size)
            self.assertEqual(chunk.metadata["chunk_overlap"], settings.chunk_overlap)

    def test_matching_index_is_left_untouched(self) -> None:
        summary, store, _ = self._run_sync(self._snapshot(split_source(self.loaded)))
        self.assertEqual(summary["unchanged_sources"], ["about.md"])
        self.assertEqual(summary["updated_sources"], [])
        store.add_documents.assert_not_called()

    def test_index_built_with_other_chunk_size_is_reindexed(self) -> None:
        with patch.object(settings, "chunk_size", 1100), patch.object(settings, "chunk_overlap", 100):
            old_chunks = split_source(self.loaded)
        self.assertNotEqual(chunking_fingerprint(), old_chunks[0].metadata and {
            "chunk_size": old_chunks[0].metadata["chunk_size"],
            "chunk_overlap": old_chunks[0].metadata["chunk_overlap"],
        })
        summary, store, written = self._run_sync(self._snapshot(old_chunks))
        self.assertEqual(summary["updated_sources"], ["about.md"])
        store.add_documents.assert_called_once()
        new_chunks = written[-1].documents
        self.assertTrue(all(c.metadata["chunk_size"] == settings.chunk_size for c in new_chunks))
        self.assertEqual(written[-1].generation, 4)

    def test_legacy_index_without_recorded_settings_is_reindexed_once(self) -> None:
        legacy = split_source(self.loaded)
        for chunk in legacy:
            chunk.metadata.pop("chunk_size")
            chunk.metadata.pop("chunk_overlap")
        summary, store, _ = self._run_sync(self._snapshot(legacy))
        self.assertEqual(summary["updated_sources"], ["about.md"])
        store.add_documents.assert_called_once()


if __name__ == "__main__":
    unittest.main()
