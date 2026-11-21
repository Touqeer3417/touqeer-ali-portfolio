"""Read-only network profile of the three remote calls in a RAG request.

Run from the backend folder (same venv as the app):

    python profile_network.py            # default: 5 warm calls, 8 s idle test
    python profile_network.py --idle 12

It changes nothing: it only times calls made with the app's own clients and
settings. It prints host names only, never keys. Each row shows the first call
(cold: DNS + TCP + TLS) and the warm calls that follow, then the same call
after an idle gap longer than httpx's default 5 s keep-alive expiry.
"""

from __future__ import annotations

import argparse
import socket
import statistics
import time
from collections.abc import Callable
from urllib.parse import urlparse

import httpx
from qdrant_client import QdrantClient

from app.config import settings
from app.database import qdrant_client
from app.providers import get_chat_model, get_embeddings

PROBE_TEXT = "What has Touqeer built?"


def _ms(fn: Callable[[], object]) -> float:
    started = time.perf_counter()
    fn()
    return (time.perf_counter() - started) * 1000


def _row(label: str, first: float, warm: list[float], after_idle: float | None = None) -> None:
    idle = f"{after_idle:8.0f}" if after_idle is not None else "       -"
    print(
        f"{label:34} first={first:7.0f}  warm p50={statistics.median(warm):6.0f} "
        f"min={min(warm):6.0f} max={max(warm):6.0f}  after_idle={idle}"
    )


def _profile(label: str, fn: Callable[[], object], warm_n: int, idle_s: float) -> None:
    first = _ms(fn)
    warm = [_ms(fn) for _ in range(warm_n)]
    time.sleep(idle_s)
    _row(label, first, warm, _ms(fn))


def _tcp_rtt(label: str, host: str, port: int, n: int) -> None:
    samples = []
    for _ in range(n):
        started = time.perf_counter()
        with socket.create_connection((host, port), timeout=10):
            pass
        samples.append((time.perf_counter() - started) * 1000)
    print(f"{label:34} TCP connect p50={statistics.median(samples):6.0f} min={min(samples):6.0f} max={max(samples):6.0f}  ({host}:{port})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warm", type=int, default=5, help="warm calls per row")
    parser.add_argument("--idle", type=float, default=8.0, help="seconds idle before the after_idle call")
    args = parser.parse_args()

    qurl = urlparse(settings.qdrant_url)
    qhost = qurl.hostname or ""
    qport = qurl.port or (443 if qurl.scheme == "https" else 6333)
    print(f"Qdrant host: {qhost}  collection: {settings.hybrid_collection}")
    print("All values in milliseconds.\n")

    print("--- pure network round trip (lower bound for any call)")
    _tcp_rtt("Qdrant", qhost, qport, args.warm)
    _tcp_rtt("OpenAI api.openai.com", "api.openai.com", 443, args.warm)

    print("\n--- app clients as configured today")
    client = qdrant_client()
    _profile("qdrant collection_exists (REST)", lambda: client.collection_exists(settings.hybrid_collection), args.warm, args.idle)

    embeddings = get_embeddings()
    vector = embeddings.embed_query(PROBE_TEXT)
    _profile("openai embed_query", lambda: embeddings.embed_query(PROBE_TEXT), args.warm, args.idle)

    def search(c: QdrantClient = client) -> object:
        return c.query_points(
            collection_name=settings.hybrid_collection,
            query=vector,
            limit=settings.dense_top_k,
            with_payload=True,
        )

    _profile("qdrant query_points (REST)", search, args.warm, args.idle)

    chat = get_chat_model().bind(max_tokens=5)

    def first_token() -> None:
        for _ in chat.stream("Reply with one word: ok"):
            break

    _profile("openai chat time-to-first-token", first_token, 3, args.idle)

    print("\n--- experiments (not used by the app)")
    longlived = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=30,
        limits=httpx.Limits(keepalive_expiry=60.0),
    )
    longlived.collection_exists(settings.hybrid_collection)  # open the connection
    _profile("qdrant REST, keepalive_expiry=60", lambda: longlived.query_points(
        collection_name=settings.hybrid_collection, query=vector, limit=settings.dense_top_k, with_payload=True
    ), args.warm, args.idle)

    try:
        grpc = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, prefer_grpc=True, timeout=30)
        grpc.collection_exists(settings.hybrid_collection)
        _profile("qdrant gRPC query_points", lambda: grpc.query_points(
            collection_name=settings.hybrid_collection, query=vector, limit=settings.dense_top_k, with_payload=True
        ), args.warm, args.idle)
    except Exception as exc:  # gRPC port may be blocked; that is itself a result
        print(f"qdrant gRPC unavailable: {type(exc).__name__}: {str(exc)[:120]}")


if __name__ == "__main__":
    main()
