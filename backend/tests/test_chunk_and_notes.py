"""Small-chunk absorption and project-scoped notes (no Qdrant/OpenAI calls).

Run from ``backend``: ``python -m unittest tests.test_chunk_and_notes -v``
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from langchain_core.documents import Document

from app.config import settings
from app.ingestion.loader import load_markdown_documents
from app.ingestion.splitter import absorb_small_chunks, split_source
from app.rag import _context_notes


def doc(text: str, **metadata) -> Document:
    return Document(page_content=text, metadata=metadata)


class AbsorbSmallChunksTests(unittest.TestCase):
    def test_lone_heading_only_chunk_is_dropped(self) -> None:
        self.assertEqual(absorb_small_chunks([doc("# Projects – Touqeer Ali")], 100), [])

    def test_lone_small_chunk_with_facts_is_kept(self) -> None:
        chunks = absorb_small_chunks([doc("Email: a@b.c")], 100)
        self.assertEqual([c.page_content for c in chunks], ["Email: a@b.c"])

    def test_tiny_chunk_already_inside_neighbour_is_dropped(self) -> None:
        big = doc("x" * 200 + "\n\nShort tail.", start_index=0)
        out = absorb_small_chunks([doc("Short tail."), big], 100)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].page_content, big.page_content)

    def test_tiny_chunk_is_merged_forward_with_its_start_index(self) -> None:
        out = absorb_small_chunks(
            [doc("Title line", start_index=5), doc("y" * 150, start_index=40)], 100
        )
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].page_content.startswith("Title line\n\n"))
        self.assertEqual(out[0].metadata["start_index"], 5)

    def test_trailing_tiny_chunk_is_merged_backward(self) -> None:
        out = absorb_small_chunks([doc("y" * 150), doc("The end")], 100)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].page_content.endswith("\n\nThe end"))

    def test_disabled_when_zero(self) -> None:
        chunks = [doc("tiny"), doc("also tiny")]
        self.assertEqual(absorb_small_chunks(chunks, 0), chunks)

    def test_real_knowledge_base_has_no_tiny_chunks_and_nothing_is_lost(self) -> None:
        corpus = load_markdown_documents(settings.knowledge_dir)
        for name, loaded in corpus.sources.items():
            with patch.object(settings, "chunk_context_prefix", False):
                with patch.object(settings, "min_chunk_chars", 0):
                    before = split_source(loaded)
                after = split_source(loaded)
            self.assertTrue(all(len(c.page_content) >= 100 for c in after), name)
            lost = [
                c.page_content for c in before
                if not any(c.page_content.strip() in a.page_content for a in after)
            ]
            # Only heading-only chunks may disappear.
            for text in lost:
                self.assertTrue(all(l.strip().startswith("#") for l in text.splitlines() if l.strip()), text)
            self.assertEqual([c.metadata["total_chunks"] for c in after[:1]], [len(after)] if after else [])


class ContextPrefixTests(unittest.TestCase):
    def _chunks(self, name: str):
        loaded = load_markdown_documents(settings.knowledge_dir).sources[name]
        return split_source(loaded)

    def test_every_chunk_starts_with_its_location_line(self) -> None:
        for chunk in self._chunks("services.md"):
            self.assertTrue(chunk.page_content.startswith("[Source: services | "), chunk.page_content[:60])
        legal = next(c for c in self._chunks("services.md") if "Legal Document AI Assistants" in c.page_content)
        self.assertIn("Section: 6. Legal Document AI Assistants", legal.page_content.splitlines()[0])

    def test_project_chunks_name_their_project(self) -> None:
        for chunk in self._chunks("projects.md"):
            self.assertIn("| Project: ", chunk.page_content.splitlines()[0])

    def test_prefix_can_be_disabled_and_changes_chunk_ids(self) -> None:
        with_prefix = self._chunks("contact.md")
        with patch.object(settings, "chunk_context_prefix", False):
            without = self._chunks("contact.md")
        self.assertFalse(without[0].page_content.startswith("[Source:"))
        self.assertNotEqual({c.metadata["chunk_id"] for c in with_prefix}, {c.metadata["chunk_id"] for c in without})


class ContextNotesScopeTests(unittest.TestCase):
    LIFEOPS = doc(
        "Stack.\n\nNote: This description documents the known architecture.",
        project_name="LifeOps AI", source_filename="projects.md",
    )
    GLOBAL = doc("Intro.\n\nNote: Prices are discussed individually.", source_filename="services.md")

    def test_note_from_unrelated_project_is_not_attached(self) -> None:
        notes = _context_notes([self.LIFEOPS, self.GLOBAL], "What services does Touqeer offer?\nHe offers RAG.")
        self.assertEqual([n for n, _ in notes], ["Prices are discussed individually."])

    def test_note_kept_when_project_is_in_the_question(self) -> None:
        notes = _context_notes([self.LIFEOPS], "Tell me about LifeOps AI\nIt uses React.")
        self.assertEqual(len(notes), 1)

    def test_legacy_call_without_relevant_text_keeps_all_notes(self) -> None:
        self.assertEqual(len(_context_notes([self.LIFEOPS, self.GLOBAL])), 2)


if __name__ == "__main__":
    unittest.main()
