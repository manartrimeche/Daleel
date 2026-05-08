"""
FastAPI routes for the Compliance Steering module.

Prefix: /api/v1/compliance
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import require_api_key
from app.compliance_schemas import (
    AssessmentCreate,
    AssessmentListOut,
    AssessmentOut,
    AssessmentUpdate,
    CompliancePosture,
    ControlCreate,
    ControlListOut,
    ControlOut,
    ControlUpdate,
    EvidenceCreate,
    EvidenceListOut,
    EvidenceOut,
    EvidenceUpdate,
    ExceptionCreate,
    ExceptionListOut,
    ExceptionOut,
    ExceptionUpdate,
    RemediationActionCreate,
    ReqControlLinkCreate,
    ReqControlLinkListOut,
    ReqControlLinkOut,
    ReqControlLinkUpdate,
    RequirementGap,
)
from app.database import get_db
from app.services import compliance_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compliance", tags=["compliance"])


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE ASSESSMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/assessments", response_model=AssessmentOut, status_code=201)
async def create_assessment(
    body: AssessmentCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Create a new compliance assessment (gap analysis exercise)."""
    try:
        return await compliance_service.create_assessment(
            db,
            company_profile_id=body.company_profile_id,
            title=body.title,
            description=body.description,
            assessment_type=body.assessment_type,
            owner=body.owner,
            risk_level=body.risk_level,
            review_frequency=body.review_frequency,
            due_date=body.due_date,
            created_by=body.created_by,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/assessments", response_model=AssessmentListOut)
async def list_assessments(
    company_profile_id: str | None = Query(None),
    status: str | None = Query(
        None, pattern=r"^(draft|in_progress|completed|archived)$"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db),
):
    """List compliance assessments with optional filters."""
    items, total = await compliance_service.list_assessments(
        db,
        company_profile_id=company_profile_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return AssessmentListOut(assessments=items, total=total)


@router.get("/assessments/{assessment_id}", response_model=AssessmentOut)
async def get_assessment(assessment_id: str, db: Any = Depends(get_db)):
    """Retrieve a single compliance assessment."""
    result = await compliance_service.get_assessment(db, assessment_id)
    if result is None:
        raise HTTPException(404, "Assessment not found")
    return result


@router.patch("/assessments/{assessment_id}", response_model=AssessmentOut)
async def update_assessment(
    assessment_id: str,
    body: AssessmentUpdate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Update a compliance assessment."""
    updated = await compliance_service.update_assessment(
        db,
        assessment_id,
        title=body.title,
        description=body.description,
        status=body.status,
        owner=body.owner,
        risk_level=body.risk_level,
        review_frequency=body.review_frequency,
        due_date=body.due_date,
    )
    if updated is None:
        raise HTTPException(404, "Assessment not found")
    return updated


@router.get(
    "/assessments/{assessment_id}/posture",
    response_model=CompliancePosture,
)
async def get_assessment_posture(
    assessment_id: str, db: Any = Depends(get_db)
):
    """Compute the compliance posture scoped to an assessment."""
    assessment = await compliance_service.get_assessment(db, assessment_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not found")
    try:
        return await compliance_service.compute_posture(
            db,
            assessment["company_profile_id"],
            assessment_id=assessment_id,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/controls", response_model=ControlOut, status_code=201)
async def create_control(
    body: ControlCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Create a new internal compliance control."""
    try:
        return await compliance_service.create_control(
            db,
            company_profile_id=body.company_profile_id,
            title=body.title,
            description=body.description,
            control_type=body.control_type,
            owner=body.owner,
            risk_level=body.risk_level,
            review_frequency=body.review_frequency,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/controls", response_model=ControlListOut)
async def list_controls(
    company_profile_id: str | None = Query(None),
    implementation_status: str | None = Query(
        None,
        pattern=r"^(planned|in_progress|implemented|not_effective)$",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db),
):
    """List controls with optional filters."""
    items, total = await compliance_service.list_controls(
        db,
        company_profile_id=company_profile_id,
        implementation_status=implementation_status,
        skip=skip,
        limit=limit,
    )
    return ControlListOut(controls=items, total=total)


@router.get("/controls/{control_id}", response_model=ControlOut)
async def get_control(control_id: str, db: Any = Depends(get_db)):
    """Retrieve a single control."""
    result = await compliance_service.get_control(db, control_id)
    if result is None:
        raise HTTPException(404, "Control not found")
    return result


@router.patch("/controls/{control_id}", response_model=ControlOut)
async def update_control(
    control_id: str,
    body: ControlUpdate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Update a control's status, effectiveness, or details."""
    updated = await compliance_service.update_control(
        db,
        control_id,
        title=body.title,
        description=body.description,
        control_type=body.control_type,
        implementation_status=body.implementation_status,
        owner=body.owner,
        risk_level=body.risk_level,
        effectiveness_score=body.effectiveness_score,
        review_frequency=body.review_frequency,
        last_reviewed_at=body.last_reviewed_at,
        next_review_date=body.next_review_date,
    )
    if updated is None:
        raise HTTPException(404, "Control not found")
    return updated


# ═══════════════════════════════════════════════════════════════════════════════
# CONTROL EVIDENCES
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/controls/{control_id}/evidences",
    response_model=EvidenceOut,
    status_code=201,
)
async def create_evidence(
    control_id: str,
    body: EvidenceCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Attach evidence metadata to a control."""
    try:
        return await compliance_service.create_evidence(
            db,
            control_id,
            title=body.title,
            description=body.description,
            evidence_type=body.evidence_type,
            file_reference=body.file_reference,
            document_id=body.document_id,
            collected_by=body.collected_by,
            collected_at=body.collected_at,
            valid_from=body.valid_from,
            valid_until=body.valid_until,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get(
    "/controls/{control_id}/evidences",
    response_model=EvidenceListOut,
)
async def list_evidences(
    control_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Any = Depends(get_db),
):
    """List evidences attached to a control."""
    items, total = await compliance_service.list_evidences(
        db, control_id, skip=skip, limit=limit
    )
    return EvidenceListOut(evidences=items, total=total, control_id=control_id)


@router.patch("/evidences/{evidence_id}", response_model=EvidenceOut)
async def update_evidence(
    evidence_id: str,
    body: EvidenceUpdate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Update evidence status or metadata."""
    updated = await compliance_service.update_evidence(
        db,
        evidence_id,
        title=body.title,
        description=body.description,
        status=body.status,
        review_notes=body.review_notes,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
    )
    if updated is None:
        raise HTTPException(404, "Evidence not found")
    return updated


# ═══════════════════════════════════════════════════════════════════════════════
# REQUIREMENT–CONTROL LINKS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/links", response_model=ReqControlLinkOut, status_code=201)
async def create_link(
    body: ReqControlLinkCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Link a legal requirement (exigence) to a control."""
    try:
        return await compliance_service.create_link(
            db,
            exigence_id=body.exigence_id,
            control_id=body.control_id,
            assessment_id=body.assessment_id,
            coverage_status=body.coverage_status,
            coverage_score=body.coverage_score,
            gap_description=body.gap_description,
            justification=body.justification,
            linked_by=body.linked_by,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/links", response_model=ReqControlLinkListOut)
async def list_links(
    exigence_id: str | None = Query(None),
    control_id: str | None = Query(None),
    assessment_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Any = Depends(get_db),
):
    """List requirement–control links with optional filters."""
    items, total = await compliance_service.list_links(
        db,
        exigence_id=exigence_id,
        control_id=control_id,
        assessment_id=assessment_id,
        skip=skip,
        limit=limit,
    )
    return ReqControlLinkListOut(links=items, total=total)


@router.patch("/links/{link_id}", response_model=ReqControlLinkOut)
async def update_link(
    link_id: str,
    body: ReqControlLinkUpdate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Update coverage status / score on a requirement–control link."""
    updated = await compliance_service.update_link(
        db,
        link_id,
        coverage_status=body.coverage_status,
        coverage_score=body.coverage_score,
        gap_description=body.gap_description,
        justification=body.justification,
    )
    if updated is None:
        raise HTTPException(404, "Link not found")
    return updated


@router.delete("/links/{link_id}", status_code=204)
async def delete_link(
    link_id: str,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Remove a requirement–control link."""
    if not await compliance_service.delete_link(db, link_id):
        raise HTTPException(404, "Link not found")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE POSTURE / GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/posture/{company_profile_id}",
    response_model=CompliancePosture,
)
async def get_compliance_posture(
    company_profile_id: str, db: Any = Depends(get_db)
):
    """Full compliance posture for a company profile."""
    try:
        return await compliance_service.compute_posture(
            db, company_profile_id
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/gaps/{company_profile_id}", response_model=list[RequirementGap])
async def get_gaps(
    company_profile_id: str,
    assessment_id: str | None = Query(None),
    db: Any = Depends(get_db),
):
    """List uncovered or partially covered requirements for a company."""
    try:
        return await compliance_service.list_gaps(
            db, company_profile_id, assessment_id=assessment_id
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# EXCEPTION REGISTER
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/exceptions", response_model=ExceptionOut, status_code=201)
async def create_exception(
    body: ExceptionCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Register a compliance exception (risk acceptance, waiver, etc.)."""
    try:
        return await compliance_service.create_exception(
            db,
            exigence_id=body.exigence_id,
            company_profile_id=body.company_profile_id,
            control_id=body.control_id,
            title=body.title,
            description=body.description,
            exception_type=body.exception_type,
            risk_level=body.risk_level,
            justification=body.justification,
            expiry_date=body.expiry_date,
            remediation_action_id=body.remediation_action_id,
            review_frequency=body.review_frequency,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/exceptions", response_model=ExceptionListOut)
async def list_exceptions(
    company_profile_id: str | None = Query(None),
    status: str | None = Query(
        None,
        pattern=r"^(requested|approved|rejected|expired|remediated)$",
    ),
    exigence_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db),
):
    """List compliance exceptions with optional filters."""
    items, total = await compliance_service.list_exceptions(
        db,
        company_profile_id=company_profile_id,
        status=status,
        exigence_id=exigence_id,
        skip=skip,
        limit=limit,
    )
    return ExceptionListOut(exceptions=items, total=total)


@router.patch("/exceptions/{exception_id}", response_model=ExceptionOut)
async def update_exception(
    exception_id: str,
    body: ExceptionUpdate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Update an exception (approve, reject, set remediation, etc.)."""
    updated = await compliance_service.update_exception(
        db,
        exception_id,
        title=body.title,
        description=body.description,
        status=body.status,
        risk_level=body.risk_level,
        justification=body.justification,
        approved_by=body.approved_by,
        expiry_date=body.expiry_date,
        remediation_action_id=body.remediation_action_id,
    )
    if updated is None:
        raise HTTPException(404, "Exception not found")
    return updated


# ═══════════════════════════════════════════════════════════════════════════════
# REMEDIATION ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/remediation-actions", status_code=201)
async def create_remediation_action(
    body: RemediationActionCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Create a remediation action linked to a gap or exception."""
    try:
        return await compliance_service.create_remediation_action(
            db,
            title=body.title,
            description=body.description,
            company_profile_id=body.company_profile_id,
            exigence_id=body.exigence_id,
            exception_id=body.exception_id,
            assigned_to=body.assigned_to,
            due_date=body.due_date,
            priority=body.priority,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
