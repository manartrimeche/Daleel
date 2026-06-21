"""
Exigence matching service — semantic search over extracted exigences.

Given a user query (question, situation description, or document text),
finds the most relevant exigences from the database using cosine similarity
on embeddings. Returns results enriched with criticality scores.

This differs from the main semantic_search (which operates on raw document
chunks) by searching specifically in the exigences collection — already
classified, typed, and scored.
"""

from __future__ import annotations

import logging

import numpy as np

from app.database import get_collection
from app.services.embedding_service import embed_text_async, embed_texts_async
from app.services.criticality_service import compute_criticality_score, score_to_level

logger = logging.getLogger(__name__)

# In-memory cache: maps document_id → list of (exigence_dict, embedding_vector)
_exigence_cache: dict[str, list[tuple[dict, np.ndarray]]] = {}


async def _load_exigence_embeddings(
    document_id: str | None = None,
    language: str | None = None,
) -> list[tuple[dict, np.ndarray]]:
    """
    Load exigences from MongoDB and compute their embeddings.

    Uses a simple in-memory cache keyed by document_id+language.
    The cache is never invalidated within a server lifetime — acceptable
    because exigences rarely change once extracted.
    """
    cache_key = f"{document_id or '__all__'}:{language or '__any__'}"
    if cache_key in _exigence_cache:
        return _exigence_cache[cache_key]

    # If language filter requested, find document IDs matching that language
    query: dict = {}
    if document_id:
        query["document_id"] = document_id
    elif language:
        doc_ids = await (
            get_collection("documents")
            .find({"language": language}, {"_id": 0, "id": 1})
            .to_list(length=500)
        )
        if doc_ids:
            query["document_id"] = {"$in": [d["id"] for d in doc_ids]}
        else:
            _exigence_cache[cache_key] = []
            return []

    exigences = await (
        get_collection("exigences")
        .find(query, {"_id": 0})
        .sort([("page_number", 1)])
        .to_list(length=5000)
    )

    if not exigences:
        _exigence_cache[cache_key] = []
        return []

    # Batch-embed all exigence texts
    texts = [e.get("text", "") for e in exigences]
    embeddings = await embed_texts_async(texts)

    paired = [
        (e, np.array(emb, dtype=np.float32))
        for e, emb in zip(exigences, embeddings)
    ]

    _exigence_cache[cache_key] = paired
    logger.info(
        "Cached %d exigence embeddings for %s",
        len(paired), cache_key,
    )
    return paired


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / norm) if norm > 0 else 0.0


def _detect_language(text: str) -> str | None:
    """Simple language detection: Arabic script → 'ar', else 'fr'."""
    arabic_chars = sum(1 for c in text if "؀" <= c <= "ۿ")
    if arabic_chars > len(text) * 0.3:
        return "ar"
    return "fr"


async def match_exigences(
    query: str,
    *,
    document_id: str | None = None,
    exigence_type: str | None = None,
    language: str | None = None,
    top_k: int = 15,
    min_score: float = 0.20,
) -> list[dict]:
    """
    Find exigences most relevant to a user query.

    Parameters
    ----------
    query : str
        The user's question, situation description, or document excerpt.
    document_id : str, optional
        Restrict to exigences from a specific document.
    exigence_type : str, optional
        Filter by type (obligation, sanction, condition, prohibition).
    language : str, optional
        Filter by document language ('fr', 'ar', 'en').
        If not provided, auto-detected from the query text.
    top_k : int
        Maximum number of results.
    min_score : float
        Minimum cosine similarity to include.

    Returns
    -------
    List of dicts with keys: article, type, text, confidence,
    relevance_score, criticality_level, criticality_score, document_id, page.
    """
    # Auto-detect language if not provided
    if not language and not document_id:
        language = _detect_language(query)

    # Embed the query
    query_vec = np.array(await embed_text_async(query), dtype=np.float32)

    # Load exigence embeddings
    paired = await _load_exigence_embeddings(document_id, language=language)
    if not paired:
        return []

    # Compute similarities
    scored: list[tuple[float, dict]] = []
    for exigence, emb_vec in paired:
        # Type filter
        if exigence_type and exigence.get("exigence_type") != exigence_type:
            continue

        sim = _cosine_similarity(query_vec, emb_vec)
        if sim >= min_score:
            scored.append((sim, exigence))

    # Sort by relevance
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    # Build sanctions context per article for inherited criticality
    articles_sanctions: dict[str, str] = {}
    for _, e in scored:
        if e.get("exigence_type") == "sanction":
            art = e.get("article_reference") or ""
            prev = articles_sanctions.get(art, "")
            articles_sanctions[art] = (prev + " " + (e.get("text") or "")).strip()

    # Enrich with criticality
    type_labels = {
        "obligation": "Obligation",
        "sanction": "Sanction",
        "condition": "Condition",
        "prohibition": "Interdiction",
    }

    results = []
    for sim, e in top:
        etype = e.get("exigence_type", "obligation")
        art = e.get("article_reference") or ""
        sanctions_ctx = articles_sanctions.get(art, "")

        fake_action = {"modalite": etype, "action_precise": e.get("text", "")}
        crit_score, crit_factors = compute_criticality_score(
            fake_action, sanctions_context=sanctions_ctx,
        )
        level = score_to_level(crit_score)

        results.append({
            "article": art,
            "type": type_labels.get(etype, etype),
            "text": e.get("text", ""),
            "confidence": e.get("confidence_score"),
            "relevance_score": round(sim, 3),
            "criticality_level": level.capitalize(),
            "criticality_score": round(crit_score, 2),
            "document_id": e.get("document_id"),
            "page": e.get("page_number"),
        })

    return results


def invalidate_cache(document_id: str | None = None):
    """Clear cached embeddings (e.g., after re-extraction)."""
    if document_id:
        # Cache keys are "{document_id}:{language}" — drop every variant.
        prefix = f"{document_id}:"
        for key in [k for k in _exigence_cache if k.startswith(prefix)]:
            _exigence_cache.pop(key, None)
    else:
        _exigence_cache.clear()
