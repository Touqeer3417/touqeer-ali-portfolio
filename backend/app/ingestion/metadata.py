"""Document/project metadata extraction for Markdown knowledge sources."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


PROJECT_HEADING = re.compile(r"(?m)^#\s+\d+\.\s+(.+?)\s*$")
MARKDOWN_HEADING = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class ContentSegment:
    """A contiguous source range belonging to one project, if applicable."""

    start: int
    end: int
    project_id: str | None = None
    project_name: str | None = None


def _clean_project_title(title: str) -> str:
    title = re.sub(r"^\d+\.\s*", "", title).strip().rstrip(" –—-").strip()
    return re.split(r"\s+[–—-]\s+", title, maxsplit=1)[0].strip()


def project_slug(name: str) -> str:
    """Create a stable, query-matchable ID from a Markdown project heading."""
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


def content_segments(content: str) -> list[ContentSegment]:
    """Split numbered project documents into project-preserving ranges."""
    matches = list(PROJECT_HEADING.finditer(content))
    if not matches:
        return [ContentSegment(0, len(content))]

    segments: list[ContentSegment] = []
    if content[: matches[0].start()].strip():
        segments.append(ContentSegment(0, matches[0].start()))
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        name = _clean_project_title(match.group(1))
        segments.append(ContentSegment(start, end, project_slug(name), name))
    return segments


def section_heading(content: str, offset: int, project_name: str | None = None) -> str | None:
    """Return the nearest heading at or before a chunk's source offset."""
    previous = None
    for match in MARKDOWN_HEADING.finditer(content):
        if match.start() > offset:
            break
        heading = match.group(2).strip()
        if len(match.group(1)) == 1 and PROJECT_HEADING.match(match.group(0)):
            heading = project_name or _clean_project_title(heading)
        previous = heading
    return previous
