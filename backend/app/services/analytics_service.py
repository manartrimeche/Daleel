"""
Analytics service — aggregate metrics for the admin dashboard charts.

Provides time-series and summary data for:
  - Q&A usage (questions per day)
  - User satisfaction (average rating over time)
  - Compliance coverage (per-profile exigence applicability %)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


async def get_qa_daily_counts(db: Any, days: int = 30) -> list[dict]:
    """Return number of questions asked per day.

    Queries ``chat_history`` (every question asked) and merges with
    ``qa_feedback`` (explicit ratings) so the chart reflects actual usage
    even when users don't leave feedback.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    # Primary source: chat_history (every question)
    rows = await db["chat_history"].aggregate(pipeline).to_list(length=400)
    counts: dict[str, int] = {r["_id"]: r["count"] for r in rows}

    # Fallback: if chat_history is empty, try qa_feedback
    if not counts:
        rows = await db["qa_feedback"].aggregate(pipeline).to_list(length=400)
        counts = {r["_id"]: r["count"] for r in rows}

    return [{"date": d, "count": c} for d, c in sorted(counts.items())]


async def get_satisfaction_over_time(db: Any, days: int = 30) -> list[dict]:
    """Return average feedback rating per day."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"created_at": {"$gte": since}, "rating": {"$ne": None}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "avg_rating": {"$avg": "$rating"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    rows = await db["qa_feedback"].aggregate(pipeline).to_list(length=400)
    return [
        {"date": r["_id"], "avg_rating": round(r["avg_rating"], 2), "count": r["count"]}
        for r in rows
    ]


async def get_compliance_coverage(db: Any) -> list[dict]:
    """
    Per-profile compliance coverage:
      coverage = applicable exigences / total exigences * 100
    """
    profiles = await db["company_profiles"].find({}, {"_id": 0, "id": 1, "name": 1}).to_list(length=500)
    total_exigences = await db["exigences"].count_documents({})
    if not total_exigences:
        return [{"profile_id": p["id"], "profile_name": p.get("name", "?"), "coverage_pct": 0, "applicable": 0, "total": 0} for p in profiles]

    # Batch: un seul pipeline pour compter les applicabilités par profil
    profile_ids = [p["id"] for p in profiles]
    pipeline = [
        {"$match": {"profile_id": {"$in": profile_ids}, "is_applicable": True}},
        {"$group": {"_id": "$profile_id", "applicable": {"$sum": 1}}},
    ]
    counts_cursor = db["exigence_applicabilities"].aggregate(pipeline)
    counts_by_profile: dict[str, int] = {}
    async for row in counts_cursor:
        counts_by_profile[row["_id"]] = row["applicable"]

    results = []
    for profile in profiles:
        applicable = counts_by_profile.get(profile["id"], 0)
        coverage = round(applicable / total_exigences * 100, 1)
        results.append({
            "profile_id": profile["id"],
            "profile_name": profile.get("name", "?"),
            "coverage_pct": coverage,
            "applicable": applicable,
            "total": total_exigences,
        })
    return results


async def get_full_analytics(db: Any, days: int = 30) -> dict:
    """Aggregate all analytics data for the dashboard."""
    qa_daily = await get_qa_daily_counts(db, days)
    satisfaction = await get_satisfaction_over_time(db, days)
    coverage = await get_compliance_coverage(db)
    return {
        "qa_daily": qa_daily,
        "satisfaction": satisfaction,
        "coverage": coverage,
        "period_days": days,
    }
