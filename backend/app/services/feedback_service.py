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
) -> dict:
    now = datetime.now(timezone.utc)
    item = {
        "id": str(uuid.uuid4()),
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


async def list_feedback(db: Any, *, skip: int = 0, limit: int = 50) -> tuple[list[dict], int]:
    cursor = db["qa_feedback"].find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    items = [item async for item in cursor]
    total = await db["qa_feedback"].count_documents({})
    return items, total


async def get_relevant_feedback_examples(
    db: Any,
    *,
    question: str,
    detected_lang: str,
    limit: int = 3,
) -> list[dict]:
    lang_query = {"language": detected_lang}
    items = [
        item
        async for item in db["qa_feedback"].find(lang_query, {"_id": 0}).sort("created_at", -1).limit(300)
    ]

    if not items:
        items = [
            item
            async for item in db["qa_feedback"].find({}, {"_id": 0}).sort("created_at", -1).limit(300)
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


async def get_best_feedback_match(query: str, top_k: int = 1) -> list[dict]:
    return []
