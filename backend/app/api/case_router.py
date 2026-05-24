"""
FastAPI routes for the Compliance Case Management module.

Prefix: /api/v1/cases
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form

from app.api.auth import get_optional_current_user, require_api_key_or_roles
from app.case_schemas import (
    CaseActionCreate,
    CaseActionListOut,
    CaseActionOut,
    CaseActionUpdate,
    CaseCreate,
    CaseDocumentAttach,
    CaseDocumentListOut,
    CaseDocumentOut,
    CaseDocumentWithDetailsOut,
    CaseDocumentUploadOut,
    DocumentAnalysisOut,
    CaseFindingCreate,
    CaseFindingListOut,
    CaseFindingOut,
    CaseFindingUpdate,
    CaseListOut,
    CaseMessageCreate,
    CaseMessageListOut,
    CaseMessageOut,
    CaseOut,
    CaseSummaryOut,
    CaseUpdate,
)
from app.database import get_db
from app.services import case_service, case_document_service

logger = logging.getLogger(__name__)
require_case_user = require_api_key_or_roles("super_admin", "owner", "admin", "member")
router = APIRouter(prefix="/cases", tags=["cases"], dependencies=[Depends(require_case_user)])


def _organization_scope(user: dict | None) -> str | None:
    if not user or user.get("role") == "super_admin":
        return None
    return user.get("organization_id")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE CASES
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("", response_model=CaseOut, status_code=201)
async def create_case(
    body: CaseCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Create a new compliance case."""
    try:
        case = await case_service.create_case(
            db,
            title=body.title,
            description=body.description,
            company_profile_id=body.company_profile_id,
            priority=body.priority,
            assigned_to=body.assigned_to,
            tags=body.tags,
            created_by=body.created_by,
            organization_id=_organization_scope(current_user),
        )
        return case
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("", response_model=CaseListOut)
async def list_cases(
    status: str | None = Query(None, pattern=r"^(open|in_progress|under_review|resolved|closed)$"),
    priority: str | None = Query(None, pattern=r"^(critical|high|medium|low)$"),
    company_profile_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """List compliance cases with optional filters."""
    cases, total = await case_service.list_cases(
        db,
        status=status,
        priority=priority,
        company_profile_id=company_profile_id,
        organization_id=_organization_scope(current_user),
        skip=skip,
        limit=limit,
    )
    return CaseListOut(cases=cases, total=total)


@router.get("/summary", response_model=CaseSummaryOut)
async def get_case_summary(
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Aggregate statistics across all cases."""
    return await case_service.get_case_summary(
        db,
        organization_id=_organization_scope(current_user),
    )


@router.get("/{case_id}", response_model=CaseOut)
async def get_case(
    case_id: str,
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Retrieve a single compliance case."""
    case = await case_service.get_case(
        db,
        case_id,
        organization_id=_organization_scope(current_user),
    )
    if case is None:
        raise HTTPException(404, "Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseOut)
async def update_case(
    case_id: str,
    body: CaseUpdate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Partially update a compliance case."""
    updated = await case_service.update_case(
        db,
        case_id,
        title=body.title,
        description=body.description,
        company_profile_id=body.company_profile_id,
        status=body.status,
        priority=body.priority,
        assigned_to=body.assigned_to,
        tags=body.tags,
        organization_id=_organization_scope(current_user),
    )
    if updated is None:
        raise HTTPException(404, "Case not found")
    return updated


@router.delete("/{case_id}", status_code=204)
async def delete_case(
    case_id: str,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Delete a case and all its sub-entities."""
    deleted = await case_service.delete_case(
        db,
        case_id,
        organization_id=_organization_scope(current_user),
    )
    if not deleted:
        raise HTTPException(404, "Case not found")


# ═══════════════════════════════════════════════════════════════════════════════
# CASE MESSAGES
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/{case_id}/messages", response_model=CaseMessageOut, status_code=201)
async def add_message(
    case_id: str,
    body: CaseMessageCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Add a message to the case conversation thread."""
    try:
        return await case_service.add_message(
            db,
            case_id,
            role=body.role,
            content=body.content,
            metadata=body.metadata,
            organization_id=_organization_scope(current_user),
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/{case_id}/messages", response_model=CaseMessageListOut)
async def list_messages(
    case_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """List messages in a case thread (chronological order)."""
    messages, total = await case_service.list_messages(
        db,
        case_id,
        skip,
        limit,
        organization_id=_organization_scope(current_user),
    )
    return CaseMessageListOut(messages=messages, total=total, case_id=case_id)


# ═══════════════════════════════════════════════════════════════════════════════
# CASE DOCUMENTS (Extended with analysis capabilities)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/{case_id}/documents", response_model=CaseDocumentOut, status_code=201)
async def attach_document(
    case_id: str,
    body: CaseDocumentAttach,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Attach an existing document to a case with role and optional analysis."""
    try:
        result = await case_document_service.attach_existing_document(
            db, case_id,
            document_id=body.document_id,
            role=body.role,
            label=body.label,
            attached_by=body.attached_by,
            run_analysis=body.run_analysis,
            organization_id=_organization_scope(current_user),
        )
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/{case_id}/documents/upload", response_model=CaseDocumentUploadOut, status_code=201)
async def upload_and_attach_document(
    case_id: str,
    file: UploadFile = File(...),
    role: str = Form(default="other", pattern=r"^(incoming_request|evidence|policy|contract|authority_notice|draft_response|other)$"),
    label: Optional[str] = Form(default=None),
    attached_by: str = Form(default="system"),
    run_analysis: bool = Form(default=True),
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Upload a new document and attach it to a case with analysis.

    This endpoint handles:
    - File upload and processing (OCR if needed)
    - Document chunking and embedding
    - Role-based attachment to case
    - Automatic document classification
    - Entity extraction (dates, parties, obligations, deadlines)
    """
    try:
        file_bytes = await file.read()
        result = await case_document_service.upload_and_attach_document(
            db,
            case_id=case_id,
            filename=file.filename or "unknown",
            file_bytes=file_bytes,
            role=role,
            label=label,
            attached_by=attached_by,
            run_analysis=run_analysis,
            organization_id=_organization_scope(current_user),
        )
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/{case_id}/documents", response_model=CaseDocumentListOut)
async def list_case_documents(
    case_id: str,
    role: Optional[str] = Query(None, pattern=r"^(incoming_request|evidence|policy|contract|authority_notice|draft_response|other)$"),
    document_type: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """List documents attached to a case, optionally filtered by role or document type."""
    docs, total = await case_document_service.list_case_documents_with_analysis(
        db,
        case_id,
        role=role,
        document_type=document_type,
        organization_id=_organization_scope(current_user),
    )
    return CaseDocumentListOut(documents=docs, total=total, case_id=case_id)


@router.get("/{case_id}/documents/{case_document_id}", response_model=CaseDocumentWithDetailsOut)
async def get_case_document(
    case_id: str,
    case_document_id: str,
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Get a specific case document with its analysis and document details."""
    doc = await case_document_service.get_case_document_with_analysis(
        db,
        case_id,
        case_document_id,
        organization_id=_organization_scope(current_user),
    )
    if not doc:
        raise HTTPException(404, "Case document not found")
    return doc


@router.post("/{case_id}/documents/{case_document_id}/analyze", response_model=DocumentAnalysisOut)
async def analyze_case_document(
    case_id: str,
    case_document_id: str,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Trigger or re-run analysis on a case document.

    This will:
    - Classify the document type
    - Generate a summary
    - Extract entities (parties, dates, deadlines, obligations, legal references)
    - Store results in case context
    """
    try:
        result = await case_document_service.analyze_case_document(
            db,
            case_id,
            case_document_id,
            organization_id=_organization_scope(current_user),
        )
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/{case_id}/documents/{case_document_id}/entities")
async def get_document_entities(
    case_id: str,
    case_document_id: str,
    entity_type: Optional[str] = Query(None, pattern=r"^(party|deadline|obligation|legal_reference)$"),
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Get extracted entities from a case document.

    Optionally filter by entity type:
    - party: Individuals, companies, organizations mentioned
    - deadline: Due dates, response deadlines
    - obligation: Legal duties, requirements
    - legal_reference: Article numbers, law citations
    """
    doc = await case_document_service.get_case_document_with_analysis(
        db,
        case_id,
        case_document_id,
        organization_id=_organization_scope(current_user),
    )
    if not doc:
        raise HTTPException(404, "Case document not found")

    analysis = doc.get("analysis") or {}
    entities = analysis.get("entities", {})

    if entity_type == "party":
        return {"parties": entities.get("parties", [])}
    elif entity_type == "deadline":
        return {"deadlines": entities.get("deadlines", [])}
    elif entity_type == "obligation":
        return {"obligations": entities.get("obligations", [])}
    elif entity_type == "legal_reference":
        return {"legal_references": entities.get("legal_references", [])}

    return entities


@router.delete("/{case_id}/documents/{case_document_id}", status_code=204)
async def detach_document(
    case_id: str,
    case_document_id: str,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Detach a document from a case."""
    if not await case_service.detach_document(
        db,
        case_id,
        case_document_id,
        organization_id=_organization_scope(current_user),
    ):
        raise HTTPException(404, "Case document link not found")


# ═══════════════════════════════════════════════════════════════════════════════
# CASE FINDINGS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/{case_id}/findings", response_model=CaseFindingOut, status_code=201)
async def create_finding(
    case_id: str,
    body: CaseFindingCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Record a legal / regulatory finding for a case."""
    try:
        return await case_service.create_finding(
            db, case_id,
            title=body.title,
            description=body.description,
            severity=body.severity,
            exigence_id=body.exigence_id,
            evidence_refs=body.evidence_refs,
            article_references=body.article_references,
            organization_id=_organization_scope(current_user),
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/{case_id}/findings", response_model=CaseFindingListOut)
async def list_findings(
    case_id: str,
    severity: str | None = Query(None, pattern=r"^(critical|major|minor|observation)$"),
    status: str | None = Query(None, pattern=r"^(identified|confirmed|mitigated|resolved)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """List findings for a case with optional severity/status filters."""
    findings, total, by_severity, by_status = await case_service.list_findings(
        db,
        case_id,
        severity=severity,
        status=status,
        skip=skip,
        limit=limit,
        organization_id=_organization_scope(current_user),
    )
    return CaseFindingListOut(
        findings=findings, total=total, case_id=case_id,
        by_severity=by_severity, by_status=by_status,
    )


@router.patch("/{case_id}/findings/{finding_id}", response_model=CaseFindingOut)
async def update_finding(
    case_id: str,
    finding_id: str,
    body: CaseFindingUpdate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Update a finding's status, severity, or details."""
    updated = await case_service.update_finding(
        db, case_id, finding_id,
        title=body.title,
        description=body.description,
        severity=body.severity,
        status=body.status,
        evidence_refs=body.evidence_refs,
        article_references=body.article_references,
        organization_id=_organization_scope(current_user),
    )
    if updated is None:
        raise HTTPException(404, "Finding not found in this case")
    return updated


# ═══════════════════════════════════════════════════════════════════════════════
# CASE ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/{case_id}/actions", response_model=CaseActionOut, status_code=201)
async def create_case_action(
    case_id: str,
    body: CaseActionCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Create a remediation action within a case."""
    try:
        return await case_service.create_case_action(
            db, case_id,
            title=body.title,
            description=body.description,
            finding_id=body.finding_id,
            action_id=body.action_id,
            assigned_to=body.assigned_to,
            due_date=body.due_date,
            priority=body.priority,
            organization_id=_organization_scope(current_user),
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/{case_id}/actions", response_model=CaseActionListOut)
async def list_case_actions(
    case_id: str,
    status: str | None = Query(None, pattern=r"^(pending|in_progress|completed|cancelled)$"),
    priority: str | None = Query(None, pattern=r"^(critical|high|medium|low)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """List remediation actions for a case."""
    actions, total, by_status, by_priority = await case_service.list_case_actions(
        db,
        case_id,
        status=status,
        priority=priority,
        skip=skip,
        limit=limit,
        organization_id=_organization_scope(current_user),
    )
    return CaseActionListOut(
        actions=actions, total=total, case_id=case_id,
        by_status=by_status, by_priority=by_priority,
    )


@router.patch("/{case_id}/actions/{action_id}", response_model=CaseActionOut)
async def update_case_action(
    case_id: str,
    action_id: str,
    body: CaseActionUpdate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """Update a case action (status, assignment, notes, etc.)."""
    updated = await case_service.update_case_action(
        db, case_id, action_id,
        title=body.title,
        description=body.description,
        status=body.status,
        assigned_to=body.assigned_to,
        due_date=body.due_date,
        priority=body.priority,
        completion_notes=body.completion_notes,
        organization_id=_organization_scope(current_user),
    )
    if updated is None:
        raise HTTPException(404, "Action not found in this case")
    return updated
