"""In-memory cache for LLM answers keyed by question + retrieved chunks."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.config import get_settings


class LLMCache:
    _store: dict[str, dict[str, Any]]

    def __init__(self, ttl_seconds: int | None = None, max_size: int | None = None) -> None:
        settings = get_settings()
        self.ttl_seconds = int(
            ttl_seconds
            if ttl_seconds is not None
            else getattr(settings, "llm_cache_ttl_seconds", 3600)
        )
        self.max_size = int(
            max_size if max_size is not None else getattr(settings, "llm_cache_max_size", 500)
        )
        self._store = {}
        self.hits = 0
        self.misses = 0

    def _make_key(self, question: str, context_chunks: list[dict]) -> str:
        normalized_question = (question or "").strip().lower()
        chunk_tokens: list[str] = []
        for chunk in context_chunks[:5]:
            chunk_id = chunk.get("id")
            if chunk_id is None:
                chunk_id = chunk.get("_id")
            if chunk_id is None:
                chunk_id = chunk.get("text", "")
            chunk_tokens.append(str(chunk_id))
        chunks_hash = hashlib.sha256("||".join(chunk_tokens).encode("utf-8")).hexdigest()
        return f"{normalized_question}::{chunks_hash}"

    def get(self, question: str, context_chunks: list[dict]) -> str | None:
        key = self._make_key(question, context_chunks)
        entry = self._store.get(key)
        if not entry:
            self.misses += 1
            return None

        now = time.time()
        if now - float(entry.get("timestamp", 0.0)) > self.ttl_seconds:
            self._store.pop(key, None)
            self.misses += 1
            return None

        self.hits += 1
        return str(entry.get("answer", ""))

    def _evict_oldest(self) -> None:
        if len(self._store) <= self.max_size:
            return
        # Evict oldest 20% when we cross capacity.
        to_evict = max(1, int(self.max_size * 0.2))
        ordered = sorted(self._store.items(), key=lambda kv: float(kv[1].get("timestamp", 0.0)))
        for key, _ in ordered[:to_evict]:
            self._store.pop(key, None)

    def set(self, question: str, context_chunks: list[dict], answer: str) -> None:
        key = self._make_key(question, context_chunks)
        self._store[key] = {
            "answer": answer,
            "timestamp": time.time(),
        }
        self._evict_oldest()

    def invalidate_all(self) -> None:
        self._store.clear()

    def stats(self) -> dict[str, float | int]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total) if total > 0 else 0.0
        return {
            "size": len(self._store),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hit_rate": hit_rate,
        }


llm_cache = LLMCache()
