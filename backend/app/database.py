"""
MongoDB database helpers.

This module exposes a shared Motor client, the active database handle,
and startup initialization for collections and indexes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError, OperationFailure

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

mongo_client = AsyncIOMotorClient(
    settings.mongodb_url,
    maxPoolSize=settings.mongodb_max_pool_size,
    minPoolSize=settings.mongodb_min_pool_size,
    serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
    connectTimeoutMS=settings.mongodb_connect_timeout_ms,
    socketTimeoutMS=settings.mongodb_socket_timeout_ms,
    retryWrites=True,
)
mongo_db = mongo_client[settings.mongodb_db_name]

_COLLECTION_INDEXES: dict[str, list[dict[str, Any]]] = {
    "documents": [
        {"fields": [("created_at", -1)]},
        {"fields": [("status", 1), ("created_at", -1)]},
        {"fields": [("language", 1), ("created_at", -1)]},
        {"fields": [("organization_id", 1), ("created_at", -1)]},
    ],
    "document_sources": [
        {"fields": [("document_id", 1)]},
        {"fields": [("file_hash", 1)], "kwargs": {"unique": True}},
    ],
    "document_raw_pages": [
        {"fields": [("document_id", 1), ("page_number", 1)]},
    ],
    "document_cleaned_texts": [
        {"fields": [("document_id", 1), ("page_number", 1), ("version", 1)]},
    ],
    "chunks": [
        {"fields": [("document_id", 1), ("chunk_index", 1)]},
        {"fields": [("document_id", 1), ("language", 1)]},
        {"fields": [("language", 1)]},
        {"fields": [("article_version_id", 1)]},
        {"fields": [("organization_id", 1)]},
        {"fields": [("embedding_dim", 1)]},
        {"fields": [("embedding_model", 1)]},
    ],
    "exigences": [
        {"fields": [("document_id", 1), ("page_number", 1)]},
        {"fields": [("document_id", 1), ("article_version_id", 1)]},
        {"fields": [("exigence_type", 1)]},
        {"fields": [("organization_id", 1), ("created_at", -1)]},
    ],
    "company_profiles": [
        {"fields": [("created_at", -1)]},
        {"fields": [("name", 1)]},
        {"fields": [("organization_id", 1)]},
    ],
    "exigence_applicabilities": [
        {"fields": [("profile_id", 1), ("exigence_id", 1)]},
        {"fields": [("profile_id", 1), ("is_applicable", 1)]},
    ],
    "lois": [
        {"fields": [("code", 1)], "kwargs": {"unique": True}},
        {"fields": [("created_at", -1)]},
    ],
    "articles": [
        {"fields": [("loi_id", 1), ("article_key", 1)], "kwargs": {"unique": True}},
        {"fields": [("loi_id", 1), ("article_number", 1)]},
    ],
    "article_versions": [
        {"fields": [("article_id", 1), ("is_current", -1)]},
        {"fields": [("article_id", 1), ("version_number", -1)], "kwargs": {"unique": True}},
    ],
    "actions": [
        {"fields": [("article_version_id", 1)]},
        {"fields": [("exigence_id", 1)]},
        {"fields": [("modalite", 1)]},
        {"fields": [("organization_id", 1), ("created_at", -1)]},
    ],
    "action_criticalities": [
        {"fields": [("action_id", 1)]},
        {"fields": [("criticality_level", 1)]},
    ],
    "action_dependencies": [
        {"fields": [("action_id", 1), ("depends_on_action_id", 1)]},
    ],
    "amendment_operations": [
        {"fields": [("document_id", 1)]},
        {"fields": [("document_id", 1), ("status", 1)]},
        {"fields": [("operation_type", 1)]},
        {"fields": [("status", 1)]},
    ],
    "audit_logs": [
        {"fields": [("created_at", -1)]},
        {"fields": [("loi_id", 1), ("created_at", -1)]},
        {"fields": [("article_id", 1), ("created_at", -1)]},
        {"fields": [("event_type", 1), ("created_at", -1)]},
        {"fields": [("actor", 1), ("created_at", -1)]},
    ],
    "qa_feedback": [
        {"fields": [("created_at", -1)]},
        {"fields": [("language", 1), ("created_at", -1)]},
        {"fields": [("source_document_id", 1), ("created_at", -1)]},
        {"fields": [("user_id", 1), ("created_at", -1)]},
        {"fields": [("rating", 1)]},
    ],
    # ── Compliance Case Management ──
    "compliance_cases": [
        {"fields": [("created_at", -1)]},
        {"fields": [("status", 1), ("created_at", -1)]},
        {"fields": [("priority", 1), ("created_at", -1)]},
        {"fields": [("company_profile_id", 1)]},
        {"fields": [("organization_id", 1), ("created_at", -1)]},
        {"fields": [("assignee_id", 1)]},
        {"fields": [("created_by", 1)]},
    ],
    "case_messages": [
        {"fields": [("case_id", 1), ("created_at", 1)]},
    ],
    "case_documents": [
        {"fields": [("case_id", 1)]},
        {"fields": [("case_id", 1), ("document_id", 1)], "kwargs": {"unique": True}},
    ],
    "case_document_analyses": [
        {"fields": [("case_id", 1), ("created_at", -1)]},
        {"fields": [("document_id", 1)]},
        {"fields": [("case_id", 1), ("document_id", 1)]},
    ],
    "case_findings": [
        {"fields": [("case_id", 1), ("created_at", -1)]},
        {"fields": [("case_id", 1), ("severity", 1)]},
        {"fields": [("case_id", 1), ("status", 1)]},
        {"fields": [("exigence_id", 1)]},
    ],
    "case_actions": [
        {"fields": [("case_id", 1), ("created_at", -1)]},
        {"fields": [("case_id", 1), ("status", 1)]},
        {"fields": [("case_id", 1), ("priority", 1)]},
        {"fields": [("finding_id", 1)]},
    ],
    # ── Compliance Steering ──
    "compliance_assessments": [
        {"fields": [("company_profile_id", 1), ("created_at", -1)]},
        {"fields": [("status", 1), ("created_at", -1)]},
    ],
    "controls": [
        {"fields": [("company_profile_id", 1), ("created_at", -1)]},
        {"fields": [("implementation_status", 1)]},
    ],
    "control_evidences": [
        {"fields": [("control_id", 1), ("created_at", -1)]},
        {"fields": [("status", 1)]},
    ],
    "requirement_control_links": [
        {"fields": [("exigence_id", 1), ("control_id", 1), ("assessment_id", 1)], "kwargs": {"unique": True}},
        {"fields": [("exigence_id", 1)]},
        {"fields": [("control_id", 1)]},
        {"fields": [("assessment_id", 1)]},
    ],
    "exception_register": [
        {"fields": [("company_profile_id", 1), ("created_at", -1)]},
        {"fields": [("exigence_id", 1)]},
        {"fields": [("status", 1)]},
    ],
    # ── Contract Analysis ──
    "contract_analyses": [
        {"fields": [("document_id", 1)], "kwargs": {"unique": True}},
        {"fields": [("organization_id", 1), ("created_at", -1)]},
        {"fields": [("status", 1), ("created_at", -1)]},
        {"fields": [("contract_type", 1)]},
        {"fields": [("score", 1)]},
    ],
    # ── Auth & Multi-tenant ──
    "users": [
        {"fields": [("email", 1)], "kwargs": {"unique": True}},
        {
            "fields": [("phone", 1)],
            "kwargs": {
                "unique": True,
                "name": "uniq_user_phone",
                "partialFilterExpression": {"phone": {"$type": "string"}},
            },
        },
        {"fields": [("organization_id", 1)]},
        {"fields": [("organization_id", 1), ("role", 1)]},
        {
            "fields": [("organization_id", 1), ("role", 1), ("owner_slot", 1)],
            "kwargs": {
                "unique": True,
                "name": "uniq_owner_per_org",
                "partialFilterExpression": {
                    "organization_id": {"$exists": True},
                    "role": "owner",
                },
            },
        },
        {"fields": [("role", 1)]},
        {"fields": [("created_at", -1)]},
    ],
    "organizations": [
        {"fields": [("name", 1)]},
        {
            "fields": [("name_key", 1)],
            "kwargs": {
                "unique": True,
                "name": "uniq_organization_name_key",
                "partialFilterExpression": {"name_key": {"$type": "string"}},
            },
        },
        {
            "fields": [("requested_by_email", 1)],
            "kwargs": {
                "unique": True,
                "name": "uniq_organization_contact_email",
                "partialFilterExpression": {"requested_by_email": {"$type": "string"}},
            },
        },
        {
            "fields": [("requested_by_phone", 1)],
            "kwargs": {
                "unique": True,
                "name": "uniq_organization_contact_phone",
                "partialFilterExpression": {"requested_by_phone": {"$type": "string"}},
            },
        },
        {"fields": [("sector", 1)]},
        {"fields": [("status", 1)]},
        {"fields": [("subscription_type", 1)]},
        {"fields": [("subscription_ends_at", 1)]},
        {"fields": [("created_at", -1)]},
    ],
    "invitations": [
        {"fields": [("token", 1)], "kwargs": {"unique": True}},
        {"fields": [("email", 1)]},
        {"fields": [("organization_id", 1)]},
        {"fields": [("status", 1)]},
    ],
    "notifications": [
        {"fields": [("created_at", -1)]},
        {"fields": [("read", 1), ("created_at", -1)]},
        {"fields": [("alert_type", 1), ("created_at", -1)]},
        {"fields": [("details.organization_id", 1), ("created_at", -1)]},
        # TTL : purge automatique des notifications éphémères (account_login,
        # account_updated, account_deactivated, member_joined, invitation_revoked).
        # Seules les notifications possédant un champ ``expires_at`` sont concernées.
        {
            "fields": [("expires_at", 1)],
            "kwargs": {
                "expireAfterSeconds": 0,
                "partialFilterExpression": {"expires_at": {"$exists": True}},
            },
        },
    ],
    "token_blacklist": [
        {"fields": [("jti", 1)], "kwargs": {"unique": True}},
        {"fields": [("expires_at", 1)], "kwargs": {"expireAfterSeconds": 0}},
        {"fields": [("user_id", 1)]},
    ],
    "password_reset_tokens": [
        {"fields": [("token", 1)], "kwargs": {"unique": True}},
        {"fields": [("email", 1)]},
        {"fields": [("expires_at", 1)], "kwargs": {"expireAfterSeconds": 0}},
    ],
    "chat_history": [
        {"fields": [("user_id", 1), ("created_at", -1)]},
        {"fields": [("organization_id", 1), ("created_at", -1)]},
    ],
    "user_memory": [
        {"fields": [("user_id", 1)], "kwargs": {"unique": True}},
        {"fields": [("organization_id", 1)]},
        {"fields": [("updated_at", -1)]},
    ],
    "conversation_summaries": [
        {"fields": [("conversation_id", 1)], "kwargs": {"unique": True}},
        {"fields": [("user_id", 1), ("updated_at", -1)]},
    ],
    # ── Internal locks (used to serialize init_db across workers) ──
    "_init_locks": [
        {"fields": [("expires_at", 1)], "kwargs": {"expireAfterSeconds": 0}},
    ],
}

_BASELINE_LOIS = [
    {
        "code": "code_societes_fr",
        "name": "Code des sociétés commerciales",
        "language": "fr",
        "jurisdiction": "tunisia",
        "description": "Baseline legal corpus for Tunisian commercial company rules.",
    },
    {
        "code": "code de travail",
        "name": "Code du travail",
        "language": "fr",
        "jurisdiction": "tunisia",
        "description": "Baseline legal corpus for Tunisian labor rules.",
    },
]


def get_collection(name: str):
    """Return a Motor collection handle by name."""
    return mongo_db[name]


async def get_db() -> AsyncIterator[Any]:
    """Yield the shared MongoDB database handle."""
    yield mongo_db


async def _acquire_init_lock(lock_name: str, ttl_seconds: int = 120) -> bool:
    """
    Best-effort distributed lock backed by a unique index on `_init_locks._id`.
    Returns True if this worker won the race and should perform the work.
    """
    now = datetime.now(timezone.utc)
    try:
        await mongo_db["_init_locks"].insert_one(
            {
                "_id": lock_name,
                "acquired_at": now,
                "expires_at": now + timedelta(seconds=ttl_seconds),
            }
        )
        return True
    except DuplicateKeyError:
        return False


async def _release_init_lock(lock_name: str) -> None:
    try:
        await mongo_db["_init_locks"].delete_one({"_id": lock_name})
    except Exception:
        logger.warning("Failed to release init lock %s", lock_name, exc_info=True)


async def _ensure_indexes() -> None:
    for collection_name, index_specs in _COLLECTION_INDEXES.items():
        collection = mongo_db[collection_name]
        existing_indexes = await collection.index_information()
        for spec in index_specs:
            fields = spec["fields"]
            signature = tuple(fields)
            matching_name = None
            matching_index = None
            for index_name, index_info in existing_indexes.items():
                if tuple(index_info.get("key", [])) == signature:
                    matching_name = index_name
                    matching_index = index_info
                    break

            index_kwargs = spec.get("kwargs", {})
            if matching_name is not None:
                if not index_kwargs.get("unique") or matching_index.get("unique"):
                    continue

                group_id = {field_name: f"${field_name}" for field_name, _ in fields}
                cursor = collection.aggregate(
                    [
                        {"$group": {"_id": group_id, "count": {"$sum": 1}}},
                        {"$match": {"count": {"$gt": 1}}},
                        {"$limit": 1},
                    ]
                )
                duplicates = await cursor.to_list(length=1)
                if duplicates:
                    logger.error(
                        "Cannot enforce unique index on %s.%s — duplicates exist; "
                        "leaving existing non-unique index in place",
                        collection_name,
                        ".".join(name for name, _ in fields),
                    )
                    continue

                try:
                    await collection.drop_index(matching_name)
                except OperationFailure:
                    logger.warning(
                        "drop_index race on %s.%s — another worker likely won",
                        collection_name,
                        matching_name,
                    )

            try:
                await collection.create_index(fields, **index_kwargs)
            except OperationFailure as exc:
                # IndexOptionsConflict / IndexKeySpecsConflict are non-fatal at startup.
                logger.warning(
                    "create_index conflict on %s %s: %s",
                    collection_name,
                    fields,
                    exc,
                )


async def _seed_baseline_lois() -> None:
    """Atomically upsert baseline lois — safe under concurrent workers."""
    lois = mongo_db["lois"]
    for law in _BASELINE_LOIS:
        now = datetime.now(timezone.utc)
        try:
            await lois.update_one(
                {"code": law["code"]},
                {
                    "$setOnInsert": {
                        "id": law["code"],
                        **law,
                        "created_at": now,
                        "updated_at": now,
                    }
                },
                upsert=True,
            )
        except DuplicateKeyError:
            # Concurrent worker won the race — that's fine.
            continue


async def _ping_database() -> None:
    """Fail fast at startup if Mongo is unreachable."""
    await mongo_db.command("ping")


async def init_db() -> None:
    """Initialize MongoDB collections, indexes, and baseline data."""
    await _ping_database()

    lock_name = "init_db"
    acquired = await _acquire_init_lock(lock_name)
    if acquired:
        try:
            await _ensure_indexes()
            await _seed_baseline_lois()
        finally:
            await _release_init_lock(lock_name)
    else:
        logger.info("init_db: another worker holds the lock — skipping index/seed step")

    from app.services.auth_service import ensure_super_admin
    await ensure_super_admin()


async def close_db() -> None:
    """Close the shared Mongo client."""
    mongo_client.close()
