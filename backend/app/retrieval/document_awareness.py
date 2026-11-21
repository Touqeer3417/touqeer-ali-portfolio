"""Resolve explicitly named portfolio projects from indexed chunk metadata."""

from __future__ import annotations

import re
import unicodedata
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Sequence

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


# --------------------------------------------------------------------------
# Multi-turn scope decision
#
# A project named in an EARLIER turn must not become a hard filter for a later,
# unrelated question: contact, services, skills and profile chunks carry no
# ``project_id`` and a project filter excludes them. The decision below is pure
# string logic (no I/O, no LLM call) over the current question, the earlier user
# turns and the indexed project names.
# --------------------------------------------------------------------------

# Questions about Touqeer himself / the site, not about one project.
_GLOBAL_TOPIC = re.compile(
    r"\b(contact|e ?mail|linkedin|phone|whatsapp|get in touch|reach|hire|hiring|freelance|"
    r"services?|pricing|price|prices|cost|rates?|charges?|skills?|experience|education|"
    r"university|degree|semester|languages?|location|background|about him|who is|"
    r"hobbies|interests?|qualifications?|rabta|raabta|qeemat|taleem)\b"
)
# Words that point back at a project from an earlier turn ("it", "this project").
_PROJECT_ANAPHORA = re.compile(
    r"\b(it|its|itself|this project|that project|the project|this one|that one|this app|"
    r"this system|this assistant|this chatbot|this tool|iska|iski|isme)\b"
)
# Project-detail vocabulary; only counts for SHORT questions that do not mention him.
_PROJECT_DETAIL = re.compile(
    r"\b(stack|technolog(?:y|ies)|tech|architecture|features?|limitations?|challenges?|"
    r"deployment|deployed|demo|repository|repo|github|results?|accuracy|implementation|"
    r"database|frameworks?|libraries|pipeline|workflow|approach|status)\b"
)
_PERSON = re.compile(r"\b(he|his|him|touqeer|touqir)\b")
_CONTINUATION = re.compile(
    r"^(tell me more|more details?|more about (it|that|this)|go on|elaborate|explain more|"
    r"continue|aur batao|mazeed)\b"
)
_BARE_DETAIL_MAX_WORDS = 8


@dataclass(frozen=True)
class ScopePlan:
    """Which query text to search with and whether to hard-filter to one project."""

    query: str
    project: tuple[str, str] | None
    reason: str


_earlier_user_turns: ContextVar[tuple[str, ...]] = ContextVar(
    "portfolio_earlier_user_turns", default=()
)


def set_earlier_user_turns(turns: Sequence[str]) -> Token:
    """Make the earlier user turns visible to the retriever for this request only."""
    return _earlier_user_turns.set(tuple(turns))


def reset_earlier_user_turns(token: Token) -> None:
    try:
        _earlier_user_turns.reset(token)
    except ValueError:  # token created in another context: just clear the value here
        _earlier_user_turns.set(())


def get_earlier_user_turns() -> tuple[str, ...]:
    return _earlier_user_turns.get()


def _last_project(turns: Sequence[str], documents: list[Document]) -> tuple[str, str] | None:
    """Most recent project named in earlier user turns (newest first)."""
    for turn in reversed(turns):
        project = resolve_project(turn, documents)
        if project:
            return project
    return None


def plan_scope(current: str, earlier: Sequence[str], documents: list[Document]) -> ScopePlan:
    """Decide the retrieval query and project scope for the CURRENT question.

    Order of rules (first match wins):
      1. current question names a project            -> scope to it (handles switching)
      2. refers back to a project AND asks a global
         topic ("hire him for something like it")    -> no filter, project name as soft context
      3. refers back to a project ("it", "this project") -> scope to the earlier project
      4. global topic (contact/services/skills/...)   -> no filter, current question only
         (only when an earlier turn named a project; otherwise the legacy joined query)
      5. short bare project-detail question
         ("And the architecture?")                    -> scope to the earlier project
      6. bare continuation ("tell me more") right after a project turn -> scope to it
      7. anything else                                -> legacy behaviour: last two user turns, no filter
    With no earlier turns this reduces to the single-turn behaviour.
    """
    normalized = _normalize(current)
    legacy_query = " ".join([*earlier[-1:], current]) if earlier else current

    named = resolve_project(current, documents)
    if named:
        return ScopePlan(current, named, "named_in_question")

    previous = _last_project(earlier, documents)
    is_global = bool(_GLOBAL_TOPIC.search(normalized))
    refers_back = bool(_PROJECT_ANAPHORA.search(normalized))

    if previous and refers_back and is_global:
        return ScopePlan(f"{previous[1]}: {current}", None, "mixed_soft_context")
    if previous and refers_back:
        return ScopePlan(f"{previous[1]}: {current}", previous, "carried_by_reference")
    if is_global:
        return ScopePlan(current if previous else legacy_query, None, "global_topic")
    if (
        previous
        and _PROJECT_DETAIL.search(normalized)
        and not _PERSON.search(normalized)
        and len(normalized.split()) <= _BARE_DETAIL_MAX_WORDS
    ):
        return ScopePlan(f"{previous[1]}: {current}", previous, "carried_bare_detail")
    if earlier and _CONTINUATION.search(normalized):
        immediate = resolve_project(earlier[-1], documents)
        if immediate:
            return ScopePlan(legacy_query, immediate, "carried_continuation")
    return ScopePlan(legacy_query, None, "unscoped")
