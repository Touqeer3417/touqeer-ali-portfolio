"""Paths and small constants for the standalone evaluation runner."""

from pathlib import Path


EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_PATH = EVALUATION_DIR / "datasets" / "evaluation_dataset.json"
REPORTS_DIR = EVALUATION_DIR / "reports"
METRIC_NAMES = (
    "answer_correctness",
    "answer_relevancy",
    "faithfulness",
    "context_recall",
    "context_precision",
)

