"""
Embedding service — sentence-transformers for multilingual text → vector.

Includes an LRU cache for search queries so repeated / popular questions
skip the model entirely.
"""

import asyncio
import hashlib
import logging
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import List


from app.config import get_settings

_executor = ThreadPoolExecutor(max_workers=2)

logger = logging.getLogger(__name__)

_model = None
_model_dim_384 = None


# ── Embedding LRU cache ──────────────────────────────────────────────────────

class _EmbeddingCache:
    """Thread-safe, bounded LRU cache for (text, dim) → embedding vectors."""

    def __init__(self, maxsize: int = 512):
        self._maxsize = maxsize
        self._store: OrderedDict[str, List[float]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _key(text: str, dim: int) -> str:
        return hashlib.sha256(f"{dim}:{text}".encode()).hexdigest()

    def get(self, text: str, dim: int) -> List[float] | None:
        k = self._key(text, dim)
        if k in self._store:
            self._store.move_to_end(k)
            self._hits += 1
            return self._store[k]
        self._misses += 1
        return None

    def put(self, text: str, dim: int, vec: List[float]) -> None:
        k = self._key(text, dim)
        self._store[k] = vec
        self._store.move_to_end(k)
        while len(self._store) > self._maxsize:
            self._store.popitem(last=False)

    @property
    def stats(self) -> dict:
        return {
            "size": len(self._store),
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / max(self._hits + self._misses, 1), 4),
        }


_search_cache: _EmbeddingCache | None = None


def _get_search_cache() -> _EmbeddingCache:
    global _search_cache
    if _search_cache is None:
        settings = get_settings()
        _search_cache = _EmbeddingCache(maxsize=settings.embedding_cache_maxsize)
        logger.info("Embedding search cache initialized (maxsize=%s)", settings.embedding_cache_maxsize)
    return _search_cache


def get_embedding_cache_stats() -> dict:
    """Return cache hit/miss statistics (for admin endpoints)."""
    return _get_search_cache().stats


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model ready")
    return _model


def get_primary_embedding_dimension() -> int:
    """Vector size produced by the configured primary embedding model."""
    return int(_get_model().get_sentence_embedding_dimension())


def _get_model_dim_384():
    global _model_dim_384
    if _model_dim_384 is None:
        from sentence_transformers import SentenceTransformer
        settings = get_settings()
        name = settings.embedding_model_dim_384
        logger.info("Loading 384-dim embedding model (query compat): %s", name)
        _model_dim_384 = SentenceTransformer(name)
        d = int(_model_dim_384.get_sentence_embedding_dimension())
        if d != 384:
            logger.warning(
                "embedding_model_dim_384 produced dim=%s (expected 384); search vs legacy chunks may be wrong",
                d,
            )
    return _model_dim_384


def embed_text(text: str) -> List[float]:
    """Embed a single text with the primary configured model (sync)."""
    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


async def embed_text_async(text: str) -> List[float]:
    """Non-blocking version of embed_text for use in async handlers."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, embed_text, text)


def embed_text_for_search(text: str, stored_vector_dim: int) -> List[float]:
    """
    Encode `text` so it matches vectors stored on chunks.

    Uses an LRU cache so repeated identical queries are free.

    When the corpus was indexed with a different model size (e.g. 384-d MiniLM)
    than the primary model (e.g. 768-d mpnet), use the compat model for queries
    so cosine search is defined and relevant.
    """
    cache = _get_search_cache()
    cached = cache.get(text, stored_vector_dim)
    if cached is not None:
        return cached

    primary_dim = get_primary_embedding_dimension()
    if stored_vector_dim == primary_dim:
        vec = embed_text(text)
    elif stored_vector_dim == 384:
        model = _get_model_dim_384()
        vec = model.encode(text, normalize_embeddings=True).tolist()
    else:
        logger.warning(
            "Unsupported stored embedding dimension %s (primary=%s); using primary model",
            stored_vector_dim,
            primary_dim,
        )
        vec = embed_text(text)

    cache.put(text, stored_vector_dim, vec)
    return vec


async def embed_text_for_search_async(text: str, stored_vector_dim: int) -> List[float]:
    """Non-blocking version of embed_text_for_search."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _executor, partial(embed_text_for_search, text, stored_vector_dim)
    )


def embed_texts(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """Embed multiple texts → list of float vectors (sync)."""
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True,
                        batch_size=batch_size, show_progress_bar=False)
    return [v.tolist() for v in vecs]


async def embed_texts_async(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """Non-blocking version of embed_texts for use in async handlers."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _executor, partial(embed_texts, texts, batch_size=batch_size)
    )
