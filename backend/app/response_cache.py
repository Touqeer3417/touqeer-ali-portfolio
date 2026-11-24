"""Bounded, TTL-aware cache for complete chatbot answers.

The widget's starter questions and the handful of things every visitor asks
("What are your skills?", "Tell me about your projects.") are answered from
memory, skipping retrieval and the LLM call entirely.

Only a visitor's *first* turn is cached. Once a conversation has history the
answer depends on conversation state - the project scope carried over by
``retrieval.document_awareness`` and the history placed in the prompt - so
reusing a stored answer could answer a different question than the one asked.
``app.rag.cacheable_question`` enforces that.

Keys combine the chat model, a knowledge-base fingerprint and the normalized
question. The cache lives in the process, so a code or settings change is
cleared by the restart that deploys it; the knowledge base is the only input
that can change under a running server, and the fingerprint covers it.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from time import monotonic
from typing import Callable, Iterator

from app.config import settings
from app.embedding_cache import normalize_query


# (chat model, knowledge-base fingerprint, normalized question)
CacheKey = tuple[str, str, str]


def knowledge_base_version() -> str:
    """Fingerprint the active corpus cheaply: one ``stat()``, no parse, no network.

    ``ingestion.sync`` republishes the BM25 snapshot atomically (``os.replace``)
    for every generation, so its mtime and size change whenever the knowledge
    base is re-indexed. Putting this in the key retires every answer built from
    the previous corpus without reading the file - and without the Qdrant
    bootstrap that ``BM25Index.snapshot()`` can trigger on a missing snapshot.
    """
    try:
        stat = settings.bm25_index_path.stat()
    except OSError:
        return "absent"
    return f"{stat.st_mtime_ns}-{stat.st_size}"


def cache_key(question: str) -> CacheKey:
    """Build the lookup key for a first-turn question.

    Case, spacing and trailing punctuation are normalized by
    ``embedding_cache.normalize_query``, so "What are your skills?" and
    "what are  your skills" share one entry while different words never do.
    """
    return (settings.chat_model, knowledge_base_version(), normalize_query(question))


class ResponseCache:
    """Thread-safe LRU of answers with a per-entry time-to-live.

    Disabled when ``max_size`` or ``ttl_seconds`` is zero, in which case every
    lookup misses and nothing is stored.
    """

    def __init__(
        self,
        max_size: int,
        ttl_seconds: float,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        # Monotonic by default: a TTL must not be affected by system clock changes.
        self._clock = clock
        self._items: OrderedDict[CacheKey, tuple[float, str]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._stores = 0
        self._evictions = 0
        self._expirations = 0

    @property
    def enabled(self) -> bool:
        return self.max_size > 0 and self.ttl_seconds > 0

    def get(self, key: CacheKey) -> str | None:
        """Return a live cached answer, or None on a miss or an expired entry."""
        if not self.enabled:
            return None
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                self._misses += 1
                return None
            stored_at, answer = entry
            if self._clock() - stored_at >= self.ttl_seconds:
                del self._items[key]
                self._expirations += 1
                self._misses += 1
                return None
            self._items.move_to_end(key)
            self._hits += 1
            return answer

    def put(self, key: CacheKey, answer: str) -> None:
        """Store a completed answer. Blank answers are never stored."""
        if not self.enabled or not answer.strip():
            return
        with self._lock:
            # str is immutable, so the stored value needs no defensive copy.
            self._items[key] = (self._clock(), answer)
            self._items.move_to_end(key)
            self._stores += 1
            while len(self._items) > self.max_size:
                self._items.popitem(last=False)
                self._evictions += 1

    def clear(self) -> None:
        """Drop every entry, keeping the counters so metrics survive a flush."""
        with self._lock:
            self._items.clear()

    def reset_stats(self) -> None:
        with self._lock:
            self._hits = self._misses = self._stores = 0
            self._evictions = self._expirations = 0

    def stats(self) -> dict[str, object]:
        """Counters for the in-process window since start-up (or last reset)."""
        with self._lock:
            lookups = self._hits + self._misses
            return {
                "enabled": self.enabled,
                "entries": len(self._items),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / lookups, 4) if lookups else None,
                "stores": self._stores,
                "evictions": self._evictions,
                "expirations": self._expirations,
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


_bypass: ContextVar[bool] = ContextVar("response_cache_bypass", default=False)


@contextmanager
def bypass_response_cache() -> Iterator[None]:
    """Neither read nor write the cache inside the enclosing block.

    Used by the evaluation adapter so RAGAS scores and the latency benchmark
    always measure a real retrieval and generation run, even when a dataset
    repeats a question. Follows the same context-variable pattern as
    ``latency.use_request_id`` and ``document_awareness.set_earlier_user_turns``,
    which keeps ``stream_answer(messages)`` unchanged.
    """
    token = _bypass.set(True)
    try:
        yield
    finally:
        _bypass.reset(token)


def cache_bypassed() -> bool:
    return _bypass.get()


response_cache = ResponseCache(
    settings.response_cache_size,
    settings.response_cache_ttl_seconds,
)
