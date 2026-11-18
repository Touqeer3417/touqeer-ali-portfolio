"""Request-local retrieval trace access for evaluation and diagnostics."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any


_retrieval_trace: ContextVar[dict[str, Any] | None] = ContextVar(
    "portfolio_retrieval_trace", default=None
)


def set_retrieval_trace(trace: dict[str, Any] | None) -> None:
    """Set trace only in the current request/task context."""
    _retrieval_trace.set(trace)


def get_retrieval_trace() -> dict[str, Any] | None:
    """Return this request's trace without sharing data across concurrent calls."""
    return _retrieval_trace.get()
