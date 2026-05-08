"""
MongoDB database helpers.

This module exposes a shared Motor client, the active database handle,
and startup initialization for collections and indexes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings

settings = get_settings()

mongo_client = AsyncIOMotorClient(settings.mongodb_url)
mongo_db = mongo_client[settings.mongodb_db_name]

_COLLECTION_INDEXES: dict[str, list[dict[str, Any]]] = {
    "documents": [
        {"fields": [("created_at", -1)]},
        {"fields": [("status", 1), ("created_at", -1)]},
        {"fields": [("language", 1), ("created_at", -1)]},
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
    ],
    "exigences": [
        {"fields": [("document_id", 1), ("page_number", 1)]},
        {"fields": [("document_id", 1), ("article_version_id", 1)]},
        {"fields": [("exigence_type", 1)]},
    ],
    "company_profiles": [
        {"fields": [("created_at", -1)]},
        {"fields": [("name", 1)]},
    ],
    "exigence_applicabilities": [
        {"fields": [("profile_id", 1), ("exigence_id", 1)]},
        {"fields": [("profile_id", 1), ("is_applicable", 1)]},
    ],
    "lois": [
        {"fields": [("code", 1)]},
        {"fields": [("created_at", -1)]},
    ],
    "articles": [
        {"fields": [("loi_id", 1), ("article_key", 1)]},
        {"fields": [("loi_id", 1), ("article_number", 1)]},
    ],
    "article_versions": [
        {"fields": [("article_id", 1), ("is_current", -1)]},
        {"fields": [("article_id", 1), ("version_number", -1)]},
    ],
    "actions": [
        {"fields": [("article_version_id", 1)]},
        {"fields": [("exigence_id", 1)]},
        {"fields": [("modalite", 1)]},
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
        {"fields": [("operation_type", 1)]},
        {"fields": [("status", 1)]},
    ],
    "audit_logs": [
        {"fields": [("created_at", -1)]},
        {"fields": [("entity_type", 1), ("entity_id", 1)]},
    ],
    "qa_feedback": [
        {"fields": [("created_at", -1)]},
        {"fields": [("language", 1), ("created_at", -1)]},
        {"fields": [("source_document_id", 1), ("created_at", -1)]},
    ],
    # ── Compliance Case Management ──
    "compliance_cases": [
        {"fields": [("created_at", -1)]},
        {"fields": [("status", 1), ("created_at", -1)]},
        {"fields": [("priority", 1), ("created_at", -1)]},
        {"fields": [("company_profile_id", 1)]},
    ],
    "case_messages": [
        {"fields": [("case_id", 1), ("created_at", 1)]},
    ],
    "case_documents": [
        {"fields": [("case_id", 1)]},
        {"fields": [("case_id", 1), ("document_id", 1)], "kwargs": {"unique": True}},
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


async def get_db() -> AsyncIterator[Any]:
    """Yield the shared MongoDB database handle."""
    yield mongo_db


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
                cursor = await collection.aggregate(
                    [
                        {"$group": {"_id": group_id, "count": {"$sum": 1}}},
                        {"$match": {"count": {"$gt": 1}}},
                        {"$limit": 1},
                    ]
                )
                duplicates = await cursor.to_list(length=1)
                if duplicates:
                    raise RuntimeError(
                        f"Cannot enforce unique index on {collection_name}.{'.'.join(name for name, _ in fields)} because duplicate values already exist"
                    )

                await collection.drop_index(matching_name)

            await collection.create_index(fields, **index_kwargs)


async def _seed_baseline_lois() -> None:
    lois = mongo_db["lois"]
    for law in _BASELINE_LOIS:
        existing = await lois.find_one({"code": law["code"]})
        if existing:
            continue
        now = datetime.now(timezone.utc)
        await lois.insert_one(
            {
                "id": law["code"],
                **law,
                "created_at": now,
                "updated_at": now,
            }
        )


async def init_db() -> None:
    """Initialize MongoDB collections, indexes, and baseline data."""
    await _ensure_indexes()
    await _seed_baseline_lois()


async def close_db() -> None:
    """Close the shared Mongo client."""
    mongo_client.close()
