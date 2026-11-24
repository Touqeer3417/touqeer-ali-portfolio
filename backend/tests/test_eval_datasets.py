"""Evaluation datasets: the extended set only appends; references stay grounded.

Run from ``backend``: ``python -m unittest tests.test_eval_datasets -v``
"""

from __future__ import annotations

import json
import re
import unittest

from app.config import settings
from evaluation.config import DATASET_PATH
from evaluation.dataset import load_dataset

EXTENDED = DATASET_PATH.with_name("evaluation_dataset_extended.json")


class ExtendedDatasetTests(unittest.TestCase):
    def test_original_cases_are_untouched_and_first(self) -> None:
        original = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
        extended = json.loads(EXTENDED.read_text(encoding="utf-8"))
        self.assertEqual(extended[: len(original)], original)
        self.assertGreater(len(extended), len(original))

    def test_extended_dataset_loads_with_unique_ids(self) -> None:
        cases = load_dataset(EXTENDED)
        self.assertEqual(len({c.case_id for c in cases}), len(cases))
        self.assertTrue(all(c.reference for c in cases))

    def test_urls_and_emails_in_references_exist_in_the_knowledge_base(self) -> None:
        kb = "\n".join(p.read_text(encoding="utf-8") for p in settings.knowledge_dir.glob("*.md"))
        for case in load_dataset(EXTENDED):
            for token in re.findall(r"https?://[^\s,]+|[\w.]+@[\w.]+\w", case.reference):
                token = token.rstrip(".")
                self.assertIn(token.rstrip("/"), kb, f"{case.case_id}: {token}")

    def test_service_list_reference_matches_the_knowledge_base_count(self) -> None:
        services = (settings.knowledge_dir / "services.md").read_text(encoding="utf-8")
        numbered = re.findall(r"(?m)^## \d+\. ", services)
        case = next(c for c in load_dataset(EXTENDED) if c.case_id == "services_full_list")
        self.assertEqual(len(numbered), 10)
        self.assertIn("ten services", case.reference)


if __name__ == "__main__":
    unittest.main()
