"""
Feedback service: persist user-corrected answers and retrieve relevant examples.

This enables lightweight continuous learning without fine-tuning by injecting
validated examples into the generation prompt.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.processing.text_utils import detect_query_language as _detect_language

_TOKEN_RE = re.compile(r"[\u0600-\u06FF\w]+", re.UNICODE)




def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) > 1}


def _similarity(query: str, candidate: str) -> float:
    q = _tokenize(query)
    c = _tokenize(candidate)
    if not q or not c:
        return 0.0
    inter = len(q.intersection(c))
    union = len(q.union(c))
    return inter / max(1, union)


async def create_feedback(
    db: Any,
    *,
    question: str,
    corrected_answer: str,
    language: Optional[str],
    rating: Optional[int],
    notes: Optional[str],
    source_document_id: Optional[str],
    tags: list[str],
    organization_id: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    item = {
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "question": question.strip(),
        "corrected_answer": corrected_answer.strip(),
        "language": language or _detect_language(question),
        "rating": rating,
        "notes": notes.strip() if notes else None,
        "source_document_id": source_document_id,
        "tags": [t.strip().lower() for t in tags if t and t.strip()][:20],
        "created_at": now,
        "updated_at": now,
    }
    await db["qa_feedback"].insert_one(item)
    item.pop("_id", None)
    return item


async def list_feedback(
    db: Any,
    *,
    skip: int = 0,
    limit: int = 50,
    organization_id: Optional[str] = None,
) -> tuple[list[dict], int]:
    query: dict[str, Any] = {}
    if organization_id:
        query["organization_id"] = organization_id

    cursor = db["qa_feedback"].find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    items = [item async for item in cursor]
    total = await db["qa_feedback"].count_documents(query)
    return items, total


async def get_relevant_feedback_examples(
    db: Any,
    *,
    question: str,
    detected_lang: str,
    limit: int = 3,
    organization_id: Optional[str] = None,
) -> list[dict]:
    base_query: dict[str, Any] = {}
    if organization_id:
        base_query["organization_id"] = organization_id

    lang_query = {**base_query, "language": detected_lang}
    items = [
        item
        async for item in db["qa_feedback"].find(lang_query, {"_id": 0}).sort("created_at", -1).limit(300)
    ]

    if not items:
        items = [
            item
            async for item in db["qa_feedback"].find(base_query, {"_id": 0}).sort("created_at", -1).limit(300)
        ]

    scored: list[tuple[float, dict]] = []
    for item in items:
        sim = _similarity(question, str(item.get("question") or ""))
        rating = float(item.get("rating") or 3)
        score = sim + (0.04 * rating)
        if sim > 0.02:
            scored.append((score, item))

    scored.sort(key=lambda row: row[0], reverse=True)

    out: list[dict] = []
    for score, item in scored[:limit]:
        out.append(
            {
                "question": item.get("question", ""),
                "corrected_answer": item.get("corrected_answer", ""),
                "language": item.get("language", ""),
                "score": round(score, 4),
            }
        )
    return out


async def get_best_feedback_match(
    db: Any,
    *,
    question: str,
    detected_lang: str,
    source_document_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    min_score: float = 0.58,
) -> dict | None:
    query: dict[str, Any] = {"language": detected_lang}
    if source_document_id:
        query["source_document_id"] = source_document_id
    if organization_id:
        query["organization_id"] = organization_id

    items = [
        item
        async for item in db["qa_feedback"].find(query, {"_id": 0}).sort("created_at", -1).limit(300)
    ]
    best_item: dict | None = None
    best_score = 0.0
    for item in items:
        score = _similarity(question, str(item.get("question") or ""))
        if score > best_score:
            best_item = item
            best_score = score

    if best_item and best_score >= min_score:
        best_item["score"] = round(best_score, 4)
        return best_item
    return None
