"""
Notification service — generate and persist alerts when amendments affect company profiles.

Alert types:
  • amendment_impact  — an applied amendment touches articles relevant to a profile
  • coverage_change   — applicability re-evaluation changed a profile's coverage
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Persistence ───────────────────────────────────────────────────────────────

async def create_notification(
    db: Any,
    *,
    alert_type: str,
    profile_id: Optional[str] = None,
    profile_name: Optional[str] = None,
    title: str,
    message: str,
    details: dict | None = None,
) -> dict:
    """Insert a new notification into the database."""
    now = datetime.now(timezone.utc)
    item = {
        "id": str(uuid.uuid4()),
        "alert_type": alert_type,
        "profile_id": profile_id,
        "profile_name": profile_name,
        "title": title,
        "message": message,
        "details": details or {},
        "read": False,
        "created_at": now,
    }
    await db["notifications"].insert_one(item)
    item.pop("_id", None)
    logger.info("Notification created: [%s] %s", alert_type, title)
    return item


async def list_notifications(
    db: Any,
    *,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    """List notifications most-recent-first."""
    total = await db["notifications"].count_documents({})
    cursor = (
        db["notifications"]
        .find({}, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    items = [doc async for doc in cursor]
    return items, total


async def mark_read(db: Any, notification_id: str) -> bool:
    """Mark a single notification as read."""
    result = await db["notifications"].update_one(
        {"id": notification_id},
        {"$set": {"read": True}},
    )
    return result.modified_count > 0


# ── Alert generators (called by other services) ──────────────────────────────

async def notify_amendment_impact(
    db: Any,
    *,
    loi_id: str,
    loi_code: str,
    operation_type: str,
    target_article_key: str,
    affected_profile_ids: list[str],
) -> int:
    """
    Fire notifications for each company profile affected by an amendment.

    Called after an amendment operation is applied successfully.
    Returns the number of notifications created.
    """
    if not affected_profile_ids:
        return 0

    created = 0
    for pid in affected_profile_ids:
        profile = await db["company_profiles"].find_one({"id": pid}, {"_id": 0, "name": 1})
        pname = (profile or {}).get("name", pid[:8])
        await create_notification(
            db,
            alert_type="amendment_impact",
            profile_id=pid,
            profile_name=pname,
            title=f"Amendement {operation_type} — {target_article_key}",
            message=(
                f"L'opération {operation_type} sur l'article {target_article_key} "
                f"(loi {loi_code}) affecte le profil « {pname} ». "
                f"Veuillez réévaluer l'applicabilité et le plan d'action."
            ),
            details={
                "loi_id": loi_id,
                "loi_code": loi_code,
                "operation_type": operation_type,
                "target_article_key": target_article_key,
            },
        )
        created += 1
    return created


async def check_and_notify_amendment_impacts(
    db: Any,
    *,
    loi_id: str,
    operation_type: str,
    target_article_key: str,
) -> int:
    """
    Identify affected profiles and fire notifications.

    A profile is affected if it has any applicable exigence linked to the
    amended article's version.
    """
    loi = await db["lois"].find_one({"id": loi_id}, {"_id": 0, "code": 1})
    loi_code = (loi or {}).get("code", "?")

    # Find article by key in this loi
    article = await db["articles"].find_one(
        {"loi_id": loi_id, "article_key": target_article_key},
        {"_id": 0, "id": 1},
    )
    if not article:
        return 0

    # Get active version for this article
    active_version = await db["article_versions"].find_one(
        {"article_id": article["id"], "status": "active"},
        {"_id": 0, "id": 1},
    )
    if not active_version:
        return 0

    # Find exigences from this version
    exigence_ids = [
        e["id"]
        async for e in db["exigences"].find(
            {"article_version_id": active_version["id"]},
            {"_id": 0, "id": 1},
        )
    ]
    if not exigence_ids:
        return 0

    # Find profiles with applicable exigences
    affected_pids = set()
    async for app in db["exigence_applicabilities"].find(
        {"exigence_id": {"$in": exigence_ids}, "is_applicable": True},
        {"_id": 0, "profile_id": 1},
    ):
        affected_pids.add(app["profile_id"])

    return await notify_amendment_impact(
        db,
        loi_id=loi_id,
        loi_code=loi_code,
        operation_type=operation_type,
        target_article_key=target_article_key,
        affected_profile_ids=list(affected_pids),
    )
