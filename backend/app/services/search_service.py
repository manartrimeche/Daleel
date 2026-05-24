"""
Search service — vector similarity search over MongoDB-stored embeddings.

Supports two backends (configured via DALEEL_VECTOR_SEARCH_BACKEND):
  • "faiss"          — FAISS in-memory index (default, fast, scalable)
  • "python-cosine"  — brute-force Python cosine (legacy fallback)
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from fastapi import HTTPException

from app.config import get_settings
from app.database import get_collection
from app.services.embedding_service import (
    embed_text_for_search_async,
    get_primary_embedding_dimension,
)
from app.services.faiss_index import FAISS_AVAILABLE, FAISS_READY, faiss_manager

logger = logging.getLogger(__name__)

# Dominant embedding size among stored chunks (invalidated on ingest / delete).
_effective_stored_dim_cache: int | None = None


def invalidate_embedding_dimension_cache() -> None:
    global _effective_stored_dim_cache
    _effective_stored_dim_cache = None


async def _aggregate_dominant_stored_embedding_dim() -> int | None:
    """Most common non-empty `embedding` length in `chunks`, or None if none."""
    pipeline = [
        {"$match": {"embedding.0": {"$exists": True}}},
        {"$project": {"sz": {"$size": "$embedding"}}},
        {"$match": {"sz": {"$gt": 0}}},
        {"$group": {"_id": "$sz", "c": {"$sum": 1}}},
        {"$sort": {"c": -1}},
        {"$limit": 1},
    ]
    coll = get_collection("chunks")
    async for row in coll.aggregate(pipeline):
        d = row.get("_id")
        if isinstance(d, int):
            return d
    return None


async def get_effective_query_embedding_dimension() -> int:
    """
    Dimension to use for query vectors: matches the majority of stored chunks,
    or the primary model if the collection has no embeddings yet.
    """
    global _effective_stored_dim_cache
    if _effective_stored_dim_cache is not None:
        return _effective_stored_dim_cache
    dominant = await _aggregate_dominant_stored_embedding_dim()
    if dominant is None:
        dim = get_primary_embedding_dimension()
        logger.info(
            "No stored chunk embeddings; using primary model dimension %s for queries",
            dim,
        )
    else:
        dim = dominant
        primary = get_primary_embedding_dimension()
        if dim != primary:
            logger.warning(
                "Stored chunks are predominantly %s-dim; query vectors will use a matching encoder "
                "(primary model is %s-dim). Re-index with the primary model for a single pipeline.",
                dim,
                primary,
            )
    _effective_stored_dim_cache = dim
    return dim



def _parse_language_filter(language_filter: Optional[str]) -> list[str]:
    if not language_filter:
        return []
    parts = [p.strip() for p in str(language_filter).split("+") if p.strip()]
    if not parts:
        return []
    return list(dict.fromkeys(parts))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    dot = np.dot(va, vb)
    norm = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(dot / norm) if norm > 0 else 0.0


async def _python_search(
    query_vec: list[float],
    top_k: int,
    language_filter: Optional[str],
    document_id: Optional[str],
    extra_filter: Optional[dict] = None,
    allowed_document_ids: set[str] | None = None,
) -> list[dict]:
    query: dict = {"embedding": {"$ne": None}}
    lang_values = _parse_language_filter(language_filter)
    if len(lang_values) == 1:
        query["language"] = lang_values[0]
    elif len(lang_values) > 1:
        query["language"] = {"$in": lang_values}
    if document_id:
        query["document_id"] = document_id
    elif allowed_document_ids is not None:
        if not allowed_document_ids:
            return []
        query["document_id"] = {"$in": list(allowed_document_ids)}
    if extra_filter:
        query.update(extra_filter)

    documents = {
        doc["id"]: doc.get("filename")
        async for doc in get_collection("documents").find({})
    }

    scored: list[tuple[float, dict]] = []
    query_dim = len(query_vec)
    skipped_mismatched_dims = 0
    cursor = get_collection("chunks").find(query)
    async for chunk in cursor:
        embedding = chunk.get("embedding") or []
        if not embedding:
            continue
        if len(embedding) != query_dim:
            skipped_mismatched_dims += 1
            continue
        score = _cosine_similarity(query_vec, embedding)
        scored.append(
            (
                score,
                {
                    "chunk_id": chunk.get("id"),
                    "document_id": chunk.get("document_id"),
                    "filename": documents.get(chunk.get("document_id")),
                    "text": chunk.get("text"),
                    "page_number": chunk.get("page_number"),
                    "section": chunk.get("section"),
                    "language": chunk.get("language"),
                    "chunk_index": chunk.get("chunk_index"),
                    "score": score,
                    "metadata": chunk.get("metadata"),
                    "loi_id": chunk.get("loi_id") or (chunk.get("metadata") or {}).get("loi_id"),
                    "article_id": chunk.get("article_id") or (chunk.get("metadata") or {}).get("article_id"),
                },
            )
        )

    if skipped_mismatched_dims:
        logger.warning(
            "Skipped %s chunk(s) due to embedding dimension mismatch (query_dim=%s)",
            skipped_mismatched_dims,
            query_dim,
        )

    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[:top_k]]


def _use_faiss() -> bool:
    """Decide whether to use the FAISS backend."""
    if not FAISS_AVAILABLE:
        return False
    return get_settings().vector_search_backend == "faiss"


async def semantic_search(
    db,
    query: str,
    top_k: int = 10,
    language_filter: Optional[str] = None,
    document_id: Optional[str] = None,
    extra_filter: Optional[dict] = None,
    organization_id: Optional[str] = None,
) -> list[dict]:
    """Vector similarity search — routes to FAISS or Python backend.

    *extra_filter* is merged into the MongoDB query for the Python backend.
    FAISS does not natively support metadata filtering; the filter is applied
    post-hoc when FAISS is active (best-effort).
    """
    stored_dim = await get_effective_query_embedding_dimension()
    query_vec = await embed_text_for_search_async(query, stored_dim)
    allowed_document_ids: set[str] | None = None
    if organization_id:
        allowed_document_ids = {
            doc["id"]
            async for doc in get_collection("documents").find(
                {"organization_id": organization_id},
                {"id": 1},
            )
        }
        if document_id and document_id not in allowed_document_ids:
            return []

    if _use_faiss():
        await faiss_manager.ensure_ready()
        if not FAISS_READY:
            raise HTTPException(
                status_code=503,
                detail="Index unavailable, re-embedding in progress",
            )
        results = await faiss_manager.search(
            query_vec, top_k, language_filter, document_id
        )
        if results:
            if allowed_document_ids is not None:
                results = [r for r in results if r.get("document_id") in allowed_document_ids]
            if extra_filter:
                # Best-effort post-filtering: keep results whose metadata match extra_filter.
                # This is a temporary measure until FAISS metadata filtering is wired.
                def _matches(row: dict) -> bool:
                    for k, v in extra_filter.items():
                        if row.get(k) != v and row.get("metadata", {}).get(k) != v:
                            return False
                    return True
                results = [r for r in results if _matches(r)]
            logger.debug("FAISS search: %s results", len(results))
            return results
        # Fall through to Python search if FAISS returned nothing (empty index)

    results = await _python_search(
        query_vec,
        top_k,
        language_filter,
        document_id,
        extra_filter,
        allowed_document_ids=allowed_document_ids,
    )
    logger.debug("Python cosine search: %s results", len(results))
    return results


async def create_vector_index(db, index_type: str = "python-cosine") -> dict:
    """MongoDB does not use pgvector indexes in this deployment."""
    return {
        "status": "not_applicable",
        "index_type": index_type,
        "message": "Vector search is handled in Python over MongoDB embeddings.",
    }


async def get_vector_stats(db) -> dict:
    """Return basic embedding statistics for MongoDB storage."""
    from app.services.embedding_service import get_embedding_cache_stats

    total_vectors = await get_collection("chunks").count_documents({"embedding": {"$ne": None}})
    total_chunks = await get_collection("chunks").count_documents({})
    dominant = await _aggregate_dominant_stored_embedding_dim()
    primary_d = get_primary_embedding_dimension()
    backend = "faiss" if _use_faiss() and faiss_manager.is_ready else "python-cosine"
    return {
        "pgvector_available": False,
        "pgvector_enabled_config": False,
        "faiss_available": FAISS_AVAILABLE,
        "faiss_index_size": faiss_manager.size if FAISS_AVAILABLE else 0,
        "active_backend": backend,
        "total_vectors": int(total_vectors),
        "index_name": None,
        "index_type": None,
        # `embedding_dimension` kept for older clients (primary model output size)
        "embedding_dimension": primary_d,
        "embedding_dimension_primary_model": primary_d,
        "embedding_dimension_stored_dominant": dominant,
        "total_chunks": int(total_chunks),
        "embedding_cache": get_embedding_cache_stats(),
    }
