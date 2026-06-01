"""
Notification service — generate and persist alerts when amendments affect company profiles.

Alert types:
  • amendment_impact  — an applied amendment touches articles relevant to a profile
  • coverage_change   — applicability re-evaluation changed a profile's coverage
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Persistence ───────────────────────────────────────────────────────────────

# Alert types whose lifetime is naturally short (activity log).
# A TTL index on `expires_at` purges them automatically.
_EPHEMERAL_ALERT_TYPES = frozenset({
    "account_login",
    "account_updated",
    "account_deactivated",
    "member_joined",
    "invitation_revoked",
})
_EPHEMERAL_TTL_DAYS = 90


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
    details = details or {}
    item: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "alert_type": alert_type,
        "profile_id": profile_id,
        "profile_name": profile_name,
        "title": title,
        "message": message,
        "details": details,
        "read": False,
        "created_at": now,
    }
    if alert_type in _EPHEMERAL_ALERT_TYPES:
        item["expires_at"] = now + timedelta(days=_EPHEMERAL_TTL_DAYS)
    await db["notifications"].insert_one(item)
    item.pop("_id", None)
    logger.info("Notification created: [%s] %s", alert_type, title)
    return item


async def list_notifications(
    db: Any,
    *,
    skip: int = 0,
    limit: int = 50,
    organization_id: str | None = None,
) -> tuple[list[dict], int]:
    """List notifications most-recent-first."""
    query: dict[str, Any] = {}
    if organization_id:
        query["details.organization_id"] = organization_id

    total = await db["notifications"].count_documents(query)
    cursor = (
        db["notifications"]
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    items = [doc async for doc in cursor]
    return items, total


async def mark_read(
    db: Any,
    notification_id: str,
    *,
    organization_id: str | None = None,
    allow_global: bool = False,
    user_id: str | None = None,
) -> str:
    """
    Mark a notification as read within the caller's allowed scope.

    Returns:
        "ok"       — the notification was updated
        "noop"     — the notification exists and is in scope but was already read
        "not_found"— no notification matches the scope (404)
        "denied"   — the call lacks required scope (no org_id or no user_id)
    """
    if not allow_global and (not organization_id or not user_id):
        return "denied"

    filt: dict[str, Any] = {"id": notification_id}
    if not allow_global:
        filt["details.organization_id"] = organization_id

    update = {"$set": {"read": True}} if allow_global else {"$addToSet": {"read_by": user_id}}

    result = await db["notifications"].update_one(filt, update)
    if result.matched_count == 0:
        return "not_found"
    return "ok" if result.modified_count > 0 else "noop"


async def mark_all_read(
    db: Any,
    *,
    organization_id: str | None = None,
    allow_global: bool = False,
    user_id: str | None = None,
) -> int:
    """
    Mark every notification in the caller's scope as read.

    Returns the number of notifications actually updated.
    """
    if allow_global:
        result = await db["notifications"].update_many(
            {"read": {"$ne": True}},
            {"$set": {"read": True}},
        )
        return result.modified_count

    if not organization_id or not user_id:
        return 0

    result = await db["notifications"].update_many(
        {
            "details.organization_id": organization_id,
            "read": {"$ne": True},
            "read_by": {"$ne": user_id},
        },
        {"$addToSet": {"read_by": user_id}},
    )
    return result.modified_count


async def mark_processed(
    db: Any,
    notification_id: str,
    *,
    decision: str,
    result_payload: dict,
) -> None:
    """
    Mark a notification as processed by an approval / rejection flow.

    Sets ``read: True`` and records both the decision and the resulting
    payload under ``details``. Used by the super_admin approve / reject
    endpoints, which need to attach business metadata atomically with
    the read flag.
    """
    field = "approved_result" if decision == "approved" else "rejected_result"
    await db["notifications"].update_one(
        {"id": notification_id},
        {
            "$set": {
                "read": True,
                "details.approval_status": decision,
                f"details.{field}": result_payload,
                "processed_at": datetime.now(timezone.utc),
            }
        },
    )


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
        profile = await db["company_profiles"].find_one(
            {"id": pid},
            {"_id": 0, "name": 1, "organization_id": 1},
        )
        pname = (profile or {}).get("name", pid[:8])
        details = {
            "loi_id": loi_id,
            "loi_code": loi_code,
            "operation_type": operation_type,
            "target_article_key": target_article_key,
        }
        if (profile or {}).get("organization_id"):
            details["organization_id"] = profile["organization_id"]

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
            details=details,
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


async def notify_amendment_summary(
    db: Any,
    *,
    loi_id: str,
    loi_code: str,
    loi_name: str,
    diff: dict,
    operations: list[dict],
) -> int:
    """
    Send a single amendment summary notification to the super_admin scope.

    Called once after all article-level operations are applied. Targeted
    per-organization notifications are handled separately by
    ``notify_amendment_impact`` (which only fires for profiles whose
    applicable exigences are actually touched).
    """
    added = diff.get("added", 0)
    modified = diff.get("modified", 0)
    removed = diff.get("removed", 0)

    op_lines = []
    for op in operations[:20]:
        op_type = op.get("type", "?")
        key = op.get("article_key", "?")
        label = {"ADD": "Ajouté", "REPLACE": "Modifié", "REPEAL": "Supprimé"}.get(op_type, op_type)
        op_lines.append(f"  • {label} : {key}")
    if len(operations) > 20:
        op_lines.append(f"  … et {len(operations) - 20} autre(s)")

    detail_text = "\n".join(op_lines) if op_lines else "  Aucun changement d'article."

    message = (
        f"Un amendement a été appliqué à la loi « {loi_name} » ({loi_code}).\n\n"
        f"Résumé : {added} article(s) ajouté(s), {modified} modifié(s), {removed} supprimé(s).\n\n"
        f"Détail des opérations :\n{detail_text}"
    )

    await create_notification(
        db,
        alert_type="amendment_summary",
        title=f"Amendement appliqué — {loi_code}",
        message=message,
        details={
            "loi_id": loi_id,
            "loi_code": loi_code,
            "loi_name": loi_name,
            "added": added,
            "modified": modified,
            "removed": removed,
            "operations": operations[:50],
        },
    )
    logger.info("Recorded amendment summary for loi %s (%s)", loi_code, loi_id)
    return 1
