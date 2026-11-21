"""Bounded, thread-safe LRU cache for query embeddings.

Identical questions (the chat widget's starter prompts, repeat visitors) skip
the OpenAI embeddings round trip. Keys include the embedding model name, so a
model change can never serve vectors from the old space.
"""

from __future__ import annotations

import threading
import unicodedata
from collections import OrderedDict

from app.config import settings


_TRAILING_PUNCTUATION = " ?!.,;:\u061f\u061b\u060c"


def normalize_query(text: str) -> str:
    """Cache key for a query: ignores case, spacing and trailing punctuation.

    "How can I contact him?" and "how can i  contact him" share one entry. Only
    cosmetic differences are merged; different words are never treated as equal.
    """
    folded = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(folded.split()).strip(_TRAILING_PUNCTUATION)


class QueryEmbeddingCache:
    def __init__(self, max_size: int) -> None:
        self.max_size = max_size
        self._items: OrderedDict[tuple[str, str], list[float]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, model: str, text: str) -> list[float] | None:
        if self.max_size <= 0:
            return None
        key = (model, normalize_query(text))
        with self._lock:
            vector = self._items.get(key)
            if vector is None:
                return None
            self._items.move_to_end(key)
            return list(vector)  # copy: callers must not mutate the cached vector

    def put(self, model: str, text: str, vector: list[float]) -> None:
        if self.max_size <= 0:
            return
        key = (model, normalize_query(text))
        with self._lock:
            self._items[key] = list(vector)
            self._items.move_to_end(key)
            while len(self._items) > self.max_size:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


query_embedding_cache = QueryEmbeddingCache(settings.embedding_cache_size)
