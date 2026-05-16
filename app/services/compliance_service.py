"""
Compliance Steering Service — gap analysis, control mapping, evidence
management, and remediation tracking.

Collections managed:
  compliance_assessments, controls, control_evidences,
  requirement_control_links, exception_register.

Follows the same module-level async-function pattern used by case_service,
audit_service, etc.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.database import get_collection
from app.services import audit_service

logger = logging.getLogger(__name__)
_collection = get_collection


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

def _assessment_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "company_profile_id": doc.get("company_profile_id"),
        "title": doc.get("title"),
        "description": doc.get("description"),
        "assessment_type": doc.get("assessment_type"),
        "status": doc.get("status"),
        "owner": doc.get("owner"),
        "risk_level": doc.get("risk_level"),
        "overall_coverage_score": doc.get("overall_coverage_score", 0.0),
        "review_frequency": doc.get("review_frequency"),
        "due_date": doc.get("due_date"),
        "completed_at": doc.get("completed_at"),
        "created_by": doc.get("created_by"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "link_count": doc.get("link_count", 0),
    }


def _control_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "company_profile_id": doc.get("company_profile_id"),
        "title": doc.get("title"),
        "description": doc.get("description"),
        "control_type": doc.get("control_type"),
        "implementation_status": doc.get("implementation_status"),
        "owner": doc.get("owner"),
        "risk_level": doc.get("risk_level"),
        "effectiveness_score": doc.get("effectiveness_score", 0.0),
        "review_frequency": doc.get("review_frequency"),
        "last_reviewed_at": doc.get("last_reviewed_at"),
        "next_review_date": doc.get("next_review_date"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "evidence_count": doc.get("evidence_count", 0),
        "linked_requirement_count": doc.get("linked_requirement_count", 0),
    }


def _evidence_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "control_id": doc.get("control_id"),
        "title": doc.get("title"),
        "description": doc.get("description"),
        "evidence_type": doc.get("evidence_type"),
        "file_reference": doc.get("file_reference"),
        "document_id": doc.get("document_id"),
        "collected_by": doc.get("collected_by"),
        "collected_at": doc.get("collected_at"),
        "valid_from": doc.get("valid_from"),
        "valid_until": doc.get("valid_until"),
        "status": doc.get("status"),
        "review_notes": doc.get("review_notes"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _link_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "exigence_id": doc.get("exigence_id"),
        "control_id": doc.get("control_id"),
        "assessment_id": doc.get("assessment_id"),
        "coverage_status": doc.get("coverage_status"),
        "coverage_score": doc.get("coverage_score", 0.0),
        "gap_description": doc.get("gap_description"),
        "justification": doc.get("justification"),
        "linked_by": doc.get("linked_by"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _exception_to_dict(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "exigence_id": doc.get("exigence_id"),
        "company_profile_id": doc.get("company_profile_id"),
        "control_id": doc.get("control_id"),
        "title": doc.get("title"),
        "description": doc.get("description"),
        "exception_type": doc.get("exception_type"),
        "status": doc.get("status"),
        "risk_level": doc.get("risk_level"),
        "justification": doc.get("justification"),
        "approved_by": doc.get("approved_by"),
        "approval_date": doc.get("approval_date"),
        "expiry_date": doc.get("expiry_date"),
        "remediation_action_id": doc.get("remediation_action_id"),
        "review_frequency": doc.get("review_frequency"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE ASSESSMENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_assessment(
    db,
    *,
    company_profile_id: str,
    title: str,
    description: Optional[str] = None,
    assessment_type: str = "initial",
    owner: Optional[str] = None,
    risk_level: str = "medium",
    review_frequency: str = "annual",
    due_date: Optional[datetime] = None,
    created_by: str = "system",
) -> dict:
    profile = await _collection("company_profiles").find_one(
        {"id": company_profile_id}
    )
    if not profile:
        raise ValueError(
            f"Company profile '{company_profile_id}' not found"
        )

    now = _now()
    assessment = {
        "id": _new_id(),
        "company_profile_id": company_profile_id,
        "title": title,
        "description": description,
        "assessment_type": assessment_type,
        "status": "draft",
        "owner": owner,
        "risk_level": risk_level,
        "overall_coverage_score": 0.0,
        "review_frequency": review_frequency,
        "due_date": due_date,
        "completed_at": None,
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
    }
    await _collection("compliance_assessments").insert_one(assessment)

    await audit_service.log_event(
        db,
        "assessment_created",
        actor=created_by,
        details={
            "assessment_id": assessment["id"],
            "company_profile_id": company_profile_id,
            "title": title,
        },
    )

    logger.info(
        "Assessment created: id=%s title=%s", assessment["id"], title
    )
    return await _enrich_assessment(assessment)


async def get_assessment(db, assessment_id: str) -> dict | None:
    doc = await _collection("compliance_assessments").find_one(
        {"id": assessment_id}
    )
    if not doc:
        return None
    return await _enrich_assessment(doc)


async def list_assessments(
    db,
    *,
    company_profile_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    query: dict = {}
    if company_profile_id:
        query["company_profile_id"] = company_profile_id
    if status:
        query["status"] = status

    total = await _collection("compliance_assessments").count_documents(query)
    cursor = (
        _collection("compliance_assessments")
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    results = []
    async for doc in cursor:
        results.append(await _enrich_assessment(doc))
    return results, int(total)


async def update_assessment(
    db,
    assessment_id: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    risk_level: Optional[str] = None,
    review_frequency: Optional[str] = None,
    due_date: Optional[datetime] = None,
) -> dict | None:
    doc = await _collection("compliance_assessments").find_one(
        {"id": assessment_id}
    )
    if not doc:
        return None

    updates: dict = {"updated_at": _now()}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if owner is not None:
        updates["owner"] = owner
    if risk_level is not None:
        updates["risk_level"] = risk_level
    if review_frequency is not None:
        updates["review_frequency"] = review_frequency
    if due_date is not None:
        updates["due_date"] = due_date

    if status is not None and status != doc.get("status"):
        updates["status"] = status
        if status == "completed":
            updates["completed_at"] = _now()
        elif doc.get("status") == "completed":
            updates["completed_at"] = None

    await _collection("compliance_assessments").update_one(
        {"id": assessment_id}, {"$set": updates}
    )

    return await get_assessment(db, assessment_id)


async def _enrich_assessment(doc: dict) -> dict:
    aid = doc["id"]
    doc["link_count"] = await _collection(
        "requirement_control_links"
    ).count_documents({"assessment_id": aid})
    return _assessment_to_dict(doc)


# ═══════════════════════════════════════════════════════════════════════════════
# CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_control(
    db,
    *,
    company_profile_id: str,
    title: str,
    description: str,
    control_type: str = "preventive",
    owner: Optional[str] = None,
    risk_level: str = "medium",
    review_frequency: str = "quarterly",
) -> dict:
    profile = await _collection("company_profiles").find_one(
        {"id": company_profile_id}
    )
    if not profile:
        raise ValueError(
            f"Company profile '{company_profile_id}' not found"
        )

    now = _now()
    control = {
        "id": _new_id(),
        "company_profile_id": company_profile_id,
        "title": title,
        "description": description,
        "control_type": control_type,
        "implementation_status": "planned",
        "owner": owner,
        "risk_level": risk_level,
        "effectiveness_score": 0.0,
        "review_frequency": review_frequency,
        "last_reviewed_at": None,
        "next_review_date": None,
        "created_at": now,
        "updated_at": now,
    }
    await _collection("controls").insert_one(control)

    await audit_service.log_event(
        db,
        "control_created",
        actor="system",
        details={
            "control_id": control["id"],
            "company_profile_id": company_profile_id,
            "title": title,
        },
    )

    logger.info("Control created: id=%s title=%s", control["id"], title)
    return await _enrich_control(control)


async def get_control(db, control_id: str) -> dict | None:
    doc = await _collection("controls").find_one({"id": control_id})
    if not doc:
        return None
    return await _enrich_control(doc)


async def list_controls(
    db,
    *,
    company_profile_id: Optional[str] = None,
    implementation_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    query: dict = {}
    if company_profile_id:
        query["company_profile_id"] = company_profile_id
    if implementation_status:
        query["implementation_status"] = implementation_status

    total = await _collection("controls").count_documents(query)
    cursor = (
        _collection("controls")
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    results = []
    async for doc in cursor:
        results.append(await _enrich_control(doc))
    return results, int(total)


async def update_control(
    db,
    control_id: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    control_type: Optional[str] = None,
    implementation_status: Optional[str] = None,
    owner: Optional[str] = None,
    risk_level: Optional[str] = None,
    effectiveness_score: Optional[float] = None,
    review_frequency: Optional[str] = None,
    last_reviewed_at: Optional[datetime] = None,
    next_review_date: Optional[datetime] = None,
) -> dict | None:
    doc = await _collection("controls").find_one({"id": control_id})
    if not doc:
        return None

    updates: dict = {"updated_at": _now()}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if control_type is not None:
        updates["control_type"] = control_type
    if implementation_status is not None:
        updates["implementation_status"] = implementation_status
    if owner is not None:
        updates["owner"] = owner
    if risk_level is not None:
        updates["risk_level"] = risk_level
    if effectiveness_score is not None:
        updates["effectiveness_score"] = max(0.0, min(1.0, effectiveness_score))
    if review_frequency is not None:
        updates["review_frequency"] = review_frequency
    if last_reviewed_at is not None:
        updates["last_reviewed_at"] = last_reviewed_at
    if next_review_date is not None:
        updates["next_review_date"] = next_review_date

    await _collection("controls").update_one(
        {"id": control_id}, {"$set": updates}
    )
    return await get_control(db, control_id)


async def _enrich_control(doc: dict) -> dict:
    cid = doc["id"]
    doc["evidence_count"] = await _collection(
        "control_evidences"
    ).count_documents({"control_id": cid})
    doc["linked_requirement_count"] = await _collection(
        "requirement_control_links"
    ).count_documents({"control_id": cid})
    return _control_to_dict(doc)


# ═══════════════════════════════════════════════════════════════════════════════
# CONTROL EVIDENCES
# ═══════════════════════════════════════════════════════════════════════════════

async def create_evidence(
    db,
    control_id: str,
    *,
    title: str,
    description: Optional[str] = None,
    evidence_type: str = "document",
    file_reference: Optional[str] = None,
    document_id: Optional[str] = None,
    collected_by: str = "system",
    collected_at: Optional[datetime] = None,
    valid_from: Optional[datetime] = None,
    valid_until: Optional[datetime] = None,
) -> dict:
    control = await _collection("controls").find_one({"id": control_id})
    if not control:
        raise ValueError(f"Control '{control_id}' not found")

    if document_id:
        doc_exists = await _collection("documents").find_one(
            {"id": document_id}
        )
        if not doc_exists:
            raise ValueError(f"Document '{document_id}' not found")

    now = _now()
    evidence = {
        "id": _new_id(),
        "control_id": control_id,
        "title": title,
        "description": description,
        "evidence_type": evidence_type,
        "file_reference": file_reference,
        "document_id": document_id,
        "collected_by": collected_by,
        "collected_at": collected_at or now,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "status": "pending",
        "review_notes": None,
        "created_at": now,
        "updated_at": now,
    }
    await _collection("control_evidences").insert_one(evidence)

    logger.info(
        "Evidence created: id=%s control=%s", evidence["id"], control_id
    )
    return _evidence_to_dict(evidence)


async def list_evidences(
    db,
    control_id: str,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[dict], int]:
    query = {"control_id": control_id}
    total = await _collection("control_evidences").count_documents(query)
    cursor = (
        _collection("control_evidences")
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    results = [_evidence_to_dict(d) async for d in cursor]
    return results, int(total)


async def update_evidence(
    db,
    evidence_id: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    review_notes: Optional[str] = None,
    valid_from: Optional[datetime] = None,
    valid_until: Optional[datetime] = None,
) -> dict | None:
    doc = await _collection("control_evidences").find_one(
        {"id": evidence_id}
    )
    if not doc:
        return None

    updates: dict = {"updated_at": _now()}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if status is not None:
        updates["status"] = status
    if review_notes is not None:
        updates["review_notes"] = review_notes
    if valid_from is not None:
        updates["valid_from"] = valid_from
    if valid_until is not None:
        updates["valid_until"] = valid_until

    await _collection("control_evidences").update_one(
        {"id": evidence_id}, {"$set": updates}
    )
    updated = await _collection("control_evidences").find_one(
        {"id": evidence_id}
    )
    return _evidence_to_dict(updated) if updated else None


# ═══════════════════════════════════════════════════════════════════════════════
# REQUIREMENT–CONTROL LINKS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_link(
    db,
    *,
    exigence_id: str,
    control_id: str,
    assessment_id: Optional[str] = None,
    coverage_status: str = "not_covered",
    coverage_score: float = 0.0,
    gap_description: Optional[str] = None,
    justification: Optional[str] = None,
    linked_by: str = "system",
) -> dict:
    exigence = await _collection("exigences").find_one({"id": exigence_id})
    if not exigence:
        raise ValueError(f"Exigence '{exigence_id}' not found")

    control = await _collection("controls").find_one({"id": control_id})
    if not control:
        raise ValueError(f"Control '{control_id}' not found")

    if assessment_id:
        assessment = await _collection("compliance_assessments").find_one(
            {"id": assessment_id}
        )
        if not assessment:
            raise ValueError(f"Assessment '{assessment_id}' not found")

    existing = await _collection("requirement_control_links").find_one({
        "exigence_id": exigence_id,
        "control_id": control_id,
        "assessment_id": assessment_id,
    })
    if existing:
        raise ValueError(
            f"Link already exists between exigence '{exigence_id}' "
            f"and control '{control_id}' "
            f"(assessment={assessment_id})"
        )

    now = _now()
    link = {
        "id": _new_id(),
        "exigence_id": exigence_id,
        "control_id": control_id,
        "assessment_id": assessment_id,
        "coverage_status": coverage_status,
        "coverage_score": max(0.0, min(1.0, coverage_score)),
        "gap_description": gap_description,
        "justification": justification,
        "linked_by": linked_by,
        "created_at": now,
        "updated_at": now,
    }
    await _collection("requirement_control_links").insert_one(link)

    logger.info(
        "Req-control link created: id=%s exigence=%s control=%s",
        link["id"], exigence_id, control_id,
    )
    return _link_to_dict(link)


async def list_links(
    db,
    *,
    exigence_id: Optional[str] = None,
    control_id: Optional[str] = None,
    assessment_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
) -> tuple[list[dict], int]:
    query: dict = {}
    if exigence_id:
        query["exigence_id"] = exigence_id
    if control_id:
        query["control_id"] = control_id
    if assessment_id:
        query["assessment_id"] = assessment_id

    total = await _collection("requirement_control_links").count_documents(
        query
    )
    cursor = (
        _collection("requirement_control_links")
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    results = [_link_to_dict(d) async for d in cursor]
    return results, int(total)


async def update_link(
    db,
    link_id: str,
    *,
    coverage_status: Optional[str] = None,
    coverage_score: Optional[float] = None,
    gap_description: Optional[str] = None,
    justification: Optional[str] = None,
) -> dict | None:
    doc = await _collection("requirement_control_links").find_one(
        {"id": link_id}
    )
    if not doc:
        return None

    updates: dict = {"updated_at": _now()}
    if coverage_status is not None:
        updates["coverage_status"] = coverage_status
    if coverage_score is not None:
        updates["coverage_score"] = max(0.0, min(1.0, coverage_score))
    if gap_description is not None:
        updates["gap_description"] = gap_description
    if justification is not None:
        updates["justification"] = justification

    await _collection("requirement_control_links").update_one(
        {"id": link_id}, {"$set": updates}
    )
    updated = await _collection("requirement_control_links").find_one(
        {"id": link_id}
    )
    return _link_to_dict(updated) if updated else None


async def delete_link(db, link_id: str) -> bool:
    result = await _collection("requirement_control_links").delete_one(
        {"id": link_id}
    )
    return result.deleted_count > 0


# ═══════════════════════════════════════════════════════════════════════════════
# EXCEPTION REGISTER
# ═══════════════════════════════════════════════════════════════════════════════

async def create_exception(
    db,
    *,
    exigence_id: str,
    company_profile_id: str,
    control_id: Optional[str] = None,
    title: str,
    description: str,
    exception_type: str = "risk_acceptance",
    risk_level: str = "medium",
    justification: str,
    expiry_date: Optional[datetime] = None,
    remediation_action_id: Optional[str] = None,
    review_frequency: str = "quarterly",
) -> dict:
    exigence = await _collection("exigences").find_one({"id": exigence_id})
    if not exigence:
        raise ValueError(f"Exigence '{exigence_id}' not found")

    profile = await _collection("company_profiles").find_one(
        {"id": company_profile_id}
    )
    if not profile:
        raise ValueError(
            f"Company profile '{company_profile_id}' not found"
        )

    if control_id:
        ctrl = await _collection("controls").find_one({"id": control_id})
        if not ctrl:
            raise ValueError(f"Control '{control_id}' not found")

    now = _now()
    exc = {
        "id": _new_id(),
        "exigence_id": exigence_id,
        "company_profile_id": company_profile_id,
        "control_id": control_id,
        "title": title,
        "description": description,
        "exception_type": exception_type,
        "status": "requested",
        "risk_level": risk_level,
        "justification": justification,
        "approved_by": None,
        "approval_date": None,
        "expiry_date": expiry_date,
        "remediation_action_id": remediation_action_id,
        "review_frequency": review_frequency,
        "created_at": now,
        "updated_at": now,
    }
    await _collection("exception_register").insert_one(exc)

    await audit_service.log_event(
        db,
        "exception_created",
        actor="system",
        details={
            "exception_id": exc["id"],
            "exigence_id": exigence_id,
            "company_profile_id": company_profile_id,
            "exception_type": exception_type,
        },
    )

    logger.info("Exception created: id=%s title=%s", exc["id"], title)
    return _exception_to_dict(exc)


async def list_exceptions(
    db,
    *,
    company_profile_id: Optional[str] = None,
    status: Optional[str] = None,
    exigence_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    query: dict = {}
    if company_profile_id:
        query["company_profile_id"] = company_profile_id
    if status:
        query["status"] = status
    if exigence_id:
        query["exigence_id"] = exigence_id

    total = await _collection("exception_register").count_documents(query)
    cursor = (
        _collection("exception_register")
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    results = [_exception_to_dict(d) async for d in cursor]
    return results, int(total)


async def update_exception(
    db,
    exception_id: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    justification: Optional[str] = None,
    approved_by: Optional[str] = None,
    expiry_date: Optional[datetime] = None,
    remediation_action_id: Optional[str] = None,
) -> dict | None:
    doc = await _collection("exception_register").find_one(
        {"id": exception_id}
    )
    if not doc:
        return None

    updates: dict = {"updated_at": _now()}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if risk_level is not None:
        updates["risk_level"] = risk_level
    if justification is not None:
        updates["justification"] = justification
    if expiry_date is not None:
        updates["expiry_date"] = expiry_date
    if remediation_action_id is not None:
        updates["remediation_action_id"] = remediation_action_id

    if status is not None and status != doc.get("status"):
        updates["status"] = status
        if status == "approved" and approved_by:
            updates["approved_by"] = approved_by
            updates["approval_date"] = _now()

    if approved_by is not None and "approved_by" not in updates:
        updates["approved_by"] = approved_by

    await _collection("exception_register").update_one(
        {"id": exception_id}, {"$set": updates}
    )

    updated = await _collection("exception_register").find_one(
        {"id": exception_id}
    )
    return _exception_to_dict(updated) if updated else None


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE POSTURE / GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

async def compute_posture(
    db, company_profile_id: str, *, assessment_id: Optional[str] = None
) -> dict:
    """
    Compute the full compliance posture for a company profile.

    Algorithm:
      1. Fetch all applicable exigence IDs (exigence_applicabilities).
      2. For each exigence, find requirement_control_links.
      3. Determine coverage status per exigence.
      4. Check exception_register for approved exceptions.
      5. Compute overall coverage score.
    """
    profile = await _collection("company_profiles").find_one(
        {"id": company_profile_id}
    )
    if not profile:
        raise ValueError(
            f"Company profile '{company_profile_id}' not found"
        )

    applicable_cursor = _collection("exigence_applicabilities").find(
        {"profile_id": company_profile_id, "is_applicable": True}
    )
    applicable_exigence_ids: list[str] = []
    async for app_doc in applicable_cursor:
        applicable_exigence_ids.append(app_doc["exigence_id"])

    if not applicable_exigence_ids:
        return {
            "company_profile_id": company_profile_id,
            "total_applicable": 0,
            "fully_covered": 0,
            "partially_covered": 0,
            "not_covered": 0,
            "excepted": 0,
            "overall_coverage_score": 1.0,
            "gaps": [],
        }

    approved_exceptions: set[str] = set()
    exc_cursor = _collection("exception_register").find({
        "company_profile_id": company_profile_id,
        "status": "approved",
    })
    async for exc_doc in exc_cursor:
        approved_exceptions.add(exc_doc["exigence_id"])

    link_query: dict = {
        "exigence_id": {"$in": applicable_exigence_ids},
    }
    if assessment_id:
        link_query["assessment_id"] = assessment_id

    links_by_exigence: dict[str, list[dict]] = {}
    link_cursor = _collection("requirement_control_links").find(link_query)
    async for link_doc in link_cursor:
        eid = link_doc["exigence_id"]
        links_by_exigence.setdefault(eid, []).append(link_doc)

    fully_covered = 0
    partially_covered = 0
    not_covered = 0
    excepted = 0
    gaps: list[dict] = []

    for eid in applicable_exigence_ids:
        if eid in approved_exceptions:
            excepted += 1
            continue

        links = links_by_exigence.get(eid, [])
        if not links:
            not_covered += 1
            exigence_doc = await _collection("exigences").find_one(
                {"id": eid}
            )
            gaps.append({
                "exigence_id": eid,
                "exigence_title": (
                    exigence_doc.get("title") if exigence_doc else None
                ),
                "coverage_status": "not_covered",
                "best_coverage_score": 0.0,
                "linked_controls": 0,
                "has_exception": False,
            })
            continue

        best_status = "not_covered"
        best_score = 0.0
        for lnk in links:
            score = lnk.get("coverage_score", 0.0)
            if score > best_score:
                best_score = score
            if lnk.get("coverage_status") == "fully_covered":
                best_status = "fully_covered"
            elif (
                lnk.get("coverage_status") == "partially_covered"
                and best_status != "fully_covered"
            ):
                best_status = "partially_covered"

        if best_status == "fully_covered":
            fully_covered += 1
        else:
            if best_status == "partially_covered":
                partially_covered += 1
            else:
                not_covered += 1

            exigence_doc = await _collection("exigences").find_one(
                {"id": eid}
            )
            gaps.append({
                "exigence_id": eid,
                "exigence_title": (
                    exigence_doc.get("title") if exigence_doc else None
                ),
                "coverage_status": best_status,
                "best_coverage_score": best_score,
                "linked_controls": len(links),
                "has_exception": False,
            })

    total = len(applicable_exigence_ids)
    covered_count = fully_covered + excepted
    score = covered_count / total if total > 0 else 1.0

    if assessment_id:
        await _collection("compliance_assessments").update_one(
            {"id": assessment_id},
            {"$set": {
                "overall_coverage_score": round(score, 4),
                "updated_at": _now(),
            }},
        )

    return {
        "company_profile_id": company_profile_id,
        "total_applicable": total,
        "fully_covered": fully_covered,
        "partially_covered": partially_covered,
        "not_covered": not_covered,
        "excepted": excepted,
        "overall_coverage_score": round(score, 4),
        "gaps": gaps,
    }


async def list_gaps(
    db, company_profile_id: str, *, assessment_id: Optional[str] = None
) -> list[dict]:
    """Return only the gaps (not_covered + partially_covered requirements)."""
    posture = await compute_posture(
        db, company_profile_id, assessment_id=assessment_id
    )
    return posture["gaps"]


# ═══════════════════════════════════════════════════════════════════════════════
# REMEDIATION ACTIONS (bridges to existing 'actions' collection)
# ═══════════════════════════════════════════════════════════════════════════════

async def create_remediation_action(
    db,
    *,
    title: str,
    description: str,
    company_profile_id: str,
    exigence_id: Optional[str] = None,
    exception_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    due_date: Optional[datetime] = None,
    priority: str = "medium",
) -> dict:
    """
    Create a remediation action and optionally link it to an exception.
    Stored in the existing 'actions' collection with modalite='remediation'.
    """
    profile = await _collection("company_profiles").find_one(
        {"id": company_profile_id}
    )
    if not profile:
        raise ValueError(
            f"Company profile '{company_profile_id}' not found"
        )

    now = _now()
    action = {
        "id": _new_id(),
        "title": title,
        "description": description,
        "company_profile_id": company_profile_id,
        "exigence_id": exigence_id,
        "modalite": "remediation",
        "assigned_to": assigned_to,
        "due_date": due_date,
        "status": "pending",
        "priority": priority,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }
    await _collection("actions").insert_one(action)

    if exception_id:
        await _collection("exception_register").update_one(
            {"id": exception_id},
            {"$set": {
                "remediation_action_id": action["id"],
                "updated_at": now,
            }},
        )

    await audit_service.log_event(
        db,
        "remediation_action_created",
        actor="system",
        details={
            "action_id": action["id"],
            "company_profile_id": company_profile_id,
            "exigence_id": exigence_id,
            "exception_id": exception_id,
        },
    )

    logger.info(
        "Remediation action created: id=%s title=%s", action["id"], title
    )
    return {
        "id": action["id"],
        "title": action["title"],
        "description": action["description"],
        "company_profile_id": action["company_profile_id"],
        "exigence_id": action["exigence_id"],
        "modalite": action["modalite"],
        "assigned_to": action["assigned_to"],
        "due_date": action["due_date"],
        "status": action["status"],
        "priority": action["priority"],
        "created_at": action["created_at"],
        "updated_at": action["updated_at"],
    }
