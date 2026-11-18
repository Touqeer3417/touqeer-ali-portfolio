"""Load and validate question/reference cases for RAGAS."""

from __future__ import annotations

import json
from dataclasses import dataclass

from evaluation.config import DATASET_PATH


@dataclass(frozen=True)
class EvaluationCase:
    """One independently verified question and its ground-truth answer."""

    case_id: str
    user_input: str
    reference: str | None


def load_dataset(path=DATASET_PATH) -> list[EvaluationCase]:
    """Read cases without synthesizing or changing their references."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"Evaluation dataset must be a non-empty JSON list: {path}")

    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Dataset row {index} must be a JSON object")
        case_id = row.get("id")
        question = row.get("user_input")
        reference = row.get("reference")
        if not all(isinstance(value, str) and value.strip() for value in (case_id, question)):
            raise ValueError(f"Dataset row {index} requires non-empty id and user_input")
        if reference is not None and not isinstance(reference, str):
            raise ValueError(f"Dataset row {index} reference must be a string or null")
        if case_id in seen_ids:
            raise ValueError(f"Duplicate evaluation case id: {case_id}")
        seen_ids.add(case_id)
        cases.append(
            EvaluationCase(
                case_id,
                question.strip(),
                reference.strip() if reference and reference.strip() else None,
            )
        )
    return cases
