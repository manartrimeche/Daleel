"""
Cross-encoder reranking service for top retrieved chunks.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time

logger = logging.getLogger(__name__)


class RerankingService:
    """
    Optional cross-encoder reranking on top of hybrid retrieval.
    """

    MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self) -> None:
        self.enabled = os.getenv("ENABLE_CROSS_ENCODER", "false").lower() == "true"
        self._model = None
        self._load_attempted = False
        self._load_failed = False
        self._load_lock = threading.Lock()

    def _ensure_model_loaded(self) -> bool:
        if not self.enabled:
            return False
        if self._model is not None:
            return True
        if self._load_attempted and self._load_failed:
            return False

        with self._load_lock:
            if self._model is not None:
                return True
            if self._load_attempted and self._load_failed:
                return False

            self._load_attempted = True
            try:
                from sentence_transformers import CrossEncoder

                self._model = CrossEncoder(self.MODEL_NAME)
                self._load_failed = False
                logger.info("Cross-encoder reranker loaded: %s", self.MODEL_NAME)
                return True
            except Exception:
                self._model = None
                self._load_failed = True
                logger.exception("Failed to load cross-encoder reranker")
                return False

    def is_available(self) -> bool:
        return self._ensure_model_loaded()

    def _score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        if self._model is None:
            return []
        scores = self._model.predict(pairs)
        return [float(score) for score in scores]

    async def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        if not chunks:
            return chunks
        if not self._ensure_model_loaded():
            return chunks

        limited_chunks = chunks[:20]
        pairs = [(query, str(chunk.get("text") or "")) for chunk in limited_chunks]

        t0 = time.perf_counter()
        try:
            scores = await asyncio.get_event_loop().run_in_executor(
                None,
                self._score_pairs,
                pairs,
            )
        except Exception:
            logger.exception("Cross-encoder reranking inference failed")
            return chunks

        elapsed = time.perf_counter() - t0
        if elapsed > 2.0:
            logger.warning(
                "Cross-encoder reranking took %.2fs for %d chunks",
                elapsed,
                len(limited_chunks),
            )

        for chunk, score in zip(limited_chunks, scores):
            chunk["rerank_score"] = float(score)

        return sorted(
            limited_chunks,
            key=lambda chunk: float(chunk.get("rerank_score", 0.0)),
            reverse=True,
        )
