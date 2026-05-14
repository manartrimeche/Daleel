"""
Case Service — Compliance Case Management.

CRUD operations for the five case-related collections:
  compliance_cases, case_messages, case_documents,
  case_findings, case_actions.

Follows the same module-level async-function pattern used by the existing
services (document_service, audit_service, action_service …).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.database import get_collection
from app.services import audit_service

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────
# Serialisers (Mongo doc → API-friendly dict)
# ─────────────────────────────────────────────────────────────

def _case_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "title": doc.get("title"),
        "description": doc.get("description"),
        "company_profile_id": doc.get("company_profile_id"),
        "status": doc.get("status"),
        "priority": doc.get("priority"),
        "assigned_to": doc.get("assigned_to"),
        "tags": doc.get("tags") or [],
        "created_by": doc.get("created_by"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "closed_at": doc.get("closed_at"),
        "message_count": doc.get("message_count", 0),
        "document_count": doc.get("document_count", 0),
        "finding_count": doc.get("finding_count", 0),
        "action_count": doc.get("action_count", 0),
    }


def _message_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "case_id": doc.get("case_id"),
        "role": doc.get("role"),
        "content": doc.get("content"),
        "metadata": doc.get("metadata"),
        "created_at": doc.get("created_at"),
    }


def _case_doc_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "case_id": doc.get("case_id"),
        "document_id": doc.get("document_id"),
        "label": doc.get("label"),
        "attached_by": doc.get("attached_by"),
        "attached_at": doc.get("attached_at"),
    }


def _finding_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "case_id": doc.get("case_id"),
        "exigence_id": doc.get("exigence_id"),
        "title": doc.get("title"),
        "description": doc.get("description"),
        "severity": doc.get("severity"),
        "status": doc.get("status"),
        "evidence_refs": doc.get("evidence_refs") or [],
        "article_references": doc.get("article_references") or [],
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _action_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "case_id": doc.get("case_id"),
        "finding_id": doc.get("finding_id"),
        "action_id": doc.get("action_id"),
        "title": doc.get("title"),
        "description": doc.get("description"),
        "assigned_to": doc.get("assigned_to"),
        "due_date": doc.get("due_date"),
        "status": doc.get("status"),
        "priority": doc.get("priority"),
        "completion_notes": doc.get("completion_notes"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "completed_at": doc.get("completed_at"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE CASES — CRUD
# ═══════════════════════════════════════════════════════════════════════════════

async def create_case(
    db,
    *,
    title: str,
    description: Optional[str] = None,
    company_profile_id: Optional[str] = None,
    priority: str = "medium",
    assigned_to: Optional[str] = None,
    tags: list[str] | None = None,
    created_by: str = "system",
) -> dict:
    """Create a new compliance case."""
    if company_profile_id:
        profile = await get_collection("company_profiles").find_one({"id": company_profile_id})
        if not profile:
            raise ValueError(f"Company profile '{company_profile_id}' not found")

    now = _now()
    case = {
        "id": _new_id(),
        "title": title,
        "description": description,
        "company_profile_id": company_profile_id,
        "status": "open",
        "priority": priority,
        "assigned_to": assigned_to,
        "tags": tags or [],
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
        "closed_at": None,
    }
    await get_collection("compliance_cases").insert_one(case)

    await audit_service.log_event(
        db,
        "case_created",
        actor=created_by,
        details={"case_id": case["id"], "title": title},
    )

    logger.info("Case created: id=%s title=%s", case["id"], title)
    return await _enrich_case(case)


async def get_case(db, case_id: str) -> dict | None:
    """Retrieve a single case by ID, enriched with sub-entity counts."""
    case = await get_collection("compliance_cases").find_one({"id": case_id})
    if not case:
        return None
    return await _enrich_case(case)


async def list_cases(
    db,
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    company_profile_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    """List cases with optional filters, newest first."""
    query: dict = {}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if company_profile_id:
        query["company_profile_id"] = company_profile_id

    total = await get_collection("compliance_cases").count_documents(query)
    cursor = (
        get_collection("compliance_cases")
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    cases = []
    async for doc in cursor:
        cases.append(await _enrich_case(doc))
    return cases, int(total)


async def update_case(
    db,
    case_id: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    company_profile_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict | None:
    """Partially update a case. Returns the updated case or None."""
    case = await get_collection("compliance_cases").find_one({"id": case_id})
    if not case:
        return None

    updates: dict = {"updated_at": _now()}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if company_profile_id is not None:
        updates["company_profile_id"] = company_profile_id
    if priority is not None:
        updates["priority"] = priority
    if assigned_to is not None:
        updates["assigned_to"] = assigned_to
    if tags is not None:
        updates["tags"] = tags

    if status is not None and status != case.get("status"):
        updates["status"] = status
        if status == "closed":
            updates["closed_at"] = _now()
        elif case.get("status") == "closed":
            updates["closed_at"] = None

    await get_collection("compliance_cases").update_one(
        {"id": case_id}, {"$set": updates}
    )

    await audit_service.log_event(
        db,
        "case_updated",
        details={"case_id": case_id, "fields_changed": list(updates.keys())},
    )

    return await get_case(db, case_id)


async def delete_case(db, case_id: str) -> bool:
    """Delete a case and all its sub-entities."""
    case = await get_collection("compliance_cases").find_one({"id": case_id})
    if not case:
        return False

    for coll in ("case_messages", "case_documents", "case_findings", "case_actions"):
        await get_collection(coll).delete_many({"case_id": case_id})

    await get_collection("compliance_cases").delete_one({"id": case_id})

    await audit_service.log_event(
        db,
        "case_deleted",
        details={"case_id": case_id, "title": case.get("title")},
    )

    logger.info("Case deleted: id=%s", case_id)
    return True


async def get_case_summary(db) -> dict:
    """Return aggregate counts across all cases."""
    total = await get_collection("compliance_cases").count_documents({})

    by_status: dict[str, int] = {}
    async for row in get_collection("compliance_cases").aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]):
        by_status[row["_id"]] = row["count"]

    by_priority: dict[str, int] = {}
    async for row in get_collection("compliance_cases").aggregate([
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}},
    ]):
        by_priority[row["_id"]] = row["count"]

    return {
        "total_cases": total,
        "by_status": by_status,
        "by_priority": by_priority,
    }


async def _enrich_case(case: dict) -> dict:
    """Add sub-entity counts to a case dict."""
    cid = case["id"]
    case["message_count"] = await get_collection("case_messages").count_documents({"case_id": cid})
    case["document_count"] = await get_collection("case_documents").count_documents({"case_id": cid})
    case["finding_count"] = await get_collection("case_findings").count_documents({"case_id": cid})
    case["action_count"] = await get_collection("case_actions").count_documents({"case_id": cid})
    return _case_to_dict(case)


# ═══════════════════════════════════════════════════════════════════════════════
# CASE MESSAGES
# ═══════════════════════════════════════════════════════════════════════════════

async def add_message(
    db,
    case_id: str,
    *,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    case = await get_collection("compliance_cases").find_one({"id": case_id})
    if not case:
        raise ValueError(f"Case '{case_id}' not found")

    msg = {
        "id": _new_id(),
        "case_id": case_id,
        "role": role,
        "content": content,
        "metadata": metadata,
        "created_at": _now(),
    }
    await get_collection("case_messages").insert_one(msg)
    await get_collection("compliance_cases").update_one(
        {"id": case_id}, {"$set": {"updated_at": _now()}}
    )
    return _message_to_dict(msg)


async def list_messages(
    db,
    case_id: str,
    skip: int = 0,
    limit: int = 200,
) -> tuple[list[dict], int]:
    query = {"case_id": case_id}
    total = await get_collection("case_messages").count_documents(query)
    cursor = (
        get_collection("case_messages")
        .find(query)
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
    )
    messages = [_message_to_dict(doc) async for doc in cursor]
    return messages, int(total)


# ═══════════════════════════════════════════════════════════════════════════════
# CASE DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def attach_document(
    db,
    case_id: str,
    *,
    document_id: str,
    label: Optional[str] = None,
    attached_by: str = "system",
) -> dict:
    case = await get_collection("compliance_cases").find_one({"id": case_id})
    if not case:
        raise ValueError(f"Case '{case_id}' not found")

    doc = await get_collection("documents").find_one({"id": document_id})
    if not doc:
        raise ValueError(f"Document '{document_id}' not found")

    existing = await get_collection("case_documents").find_one(
        {"case_id": case_id, "document_id": document_id}
    )
    if existing:
        raise ValueError(f"Document '{document_id}' already attached to case '{case_id}'")

    case_doc = {
        "id": _new_id(),
        "case_id": case_id,
        "document_id": document_id,
        "label": label,
        "attached_by": attached_by,
        "attached_at": _now(),
    }
    await get_collection("case_documents").insert_one(case_doc)
    await get_collection("compliance_cases").update_one(
        {"id": case_id}, {"$set": {"updated_at": _now()}}
    )
    return _case_doc_to_dict(case_doc)


async def list_case_documents(
    db,
    case_id: str,
) -> tuple[list[dict], int]:
    query = {"case_id": case_id}
    total = await get_collection("case_documents").count_documents(query)
    cursor = get_collection("case_documents").find(query).sort("attached_at", -1)
    docs = [_case_doc_to_dict(d) async for d in cursor]
    return docs, int(total)


async def detach_document(db, case_id: str, case_document_id: str) -> bool:
    result = await get_collection("case_documents").delete_one(
        {"id": case_document_id, "case_id": case_id}
    )
    if result.deleted_count:
        await get_collection("compliance_cases").update_one(
            {"id": case_id}, {"$set": {"updated_at": _now()}}
        )
    return result.deleted_count > 0


# ═══════════════════════════════════════════════════════════════════════════════
# CASE FINDINGS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_finding(
    db,
    case_id: str,
    *,
    title: str,
    description: str,
    severity: str = "major",
    exigence_id: Optional[str] = None,
    evidence_refs: list[str] | None = None,
    article_references: list[str] | None = None,
) -> dict:
    case = await get_collection("compliance_cases").find_one({"id": case_id})
    if not case:
        raise ValueError(f"Case '{case_id}' not found")

    if exigence_id:
        exigence = await get_collection("exigences").find_one({"id": exigence_id})
        if not exigence:
            raise ValueError(f"Exigence '{exigence_id}' not found")

    now = _now()
    finding = {
        "id": _new_id(),
        "case_id": case_id,
        "exigence_id": exigence_id,
        "title": title,
        "description": description,
        "severity": severity,
        "status": "identified",
        "evidence_refs": evidence_refs or [],
        "article_references": article_references or [],
        "created_at": now,
        "updated_at": now,
    }
    await get_collection("case_findings").insert_one(finding)
    await get_collection("compliance_cases").update_one(
        {"id": case_id}, {"$set": {"updated_at": now}}
    )
    return _finding_to_dict(finding)


async def update_finding(
    db,
    case_id: str,
    finding_id: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    evidence_refs: Optional[list[str]] = None,
    article_references: Optional[list[str]] = None,
) -> dict | None:
    finding = await get_collection("case_findings").find_one(
        {"id": finding_id, "case_id": case_id}
    )
    if not finding:
        return None

    updates: dict = {"updated_at": _now()}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if severity is not None:
        updates["severity"] = severity
    if status is not None:
        updates["status"] = status
    if evidence_refs is not None:
        updates["evidence_refs"] = evidence_refs
    if article_references is not None:
        updates["article_references"] = article_references

    await get_collection("case_findings").update_one(
        {"id": finding_id}, {"$set": updates}
    )

    updated = await get_collection("case_findings").find_one({"id": finding_id})
    return _finding_to_dict(updated) if updated else None


async def list_findings(
    db,
    case_id: str,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
) -> tuple[list[dict], int, dict, dict]:
    """Returns (findings, total, by_severity, by_status)."""
    query: dict = {"case_id": case_id}
    if severity:
        query["severity"] = severity
    if status:
        query["status"] = status

    total = await get_collection("case_findings").count_documents(query)
    cursor = (
        get_collection("case_findings")
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    findings = [_finding_to_dict(d) async for d in cursor]

    base_query = {"case_id": case_id}
    by_severity: dict[str, int] = {}
    async for row in get_collection("case_findings").aggregate([
        {"$match": base_query},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
    ]):
        by_severity[row["_id"]] = row["count"]

    by_status: dict[str, int] = {}
    async for row in get_collection("case_findings").aggregate([
        {"$match": base_query},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]):
        by_status[row["_id"]] = row["count"]

    return findings, int(total), by_severity, by_status


# ═══════════════════════════════════════════════════════════════════════════════
# CASE ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_case_action(
    db,
    case_id: str,
    *,
    title: str,
    description: str,
    finding_id: Optional[str] = None,
    action_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    due_date: Optional[datetime] = None,
    priority: str = "medium",
) -> dict:
    case = await get_collection("compliance_cases").find_one({"id": case_id})
    if not case:
        raise ValueError(f"Case '{case_id}' not found")

    if finding_id:
        finding = await get_collection("case_findings").find_one(
            {"id": finding_id, "case_id": case_id}
        )
        if not finding:
            raise ValueError(f"Finding '{finding_id}' not found in case '{case_id}'")

    if action_id:
        action = await get_collection("actions").find_one({"id": action_id})
        if not action:
            raise ValueError(f"Action '{action_id}' not found")

    now = _now()
    case_action = {
        "id": _new_id(),
        "case_id": case_id,
        "finding_id": finding_id,
        "action_id": action_id,
        "title": title,
        "description": description,
        "assigned_to": assigned_to,
        "due_date": due_date,
        "status": "pending",
        "priority": priority,
        "completion_notes": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }
    await get_collection("case_actions").insert_one(case_action)
    await get_collection("compliance_cases").update_one(
        {"id": case_id}, {"$set": {"updated_at": now}}
    )
    return _action_to_dict(case_action)


async def update_case_action(
    db,
    case_id: str,
    case_action_id: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    due_date: Optional[datetime] = None,
    priority: Optional[str] = None,
    completion_notes: Optional[str] = None,
) -> dict | None:
    action = await get_collection("case_actions").find_one(
        {"id": case_action_id, "case_id": case_id}
    )
    if not action:
        return None

    updates: dict = {"updated_at": _now()}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if assigned_to is not None:
        updates["assigned_to"] = assigned_to
    if due_date is not None:
        updates["due_date"] = due_date
    if priority is not None:
        updates["priority"] = priority
    if completion_notes is not None:
        updates["completion_notes"] = completion_notes

    if status is not None and status != action.get("status"):
        updates["status"] = status
        if status == "completed":
            updates["completed_at"] = _now()
        elif action.get("status") == "completed":
            updates["completed_at"] = None

    await get_collection("case_actions").update_one(
        {"id": case_action_id}, {"$set": updates}
    )

    updated = await get_collection("case_actions").find_one({"id": case_action_id})
    return _action_to_dict(updated) if updated else None


async def list_case_actions(
    db,
    case_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
) -> tuple[list[dict], int, dict, dict]:
    """Returns (actions, total, by_status, by_priority)."""
    query: dict = {"case_id": case_id}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority

    total = await get_collection("case_actions").count_documents(query)
    cursor = (
        get_collection("case_actions")
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    actions = [_action_to_dict(d) async for d in cursor]

    base_query = {"case_id": case_id}
    by_status: dict[str, int] = {}
    async for row in get_collection("case_actions").aggregate([
        {"$match": base_query},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]):
        by_status[row["_id"]] = row["count"]

    by_priority: dict[str, int] = {}
    async for row in get_collection("case_actions").aggregate([
        {"$match": base_query},
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}},
    ]):
        by_priority[row["_id"]] = row["count"]

    return actions, int(total), by_status, by_priority
