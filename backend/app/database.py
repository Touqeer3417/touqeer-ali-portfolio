"""Shared connections to the existing Qdrant collection."""

from __future__ import annotations

from functools import lru_cache

from qdrant_client import QdrantClient

from app.config import settings
from app.http_clients import qdrant_http_kwargs


@lru_cache(maxsize=1)
def qdrant_client() -> QdrantClient:
    """Return the cached synchronous client used by ingestion and cleanup."""
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=30,
        **qdrant_http_kwargs(),
    )
