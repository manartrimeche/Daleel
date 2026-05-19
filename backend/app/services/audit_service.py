"""
Audit Service — Sprint 5 (Step 13 of the workflow).

Append-only audit trail for all legislative update events.

Every significant system action writes one AuditLog entry:
  document_classified  — document_type set to 'modificatif'
  amendment_extracted  — LLM extracted operations from an amendment doc
  amendment_applied    — an AmendmentOperation was applied to an article
  version_superseded   — an ArticleVersion marked 'superseded'
  article_repealed     — an ArticleVersion marked 'repealed'
  recalculation_done   — post-amendment pipeline completed

AuditLog records are NEVER updated or deleted.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.database import get_collection

logger = logging.getLogger(__name__)
_collection = get_collection



# ─────────────────────────────────────────────────────────────
# Serialiser
# ─────────────────────────────────────────────────────────────

def _log_to_dict(log: dict) -> dict:
    return {
        "id": log.get("id"),
        "actor": log.get("actor"),
        "event_type": log.get("event_type"),
        "loi_id": log.get("loi_id"),
        "article_id": log.get("article_id"),
        "old_version_id": log.get("old_version_id"),
        "new_version_id": log.get("new_version_id"),
        "amendment_op_id": log.get("amendment_op_id"),
        "proof_extract": log.get("proof_extract"),
        "legal_reference": log.get("legal_reference"),
        "confidence": log.get("confidence"),
        "details": log.get("details") or {},
        "created_at": log.get("created_at"),
    }


# ─────────────────────────────────────────────────────────────
# Write
# ─────────────────────────────────────────────────────────────

async def log_event(
    db,
    event_type: str,
    *,
    actor: str = "system",
    loi_id: Optional[str] = None,
    article_id: Optional[str] = None,
    old_version_id: Optional[str] = None,
    new_version_id: Optional[str] = None,
    amendment_op_id: Optional[str] = None,
    proof_extract: Optional[str] = None,
    legal_reference: Optional[str] = None,
    confidence: float = 1.0,
    details: Optional[dict] = None,
    commit: bool = False,
    ) -> dict:
    """
    Write one audit log entry.

    Uses flush (not commit) by default so the caller can batch multiple
    log entries in the same transaction.
    Set commit=True to immediately persist a standalone event.
    """
    log = {
        "id": str(uuid.uuid4()),
        "actor": actor,
        "event_type": event_type,
        "loi_id": loi_id,
        "article_id": article_id,
        "old_version_id": old_version_id,
        "new_version_id": new_version_id,
        "amendment_op_id": amendment_op_id,
        "proof_extract": (proof_extract or "")[:2000],
        "legal_reference": (legal_reference or "")[:512] or None,
        "confidence": max(0.0, min(1.0, confidence)),
        "details": details or {},
        "created_at": datetime.now(timezone.utc),
    }
    await _collection("audit_logs").insert_one(log)

    logger.info(
        f"AuditLog [{event_type}] actor={actor} "
        f"loi={loi_id} article={article_id} "
        f"old_v={old_version_id} new_v={new_version_id}"
    )
    return _log_to_dict(log)


# ─────────────────────────────────────────────────────────────
# Read
# ─────────────────────────────────────────────────────────────

async def get_audit_logs(
    db,
    loi_id: Optional[str] = None,
    article_id: Optional[str] = None,
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[dict], int]:
    """
    Query audit logs with optional filters.
    Always returned most-recent-first.
    """
    query: dict = {}

    if loi_id:
        query["loi_id"] = loi_id
    if article_id:
        query["article_id"] = article_id
    if event_type:
        query["event_type"] = event_type

    total = await _collection("audit_logs").count_documents(query)
    cursor = _collection("audit_logs").find(query).sort("created_at", -1).skip(skip).limit(limit)
    logs = [_log_to_dict(log) async for log in cursor]

    return logs, int(total)
