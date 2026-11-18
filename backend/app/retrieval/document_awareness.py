"""Resolve explicitly named portfolio projects from indexed chunk metadata."""

from __future__ import annotations

import re
import unicodedata

from langchain_core.documents import Document


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", normalized.casefold()))


def resolve_project(query: str, documents: list[Document]) -> tuple[str, str] | None:
    """Match the longest known project name explicitly mentioned by the query."""
    normalized_query = f" {_normalize(query)} "
    known: dict[str, str] = {}
    for document in documents:
        project_id = document.metadata.get("project_id")
        project_name = document.metadata.get("project_name")
        if isinstance(project_id, str) and isinstance(project_name, str):
            known[project_id] = project_name

    matches = [
        (project_id, name)
        for project_id, name in known.items()
        if f" {_normalize(name)} " in normalized_query
    ]
    if not matches:
        return None
    return max(matches, key=lambda pair: len(_normalize(pair[1])))
