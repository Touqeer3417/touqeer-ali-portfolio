"""HTTP connection settings that keep upstream connections warm between requests.

httpx closes idle keep-alive connections after 5 seconds by default. Any pause
longer than that makes the next request pay a fresh TCP + TLS handshake to
Qdrant or OpenAI. A longer expiry avoids that without changing any payload.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings


logger = logging.getLogger("rag")


def qdrant_http_kwargs() -> dict[str, Any]:
    """Extra QdrantClient kwargs (REST only). Empty when keep-alive tuning is off."""
    expiry = settings.http_keepalive_expiry
    if expiry <= 0:
        return {}
    # Same pool sizes as the httpx defaults; only the idle expiry changes.
    return {
        "limits": httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=expiry,
        )
    }


def openai_http_kwargs() -> dict[str, Any]:
    """`http_client` / `http_async_client` kwargs for the LangChain OpenAI wrappers.

    Uses the OpenAI SDK's own default clients, so timeouts, redirects and
    headers stay exactly as the SDK sets them. Falls back to the SDK defaults
    if the installed SDK does not expose what is needed.
    """
    expiry = settings.http_keepalive_expiry
    if expiry <= 0:
        return {}
    try:
        from openai import DefaultAsyncHttpxClient, DefaultHttpxClient
        from openai._constants import DEFAULT_CONNECTION_LIMITS

        # Build Limits from the SDK's own class so it matches its httpx flavour.
        limits = type(DEFAULT_CONNECTION_LIMITS)(
            max_connections=DEFAULT_CONNECTION_LIMITS.max_connections,
            max_keepalive_connections=DEFAULT_CONNECTION_LIMITS.max_keepalive_connections,
            keepalive_expiry=expiry,
        )
        return {
            "http_client": DefaultHttpxClient(limits=limits),
            "http_async_client": DefaultAsyncHttpxClient(limits=limits),
        }
    except Exception:  # noqa: BLE001 - tuning is optional; never break startup
        logger.warning("keep-alive tuning unavailable for OpenAI clients; using SDK defaults", exc_info=True)
        return {}
