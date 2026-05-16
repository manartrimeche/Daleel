"""
FastAPI routes — document upload, listing, search.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from typing import Any

from app.api.auth import get_current_user, get_optional_current_user, require_api_key, require_admin
from app.config import get_settings
from app.database import get_db
from app.limiter import limiter
from app.schemas import (
    ActionCriticalityOut,
    ActionDependencyCreate,
    ActionDependencyOut,
    ActionListOut,
    ActionOut,
    AgenticAskResponse,
    AmendmentOperationListOut,
    AmendmentUploadResponse,
    ApplicabilityEvalResponse,
    ApplyAllAmendmentsResponse,
    ApplyAmendmentResponse,
    ArticleListOut,
    ArticleOut,
    ArticleVersionListOut,
    ArticleVersionOut,
    AskRequest,
    AskResponse,
    AuditLogListOut,
    BulkUploadResponse,
    ChunkListOut,
    ClassifyDocumentRequest,
    CleanedTextListOut,
    CompanyProfileCreate,
    CompanyProfileListOut,
    CompanyProfileOut,
    ComputeCriticalityRequest,
    ComputeCriticalityResponse,
    DocumentListOut,
    DocumentOut,
    DocumentSourceOut,
    ExigenceApplicabilityListOut,
    ExigenceListOut,
    ExtractActionsRequest,
    ExtractActionsResponse,
    ExtractAmendmentsRequest,
    ExtractAmendmentsResponse,
    FeedbackCreate,
    FeedbackListOut,
    FeedbackOut,
    LoiCreate,
    LoiListOut,
    LoiOut,
    LoiUpdate,
    RawPageListOut,
    RecalculationResponse,
    RoadmapOut,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SegmentDocumentRequest,
    SegmentDocumentResponse,
)
from app.services import (
    amendment_service,
    applicability_service,
    audit_service,
    auth_service,
    criticality_service,
    action_service,
    document_service,
    feedback_service,
    llm_service,
    loi_service,
    notification_service,
    recalculation_service,
    roadmap_service,
    search_service,
)
from app.services.email_service import send_invitation_email
from app.services.llm_cache import llm_cache

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def _resolve_bulk_upload_dir(raw_path: str, base_dir: Path) -> Path:
    if not raw_path:
        raise HTTPException(400, "data_dir is required")

    if raw_path.startswith(("/", "~")):
        raise HTTPException(400, "Invalid data_dir: absolute paths are not allowed")

    candidate_path = Path(raw_path)
    if candidate_path.is_absolute():
        raise HTTPException(400, "Invalid data_dir: absolute paths are not allowed")

    if ".." in candidate_path.parts:
        raise HTTPException(400, "Invalid data_dir: path traversal is not allowed")

    base_resolved = base_dir.resolve()
    resolved = (base_resolved / candidate_path).resolve()

    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise HTTPException(
            400,
            "Invalid data_dir: path must stay inside the configured upload directory",
        ) from exc

    return resolved


# ── Upload ──


@router.post("/documents/upload", response_model=DocumentOut, status_code=201)
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    clear_db: bool = Query(
        False, description="If true, delete all existing documents before uploading"
    ),
    chunk_size: int | None = Query(None, ge=100, le=5000),
    chunk_overlap: int | None = Query(None, ge=0, le=500),
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
    _key: str | None = Depends(require_api_key),
):
    """Upload and process a document (PDF or DOCX only)."""
    if clear_db and current_user and current_user.get("role") != "super_admin":
        raise HTTPException(403, "Seul le super admin peut vider la base documentaire")
    if clear_db:
        await document_service.clear_all_documents(db)

    if not file.filename:
        raise HTTPException(400, "No filename provided")

    allowed_ext = {".pdf", ".docx", ".doc"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_ext:
        raise HTTPException(400, f"Type de fichier non supporté. Formats acceptés : PDF, DOCX")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_bytes:
            raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
        chunks.append(chunk)
    content = b"".join(chunks)

    if current_user and current_user.get("role") != "super_admin":
        doc = await document_service.create_pending_upload(
            db,
            file.filename,
            content,
            approval_type="document_upload",
            requested_by=str(current_user["_id"]),
            organization_id=current_user.get("organization_id"),
        )
        await notification_service.create_notification(
            db,
            alert_type="approval_document",
            title="Document à approuver",
            message=(
                f"{current_user.get('full_name', 'Un gérant')} a uploadé « {file.filename} ». "
                "Le document attend l'approbation du super admin."
            ),
            details={
                "target_type": "document",
                "document_id": doc["id"],
                "filename": file.filename,
                "requested_by": str(current_user["_id"]),
                "organization_id": current_user.get("organization_id"),
                "approval_status": "pending_approval",
            },
        )
        return doc

    doc = await document_service.upload_document(
        db,
        file.filename,
        content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if doc.get("status") == "error":
        raise HTTPException(422, doc.get("error_message") or "Processing failed")
    return doc


# ── Amendment upload (article-level diff & replace) ──


@router.post(
    "/documents/upload-amendment",
    response_model=AmendmentUploadResponse,
    status_code=201,
)
@limiter.limit("5/minute")
async def upload_amendment(
    request: Request,
    file: UploadFile = File(...),
    loi_id: str | None = Query(None, description="UUID of the target Loi (auto-detected from document content if omitted)"),
    chunk_size: int | None = Query(None, ge=100, le=5000),
    chunk_overlap: int | None = Query(None, ge=0, le=500),
    db: Any = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
    _key: str | None = Depends(require_api_key),
):
    """Upload an amended document. Auto-detects the target law from the text,
    compares articles with the existing version, applies changes, and replaces
    the old document."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_bytes:
            raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
        chunks.append(chunk)
    content = b"".join(chunks)

    if current_user and current_user.get("role") != "super_admin":
        doc = await document_service.create_pending_upload(
            db,
            file.filename,
            content,
            approval_type="amendment_upload",
            requested_by=str(current_user["_id"]),
            organization_id=current_user.get("organization_id"),
            loi_id=loi_id,
        )
        await notification_service.create_notification(
            db,
            alert_type="approval_amendment",
            title="Amendement à approuver",
            message=(
                f"{current_user.get('full_name', 'Un gérant')} a uploadé l'amendement « {file.filename} ». "
                "Il attend l'approbation du super admin avant traitement."
            ),
            details={
                "target_type": "amendment",
                "document_id": doc["id"],
                "filename": file.filename,
                "loi_id": loi_id,
                "requested_by": str(current_user["_id"]),
                "organization_id": current_user.get("organization_id"),
                "approval_status": "pending_approval",
            },
        )
        return {
            "document": doc,
            "old_document_id": None,
            "diff": {"added": 0, "modified": 0, "removed": 0, "unchanged": 0},
            "operations": [],
            "notifications_sent": 1,
            "message": "Amendement envoyé au super admin pour approbation.",
        }

    try:
        result = await document_service.upload_amendment_document(
            db,
            file.filename,
            content,
            loi_id=loi_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    return result


# ── Bulk upload from data directory ──


@router.post(
    "/documents/bulk-upload", response_model=BulkUploadResponse, status_code=201,
    dependencies=[Depends(require_api_key)],
)
@limiter.limit("5/minute")
async def bulk_upload(
    request: Request,
    data_dir: str = Query(
        "data", description="Path (relative to UPLOAD_DIR) with files to process"
    ),
    clear_db: bool = Query(
        False, description="If true, delete all existing documents before uploading"
    ),
    chunk_size: int | None = Query(None, ge=100, le=5000),
    chunk_overlap: int | None = Query(None, ge=0, le=500),
    db: Any = Depends(get_db),
):
    """Process all supported files from a local directory, chunk, embed, and store in DB."""
    dir_path = _resolve_bulk_upload_dir(data_dir, settings.upload_dir)

    if clear_db:
        await document_service.clear_all_documents(db)

    if not dir_path.is_dir():
        raise HTTPException(404, f"Directory not found: {data_dir}")

    results = await document_service.bulk_upload_from_data(
        db,
        dir_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not results:
        raise HTTPException(422, "No supported files found in the directory")

    ok = sum(1 for r in results if r.get("status") == "ready")
    total_chunks = sum(r.get("total_chunks", 0) for r in results)

    return BulkUploadResponse(
        total_files=len(results),
        succeeded=ok,
        failed=len(results) - ok,
        total_chunks=total_chunks,
        documents=results,
    )


# ── List documents ──


@router.get("/documents", response_model=DocumentListOut)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db),
):
    docs, total = await document_service.list_documents(db, skip, limit)
    return DocumentListOut(documents=docs, total=total)


# ── Get single document ──


@router.get("/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: str, db: Any = Depends(get_db)):
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    return doc


@router.get("/documents/{doc_id}/source", response_model=DocumentSourceOut)
async def get_document_source(doc_id: str, db: Any = Depends(get_db)):
    source = await document_service.get_document_source(db, doc_id)
    if source is None:
        raise HTTPException(404, "Document source not found")
    return source


# ── Get document chunks ──


@router.get("/documents/{doc_id}/chunks", response_model=ChunkListOut)
async def get_chunks(
    doc_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Any = Depends(get_db),
):
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    chunks, total = await document_service.get_chunks(db, doc_id, skip, limit)
    return ChunkListOut(chunks=chunks, total=total, document_id=doc_id)


@router.get("/documents/{doc_id}/raw-pages", response_model=RawPageListOut)
async def get_raw_pages(
    doc_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Any = Depends(get_db),
):
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    raw_pages, total = await document_service.get_raw_pages(db, doc_id, skip, limit)
    return RawPageListOut(raw_pages=raw_pages, total=total, document_id=doc_id)


@router.get("/documents/{doc_id}/cleaned-pages", response_model=CleanedTextListOut)
async def get_cleaned_pages(
    doc_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Any = Depends(get_db),
):
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    cleaned_pages, total = await document_service.get_cleaned_pages(
        db, doc_id, skip, limit
    )
    return CleanedTextListOut(
        cleaned_pages=cleaned_pages, total=total, document_id=doc_id
    )


@router.get("/documents/{doc_id}/exigences", response_model=ExigenceListOut)
async def get_exigences(
    doc_id: str,
    exigence_type: str | None = Query(
        None, pattern=r"^(obligation|prohibition|condition|sanction)$"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Any = Depends(get_db),
):
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    exigences, total, type_counts = await document_service.get_exigences(
        db, doc_id, exigence_type=exigence_type, skip=skip, limit=limit
    )
    return ExigenceListOut(
        exigences=exigences,
        total=total,
        document_id=doc_id,
        by_type=type_counts,
    )


@router.post("/documents/{doc_id}/extract-exigences", dependencies=[Depends(require_api_key)])
async def extract_exigences_endpoint(
    doc_id: str,
    db: Any = Depends(get_db),
):
    """
    Manually trigger exigence extraction for a document.
    Analyzes all cleaned pages and extracts regulatory requirements (obligations, prohibitions, conditions, sanctions).

    Returns:
    - exigences_extracted: count of exigences extracted
    - by_type: breakdown by exigence type
    """
    doc = await document_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")

    # Get all cleaned pages for this document
    cleaned_pages, _ = await document_service.get_cleaned_pages(
        db, doc_id, skip=0, limit=10000
    )
    if not cleaned_pages:
        raise HTTPException(
            422, "Document has no cleaned text. Please process the document first."
        )

    cleaned_orm_pages = cleaned_pages

    # Extract exigences
    count = await document_service.extract_and_store_exigences(
        db, doc_id, cleaned_orm_pages, language=doc.get("language", "unknown")
    )

    # Get breakdown by type
    _, _, type_counts = await document_service.get_exigences(db, doc_id)

    return {
        "document_id": doc_id,
        "exigences_extracted": count,
        "by_type": type_counts,
        "message": f"Successfully extracted {count} exigences from {len(cleaned_orm_pages)} pages.",
    }


# ── Delete document ──


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: str, db: Any = Depends(get_db), _key: str | None = Depends(require_api_key)):
    deleted = await document_service.delete_document(db, doc_id)
    if not deleted:
        raise HTTPException(404, "Document not found")


# ── Semantic search ──


@router.post("/search", response_model=SearchResponse)
@limiter.limit("10/minute")
async def search(
    request: Request,
    body: SearchRequest,
    db: Any = Depends(get_db),
):
    """Vector similarity search across all documents."""
    results = await search_service.semantic_search(
        db,
        query=body.query,
        top_k=body.top_k,
        language_filter=body.language_filter,
        document_id=body.document_id,
    )
    return SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


# ── LLM Q&A (RAG) ──


@router.post("/ask", response_model=AskResponse)
@limiter.limit("10/minute")
async def ask_question(
    request: Request,
    body: AskRequest,
    db: Any = Depends(get_db),
):
    """Ask a legal question. Retrieves relevant documents and generates an answer using LLM."""
    result = await llm_service.ask(
        db,
        question=body.question,
        top_k=body.top_k,
        language_filter=body.language_filter,
        response_language=body.response_language,
        document_id=body.document_id,
        llm_model=body.llm_model,
        temperature=body.temperature,
        history=[{"role": m.role, "content": m.content} for m in body.history] if body.history else None,
        use_domain_router=body.use_domain_router,
        use_quality_guard=body.use_quality_guard,
        intent=body.intent,
    )

    # Save Q&A to conversation history
    try:
        from app.api.auth import _bearer_scheme
        from fastapi.security import HTTPAuthorizationCredentials
        creds = await _bearer_scheme(request)
        user = None
        if creds:
            try:
                from app.services import auth_service as _as
                payload = _as.decode_token(creds.credentials)
                if payload.get("type") == "access":
                    user = await _as.get_user_by_id(payload["sub"])
            except Exception:
                pass
        if user:
            from datetime import datetime, timezone
            await db["chat_history"].insert_one({
                "user_id": user["id"],
                "organization_id": user.get("organization_id"),
                "question": body.question,
                "answer": result.get("answer", ""),
                "sources_count": len(result.get("sources", [])),
                "created_at": datetime.now(timezone.utc),
            })
    except Exception:
        logger.debug("Could not save chat history (non-fatal)", exc_info=True)

    return AskResponse(**result)


@router.post("/ask-agentic", response_model=AgenticAskResponse)
@limiter.limit("10/minute")
async def ask_question_agentic(request: Request, body: AskRequest, db: Any = Depends(get_db)):
    """Ask a legal question using an agentic retrieval loop (non-breaking mode)."""
    result = await llm_service.ask_agentic(
        db,
        question=body.question,
        top_k=body.top_k,
        language_filter=body.language_filter,
        response_language=body.response_language,
        document_id=body.document_id,
        temperature=body.temperature,
        history=[{"role": m.role, "content": m.content} for m in body.history],
        use_domain_router=body.use_domain_router,
        use_quality_guard=body.use_quality_guard,
        intent=body.intent,
    )

    # Save Q&A to conversation history
    try:
        from app.api.auth import _bearer_scheme
        creds = await _bearer_scheme(request)
        user = None
        if creds:
            try:
                from app.services import auth_service as _as
                payload = _as.decode_token(creds.credentials)
                if payload.get("type") == "access":
                    user = await _as.get_user_by_id(payload["sub"])
            except Exception:
                pass
        if user:
            from datetime import datetime, timezone
            await db["chat_history"].insert_one({
                "user_id": user["id"],
                "organization_id": user.get("organization_id"),
                "question": body.question,
                "answer": result.get("answer", ""),
                "sources_count": len(result.get("sources", [])),
                "created_at": datetime.now(timezone.utc),
            })
    except Exception:
        logger.debug("Could not save chat history (non-fatal)", exc_info=True)

    return AgenticAskResponse(**result)


@router.post("/ask-auto", response_model=AgenticAskResponse)
@limiter.limit("10/minute")
async def ask_question_auto(request: Request, body: AskRequest, db: Any = Depends(get_db)):
    """Ask a legal question with automatic backend mode selection (classic vs agentic)."""
    result = await llm_service.ask_auto(
        db,
        question=body.question,
        top_k=body.top_k,
        language_filter=body.language_filter,
        response_language=body.response_language,
        document_id=body.document_id,
        temperature=body.temperature,
        history=[{"role": m.role, "content": m.content} for m in body.history],
        use_domain_router=body.use_domain_router,
        use_quality_guard=body.use_quality_guard,
        intent=body.intent,
    )
    return AgenticAskResponse(**result)


@router.post("/ask-stream")
@limiter.limit("10/minute")
async def ask_question_stream(request: Request, body: AskRequest, db: Any = Depends(get_db)):
    """
    Streaming RAG Q&A via Server-Sent Events (SSE).

    Events emitted:
    - `sources` : list of source metadata (sent immediately after retrieval)
    - `token`   : a single LLM output token (streamed progressively)
    - `error`   : an error message if something goes wrong
    - `done`    : final metadata (model name, chunks_used)

    Usage: ``EventSource('/api/v1/ask-stream', { method: 'POST', body: ... })``
    """

    async def _event_generator():
        async for evt in llm_service.ask_stream(
            db,
            question=body.question,
            top_k=body.top_k,
            language_filter=body.language_filter,
            document_id=body.document_id,
            temperature=body.temperature,
            history=[{"role": m.role, "content": m.content} for m in body.history],
            use_domain_router=body.use_domain_router,
            use_quality_guard=body.use_quality_guard,
            intent=body.intent,
        ):
            yield f"event: {evt['event']}\ndata: {evt['data']}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/feedback", response_model=FeedbackOut, status_code=201)
@limiter.limit("20/minute")
async def create_feedback_entry(request: Request, body: FeedbackCreate, db: Any = Depends(get_db)):
    """Store a user-corrected answer to improve future responses."""
    item = await feedback_service.create_feedback(
        db,
        question=body.question,
        corrected_answer=body.corrected_answer,
        language=body.language,
        rating=body.rating,
        notes=body.notes,
        source_document_id=body.source_document_id,
        tags=body.tags,
    )
    return FeedbackOut(**item)


@router.get("/feedback", response_model=FeedbackListOut)
async def list_feedback_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db),
):
    """List stored user feedback entries (latest first)."""
    items, total = await feedback_service.list_feedback(db, skip=skip, limit=limit)
    return FeedbackListOut(items=[FeedbackOut(**item) for item in items], total=total)


# ── SPRINT 2: COMPANY PROFILES & APPLICABILITY ──

# ── Company Profile Management ──


@router.post("/company-profiles", response_model=CompanyProfileOut, status_code=201)
async def create_company_profile(
    body: CompanyProfileCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """Create a new company profile for applicability evaluation."""
    profile = await applicability_service.create_company_profile(
        db,
        name=body.name,
        sector=body.sector,
        size=body.size,
        employees=body.employees,
        activities=body.activities,
        jurisdiction=body.jurisdiction,
        notes=body.notes,
    )
    return profile


@router.get("/company-profiles", response_model=CompanyProfileListOut)
async def list_company_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db),
):
    """List all company profiles."""
    profiles, total = await applicability_service.list_company_profiles(
        db, skip=skip, limit=limit
    )
    return CompanyProfileListOut(profiles=profiles, total=total)


@router.get("/company-profiles/{profile_id}", response_model=CompanyProfileOut)
async def get_company_profile(
    profile_id: str,
    db: Any = Depends(get_db),
):
    """Get a specific company profile by ID."""
    profile = await applicability_service.get_company_profile(db, profile_id)
    if not profile:
        raise HTTPException(404, "Company profile not found")
    return profile


@router.put("/company-profiles/{profile_id}", response_model=CompanyProfileOut, dependencies=[Depends(require_api_key)])
async def update_company_profile(
    profile_id: str,
    body: CompanyProfileCreate,
    db: Any = Depends(get_db),
):
    """Update a company profile."""
    updated = await applicability_service.update_company_profile(
        db,
        profile_id,
        name=body.name,
        sector=body.sector,
        size=body.size,
        employees=body.employees,
        activities=body.activities,
        jurisdiction=body.jurisdiction,
        notes=body.notes,
    )
    if not updated:
        raise HTTPException(404, "Company profile not found")
    return updated


@router.delete("/company-profiles/{profile_id}", status_code=204, dependencies=[Depends(require_api_key)])
async def delete_company_profile(
    profile_id: str,
    db: Any = Depends(get_db),
):
    """Delete a company profile (cascades to applicabilities)."""
    deleted = await applicability_service.delete_company_profile(db, profile_id)
    if not deleted:
        raise HTTPException(404, "Company profile not found")


# ── Applicability Evaluation ──


@router.post("/company-profiles/{profile_id}/evaluate-applicabilities", dependencies=[Depends(require_api_key)])
async def evaluate_applicabilities(
    profile_id: str,
    db: Any = Depends(get_db),
    exigence_ids: list[str] | None = None,
    document_id: str | None = None,
):
    """
    Evaluate applicability of exigences to a company profile using LLM.

    Optional filters (passed as query parameters):
    - exigence_ids: List of specific exigence IDs to evaluate
    - document_id: Filter to exigences from a specific document

    If both are None, evaluates ALL exigences across all documents.
    """
    # Verify profile exists
    profile = await applicability_service.get_company_profile(db, profile_id)
    if not profile:
        raise HTTPException(404, "Company profile not found")

    try:
        count = await applicability_service.evaluate_applicabilities(
            db,
            profile_id,
            exigence_ids=exigence_ids,
            document_id=document_id,
        )
    except Exception as e:
        logger.error(f"Error evaluating applicabilities: {e}")
        raise HTTPException(500, "Internal error during applicability evaluation")

    if count == 0:
        raise HTTPException(422, "No exigences found to evaluate with given filters")

    # Get summary statistics
    summary = await applicability_service.get_applicability_summary(db, profile_id)

    return ApplicabilityEvalResponse(
        profile_id=profile_id,
        evaluated_exigences=count,
        applicable=summary["applicable"],
        not_applicable=summary["not_applicable"],
        avg_confidence=summary["avg_confidence"],
        by_type=summary["by_type"],
        message=f"Evaluated {count} exigences. {summary['applicable']} applicable, {summary['not_applicable']} not applicable.",
    )


@router.get(
    "/company-profiles/{profile_id}/applicabilities",
    response_model=ExigenceApplicabilityListOut,
)
async def get_applicabilities(
    profile_id: str,
    is_applicable: bool | None = Query(None, description="Filter by applicable status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Any = Depends(get_db),
):
    """
    Get applicabilities for a company profile.

    Optional filter:
    - is_applicable: true or false to filter results
    """
    # Verify profile exists
    profile = await applicability_service.get_company_profile(db, profile_id)
    if not profile:
        raise HTTPException(404, "Company profile not found")

    applicabilities, total = await applicability_service.get_applicabilities(
        db, profile_id, is_applicable=is_applicable, skip=skip, limit=limit
    )

    # Get summary for counts
    summary = await applicability_service.get_applicability_summary(db, profile_id)

    return ExigenceApplicabilityListOut(
        applicabilities=applicabilities,
        total=total,
        applicable_count=summary["applicable"],
        not_applicable_count=summary["not_applicable"],
    )


@router.get("/company-profiles/{profile_id}/applicabilities/summary")
async def get_applicability_summary(
    profile_id: str,
    db: Any = Depends(get_db),
):
    """Get summary statistics of applicabilities for a company profile."""
    # Verify profile exists
    profile = await applicability_service.get_company_profile(db, profile_id)
    if not profile:
        raise HTTPException(404, "Company profile not found")

    summary = await applicability_service.get_applicability_summary(db, profile_id)
    return {"profile_id": profile_id, "profile_name": profile["name"], **summary}


# ══════════════════════════════════════════════════════════════════════════════
# SPRINT 3 — LOI / ARTICLE / ARTICLE_VERSION / ACTION
# ══════════════════════════════════════════════════════════════════════════════

# ── Lois ──────────────────────────────────────────────────────────────────────


@router.post("/lois", response_model=LoiOut, status_code=201)
async def create_loi(
    body: LoiCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """
    Create a new Loi (legal code/law entity).

    Examples: code='CT' name='Code du Travail', code='CS' name='Code des Sociétés'.
    The code must be unique across all lois.
    """
    try:
        return await loi_service.create_loi(
            db,
            code=body.code,
            name=body.name,
            jurisdiction=body.jurisdiction,
            language=body.language,
            description=body.description,
            version_label=body.version_label,
        )
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.get("/lois", response_model=LoiListOut)
async def list_lois(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db),
):
    """List all registered Lois with per-loi article counts."""
    lois, total = await loi_service.list_lois(db, skip=skip, limit=limit)
    return LoiListOut(lois=lois, total=total)


@router.get("/lois/{loi_id}", response_model=LoiOut)
async def get_loi(
    loi_id: str,
    db: Any = Depends(get_db),
):
    """Get a Loi by UUID."""
    loi = await loi_service.get_loi(db, loi_id)
    if not loi:
        raise HTTPException(404, "Loi not found")
    return loi


@router.patch("/lois/{loi_id}", response_model=LoiOut, dependencies=[Depends(require_api_key)])
async def update_loi(
    loi_id: str,
    body: LoiUpdate,
    db: Any = Depends(get_db),
):
    """Partial update of a Loi's metadata (name, description, version_label…)."""
    loi = await loi_service.update_loi(db, loi_id, **body.model_dump(exclude_none=True))
    if not loi:
        raise HTTPException(404, "Loi not found")
    return loi


@router.delete("/lois/{loi_id}", status_code=204, dependencies=[Depends(require_api_key)])
async def delete_loi(
    loi_id: str,
    db: Any = Depends(get_db),
):
    """Delete a Loi and cascade to all its articles and versions."""
    deleted = await loi_service.delete_loi(db, loi_id)
    if not deleted:
        raise HTTPException(404, "Loi not found")


# ── Segmentation ──────────────────────────────────────────────────────────────


@router.post(
    "/lois/{loi_id}/segment-document",
    response_model=SegmentDocumentResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def segment_document(
    loi_id: str,
    body: SegmentDocumentRequest,
    db: Any = Depends(get_db),
):
    """
    Segment an already-uploaded document into article-level units and store them under this Loi.

    Pipeline:
      1. Loads all cleaned pages for the document.
      2. Detects hierarchy markers: Titre → Chapitre → Section.
      3. Splits strictly at Article / الفصل boundaries.
      4. Creates Article records (unique per loi by article_key, e.g. 'CT-Art-95').
      5. Creates ArticleVersion(v1) per article.
         If an article_key already exists → creates v(n+1) and marks previous as 'superseded'.
      6. Links the Document to this Loi.
    """
    try:
        result = await loi_service.segment_document(
            db,
            loi_id=loi_id,
            document_id=body.document_id,
            language_override=body.language_override,
            auto_extract_exigences=body.auto_extract_exigences,
            auto_extract_actions=body.auto_extract_actions,
        )
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))


# ── Articles ──────────────────────────────────────────────────────────────────


@router.get("/lois/{loi_id}/articles", response_model=ArticleListOut)
async def list_articles(
    loi_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(
        None, description="Keyword filter on heading or article number"
    ),
    db: Any = Depends(get_db),
):
    """List all articles for a Loi with active_version_id and total_versions."""
    loi = await loi_service.get_loi(db, loi_id)
    if not loi:
        raise HTTPException(404, "Loi not found")
    articles, total = await loi_service.list_articles(
        db, loi_id, skip=skip, limit=limit, search=search
    )
    return ArticleListOut(articles=articles, total=total, loi_id=loi_id)


@router.get("/articles/{article_id}", response_model=ArticleOut)
async def get_article(
    article_id: str,
    db: Any = Depends(get_db),
):
    """Get an Article by UUID."""
    article = await loi_service.get_article(db, article_id)
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.get(
    "/lois/{loi_id}/articles/by-key/{article_key}",
    response_model=ArticleOut,
)
async def get_article_by_key(
    loi_id: str,
    article_key: str,
    db: Any = Depends(get_db),
):
    """Get an Article by its stable unique key within a Loi (e.g. 'CT-Art-95')."""
    article = await loi_service.get_article_by_key(db, loi_id, article_key)
    if not article:
        raise HTTPException(404, f"Article '{article_key}' not found in this Loi")
    return article


# ── Article Versions ──────────────────────────────────────────────────────────


@router.get("/articles/{article_id}/versions", response_model=ArticleVersionListOut)
async def list_article_versions(
    article_id: str,
    db: Any = Depends(get_db),
):
    """
    List all versions of an Article (active + superseded + repealed).

    Full legal history is preserved — versions are never deleted.
    """
    article = await loi_service.get_article(db, article_id)
    if not article:
        raise HTTPException(404, "Article not found")
    versions, total = await loi_service.list_article_versions(db, article_id)
    return ArticleVersionListOut(versions=versions, total=total, article_id=article_id)


@router.get("/article-versions/{version_id}", response_model=ArticleVersionOut)
async def get_article_version(
    version_id: str,
    db: Any = Depends(get_db),
):
    """Get a specific ArticleVersion by UUID."""
    version = await loi_service.get_article_version(db, version_id)
    if not version:
        raise HTTPException(404, "ArticleVersion not found")
    return version


@router.get("/article-versions/{version_id}/exigences", response_model=ExigenceListOut)
async def get_version_exigences(
    version_id: str,
    exigence_type: str | None = Query(
        None,
        description="Filter by type: obligation | prohibition | condition | sanction",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Any = Depends(get_db),
):
    """Get all Exigences extracted from this ArticleVersion."""
    from app.services.document_service import _exigence_to_out

    version = await loi_service.get_article_version(db, version_id)
    if not version:
        raise HTTPException(404, "ArticleVersion not found")

    query: dict = {"article_version_id": version_id}

    if exigence_type:
        query["exigence_type"] = exigence_type

    total = await db["exigences"].count_documents(query)
    rows = await db["exigences"].find(query).sort([
        ("page_number", 1),
        ("confidence_score", -1),
    ]).skip(skip).limit(limit).to_list(length=None)

    return ExigenceListOut(
        exigences=[_exigence_to_out(e) for e in rows],
        total=total,
        document_id=version.get("source_document_id") or "",
    )


# ── Actions ───────────────────────────────────────────────────────────────────


@router.post(
    "/article-versions/{version_id}/extract-actions",
    response_model=ExtractActionsResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def extract_actions(
    version_id: str,
    body: ExtractActionsRequest,
    db: Any = Depends(get_db),
):
    """
    Extract structured compliance Actions from the Exigences of this ArticleVersion via LLM.

    Each Action provides:
    - modalite      : obligation | interdiction | sanction | condition
    - action_precise: the concrete thing the company must do / avoid
    - conditions    : list of applicability conditions
    - preuve        : document/evidence proving compliance

    Pass exigence_ids to restrict extraction to specific exigences;
    leave empty to process all exigences linked to this ArticleVersion.
    """
    version = await loi_service.get_article_version(db, version_id)
    if not version:
        raise HTTPException(404, "ArticleVersion not found")
    try:
        result = await action_service.extract_and_store_actions(
            db,
            article_version_id=version_id,
            exigence_ids=body.exigence_ids,
        )
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/article-versions/{version_id}/actions", response_model=ActionListOut)
async def get_version_actions(
    version_id: str,
    modalite: str | None = Query(
        None,
        description="Filter: obligation | interdiction | sanction | condition",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Any = Depends(get_db),
):
    """Get all Actions extracted from this ArticleVersion, optionally filtered by modalite."""
    version = await loi_service.get_article_version(db, version_id)
    if not version:
        raise HTTPException(404, "ArticleVersion not found")
    actions, total, by_modalite = await action_service.get_actions_by_version(
        db, version_id, modalite=modalite, skip=skip, limit=limit
    )
    return ActionListOut(actions=actions, total=total, by_modalite=by_modalite)


@router.get("/actions/{action_id}", response_model=ActionOut)
async def get_action(
    action_id: str,
    db: Any = Depends(get_db),
):
    """Get a single Action by UUID."""
    action = await action_service.get_action(db, action_id)
    if not action:
        raise HTTPException(404, "Action not found")
    return action


@router.delete("/article-versions/{version_id}/actions", status_code=204, dependencies=[Depends(require_api_key)])
async def delete_version_actions(
    version_id: str,
    db: Any = Depends(get_db),
):
    """
    Delete all Actions for an ArticleVersion to allow clean re-extraction.
    Does not affect the Exigences or the ArticleVersion itself.
    """
    version = await loi_service.get_article_version(db, version_id)
    if not version:
        raise HTTPException(404, "ArticleVersion not found")
    await action_service.delete_actions_by_version(db, version_id)


# ══════════════════════════════════════════════════════════════════════════════
# SPRINT 4 — CRITICITÉ, DÉPENDANCES & FEUILLE DE ROUTE
# ══════════════════════════════════════════════════════════════════════════════

# ── Criticité ─────────────────────────────────────────────────────────────────


@router.post(
    "/lois/{loi_id}/compute-criticality",
    response_model=ComputeCriticalityResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def compute_criticality_for_loi(
    loi_id: str,
    body: ComputeCriticalityRequest,
    db: Any = Depends(get_db),
):
    """
    Compute criticality for all active Actions under a Loi (rule-based engine).

    Levels assigned:
    - **critique**   : score ≥ 0.75 — sanctions, fines, criminal liability
    - **importante** : score ≥ 0.50 — obligations, prohibitions
    - **secondaire** : score < 0.50  — conditions, informational duties

    Pass `recompute=true` to force re-evaluation of already-computed actions.
    """
    loi = await loi_service.get_loi(db, loi_id)
    if not loi:
        raise HTTPException(404, "Loi not found")
    try:
        result = await criticality_service.compute_for_loi(
            db, loi_id, recompute=body.recompute
        )
        return result
    except Exception as e:
        logger.error(f"Criticality computation error: {e}")
        raise HTTPException(500, "Internal computation error")


@router.post(
    "/article-versions/{version_id}/compute-criticality",
    response_model=ComputeCriticalityResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def compute_criticality_for_version(
    version_id: str,
    body: ComputeCriticalityRequest,
    db: Any = Depends(get_db),
):
    """
    Compute criticality for all (or selected) Actions of one ArticleVersion.

    Optionally scope to specific `action_ids` in the request body.
    """
    version = await loi_service.get_article_version(db, version_id)
    if not version:
        raise HTTPException(404, "ArticleVersion not found")
    try:
        result = await criticality_service.compute_for_article_version(
            db,
            article_version_id=version_id,
            action_ids=body.action_ids,
            recompute=body.recompute,
        )
        return result
    except Exception as e:
        logger.error(f"Criticality computation error: {e}")
        raise HTTPException(500, "Internal computation error")


@router.get("/actions/{action_id}/criticality", response_model=ActionCriticalityOut)
async def get_action_criticality(
    action_id: str,
    db: Any = Depends(get_db),
):
    """
    Get the criticality record for a specific Action.

    Returns 404 if criticality has not been computed yet.
    Use `POST /article-versions/{id}/compute-criticality` to trigger computation.
    """
    action = await action_service.get_action(db, action_id)
    if not action:
        raise HTTPException(404, "Action not found")
    crit = await criticality_service.get_criticality(db, action_id)
    if not crit:
        raise HTTPException(
            404,
            "Criticality not yet computed for this action. "
            "Call POST /article-versions/{version_id}/compute-criticality first.",
        )
    return crit


# ── Dépendances ───────────────────────────────────────────────────────────────


@router.post(
    "/action-dependencies", response_model=ActionDependencyOut, status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def add_action_dependency(
    body: ActionDependencyCreate,
    db: Any = Depends(get_db),
):
    """
    Declare that one Action depends on another.

    dependency_type:
    - **prerequis**  : action_id can only begin after depends_on_id is complete
    - **sequence**   : action_id should immediately follow depends_on_id
    - **maintien**   : action_id must stay active as long as depends_on_id is active

    This information is used by the roadmap generator for topological ordering.
    """
    try:
        dep = await roadmap_service.add_dependency(
            db,
            action_id=body.action_id,
            depends_on_id=body.depends_on_id,
            dependency_type=body.dependency_type,
            reason=body.reason,
        )
        return dep
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get(
    "/actions/{action_id}/dependencies", response_model=list[ActionDependencyOut]
)
async def list_action_dependencies(
    action_id: str,
    db: Any = Depends(get_db),
):
    """
    List all dependencies declared for an Action (i.e., its prerequisites).
    """
    action = await action_service.get_action(db, action_id)
    if not action:
        raise HTTPException(404, "Action not found")
    return await roadmap_service.list_dependencies(db, action_id)


@router.delete("/action-dependencies/{dep_id}", status_code=204, dependencies=[Depends(require_api_key)])
async def delete_action_dependency(
    dep_id: str,
    db: Any = Depends(get_db),
):
    """
    Remove a dependency relationship by its UUID.
    """
    deleted = await roadmap_service.delete_dependency(db, dep_id)
    if not deleted:
        raise HTTPException(404, "Dependency not found")


# ── Feuille de route ──────────────────────────────────────────────────────────


@router.get(
    "/company-profiles/{profile_id}/roadmap",
    response_model=RoadmapOut,
)
async def get_roadmap(
    profile_id: str,
    db: Any = Depends(get_db),
):
    """
    Generate the dynamic compliance action plan for a company profile.

    The roadmap:
    1. Retrieves all applicable Actions (via evaluated applicabilities).
    2. Computes missing criticality levels automatically.
    3. Applies topological sort respecting declared dependencies.
    4. Orders actions: **critique** first → **importante** → **secondaire**.

    Prerequisites:
    - Run `POST /company-profiles/{id}/evaluate-applicabilities` first.
    - Run `POST /article-versions/{id}/extract-actions` on relevant versions.

    The roadmap is **dynamic**: calling this endpoint again after any change
    (profile update, new law version, re-evaluation) returns fresh results.
    """
    profile = await applicability_service.get_company_profile(db, profile_id)
    if not profile:
        raise HTTPException(404, "Company profile not found")
    try:
        roadmap = await roadmap_service.generate_roadmap(db, profile_id)
        return roadmap
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.error(f"Roadmap generation error for profile {profile_id}: {e}")
        raise HTTPException(500, "Internal error during roadmap generation")


@router.post(
    "/company-profiles/{profile_id}/roadmap/refresh",
    response_model=RoadmapOut,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def refresh_roadmap(
    profile_id: str,
    db: Any = Depends(get_db),
):
    """
    Force-regenerate the compliance roadmap after a profile or law update.

    Identical to GET /roadmap but signals intent to recalculate (useful
    after re-running applicability evaluation or extracting new actions).
    """
    profile = await applicability_service.get_company_profile(db, profile_id)
    if not profile:
        raise HTTPException(404, "Company profile not found")
    try:
        roadmap = await roadmap_service.generate_roadmap(db, profile_id)
        return roadmap
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.error(f"Roadmap refresh error for profile {profile_id}: {e}")
        raise HTTPException(500, "Internal error during roadmap refresh")


# ══════════════════════════════════════════════════════════════════════════════
# SPRINT 5 — MISE À JOUR LÉGISLATIVE : AMENDEMENTS, VERSIONING, AUDIT
# ══════════════════════════════════════════════════════════════════════════════

# ── Step 10 : Classification de document ──────────────────────────────────────


@router.patch("/documents/{doc_id}/classify", dependencies=[Depends(require_api_key)])
async def classify_document(
    doc_id: str,
    body: ClassifyDocumentRequest,
    db: Any = Depends(get_db),
):
    """
    Classify an uploaded document and optionally link it to a Loi.

    document_type:
    - **loi_principale** : the main law text (default on upload)
    - **modificatif**    : an amendment/modification text — required before extraction
    - **autre**          : other (circulaire, décret d'application…)

    Setting `modificatif` with a `loi_id` is the required first step before
    calling `POST /documents/{id}/extract-amendments`.
    """
    try:
        result = await amendment_service.classify_document(
            db,
            document_id=doc_id,
            document_type=body.document_type,
            loi_id=body.loi_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))


# ── Step 11 : Extraction des opérations d'amendement ──────────────────────────


@router.post(
    "/documents/{doc_id}/extract-amendments",
    response_model=ExtractAmendmentsResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def extract_amendments(
    doc_id: str,
    body: ExtractAmendmentsRequest,
    db: Any = Depends(get_db),
):
    """
    Extract ADD / REPLACE / MODIFY / REPEAL operations from an amendment document via LLM.

    Prerequisites:
    1. Document must be uploaded and processed (status=ready).
    2. Document should be classified as `modificatif` (call PATCH /documents/{id}/classify first).

    The extracted operations are stored with status **pending** and can be reviewed
    before applying with `POST /documents/{id}/apply-amendments`.
    """
    try:
        result = await amendment_service.extract_amendment_operations(
            db,
            document_id=doc_id,
            loi_id=body.loi_id,
            language_override=body.language_override,
        )
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.error(f"Amendment extraction error: {e}")
        raise HTTPException(500, "Internal error during amendment extraction")


@router.get("/documents/{doc_id}/amendments", response_model=AmendmentOperationListOut)
async def list_amendments(
    doc_id: str,
    status: str | None = Query(
        None, description="Filter: pending | applied | rejected"
    ),
    db: Any = Depends(get_db),
):
    """
    List all AmendmentOperations extracted from a document.

    Filter by status to review pending operations before applying.
    """
    ops, total, by_type, by_status = await amendment_service.list_operations(
        db, doc_id, status=status
    )
    return AmendmentOperationListOut(
        operations=ops,
        total=total,
        document_id=doc_id,
        by_type=by_type,
        by_status=by_status,
    )


# ── Step 12 : Application du versioning ───────────────────────────────────────


@router.post(
    "/amendment-operations/{op_id}/apply",
    response_model=ApplyAmendmentResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def apply_amendment(
    op_id: str,
    db: Any = Depends(get_db),
):
    """
    Apply a single pending AmendmentOperation with immutable versioning.

    What happens:
    - **REPLACE / MODIFY** : creates a new `ArticleVersion` (v+1, status=active),
      marks the previous version `superseded`. No data is ever overwritten.
    - **REPEAL** : marks the active `ArticleVersion` as `repealed`.
    - **ADD** : creates the `Article` (if new) and its first `ArticleVersion`.

    An `AuditLog` entry is written for every operation.
    """
    try:
        result = await amendment_service.apply_amendment_operation(db, op_id)

        # Phase 14: trigger recalculation automatically after successful apply.
        try:
            loi_id = result.get("loi_id")
            new_version_id = result.get("new_version_id")

            if loi_id and new_version_id:
                await recalculation_service.recalculate_after_amendment(
                    db,
                    loi_id,
                    [new_version_id],
                )
                result["message"] += " Recalculation triggered automatically."
            elif loi_id:
                await recalculation_service.recalculate_for_loi(db, loi_id)
                result["message"] += " Recalculation triggered automatically."
        except Exception as recalc_err:
            logger.error(
                "Automatic recalculation failed after apply %s: %s",
                op_id,
                recalc_err,
            )
            result["message"] += (
                " Automatic recalculation failed; run "
                "POST /lois/{loi_id}/recalculate manually."
            )

        # Fire notifications for affected company profiles
        try:
            from app.services.notification_service import check_and_notify_amendment_impacts
            loi_id = result.get("loi_id")
            op_type = result.get("operation_type", "")
            target_key = result.get("target_article_key", "")
            if loi_id and target_key:
                n = await check_and_notify_amendment_impacts(
                    db, loi_id=loi_id, operation_type=op_type, target_article_key=target_key,
                )
                if n:
                    result["message"] += f" {n} notification(s) sent."
        except Exception as notif_err:
            logger.warning("Notification dispatch failed: %s", notif_err)

        return result
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.error(f"Amendment application error: {e}")
        raise HTTPException(500, "Internal error during amendment application")


@router.post(
    "/documents/{doc_id}/apply-amendments",
    response_model=ApplyAllAmendmentsResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def apply_all_amendments(
    doc_id: str,
    db: Any = Depends(get_db),
):
    """
    Apply all pending AmendmentOperations for a document in a single batch.

    Operations are applied in chronological order (creation order).
    Failed operations are marked `rejected` and do not block the others.

    After applying, call `POST /lois/{loi_id}/recalculate` to update
    exigences, actions, criticality and the roadmap.
    """
    try:
        result = await amendment_service.apply_all_pending(db, doc_id)

        # Phase 14: trigger recalculation automatically after successful batch apply.
        try:
            loi_ids_affected = result.get("loi_ids_affected", [])
            new_version_ids = sorted(
                {
                    r.get("new_version_id")
                    for r in result.get("results", [])
                    if r.get("status") == "applied" and r.get("new_version_id")
                }
            )

            # Recalculate for each affected loi
            if loi_ids_affected:
                if new_version_ids:
                    for loi_id in loi_ids_affected:
                        await recalculation_service.recalculate_after_amendment(
                            db,
                            loi_id,
                            new_version_ids,
                        )
                    result["message"] += " Recalculation triggered automatically."
                elif result.get("applied", 0) > 0:
                    for loi_id in loi_ids_affected:
                        await recalculation_service.recalculate_for_loi(db, loi_id)
                    result["message"] += " Recalculation triggered automatically."
        except Exception as recalc_err:
            logger.error(
                "Automatic recalculation failed after batch apply doc %s: %s",
                doc_id,
                recalc_err,
            )
            result["message"] += (
                " Automatic recalculation failed; run "
                "POST /lois/{loi_id}/recalculate manually."
            )

        return result
    except Exception as e:
        logger.error(f"Batch amendment error: {e}")
        raise HTTPException(500, "Internal error during batch amendment processing")


# ── Step 13 : Journal d'audit ─────────────────────────────────────────────────


@router.get("/audit-logs", response_model=AuditLogListOut)
async def get_audit_logs(
    loi_id: str | None = Query(None, description="Filter by Loi UUID"),
    article_id: str | None = Query(None, description="Filter by Article UUID"),
    event_type: str | None = Query(None, description="Filter by event type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Any = Depends(get_db),
):
    """
    Query the audit log — append-only trail of all legislative update events.

    Filterable by: Loi, Article, event_type (amendment_applied, version_superseded…).
    Always returned most-recent-first.
    """
    logs, total = await audit_service.get_audit_logs(
        db,
        loi_id=loi_id,
        article_id=article_id,
        event_type=event_type,
        skip=skip,
        limit=limit,
    )
    return AuditLogListOut(logs=logs, total=total)


@router.get("/lois/{loi_id}/audit-logs", response_model=AuditLogListOut)
async def get_loi_audit_logs(
    loi_id: str,
    event_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Any = Depends(get_db),
):
    """Audit log filtered by Loi — full legislative history of this law."""
    loi = await loi_service.get_loi(db, loi_id)
    if not loi:
        raise HTTPException(404, "Loi not found")
    logs, total = await audit_service.get_audit_logs(
        db, loi_id=loi_id, event_type=event_type, skip=skip, limit=limit
    )
    return AuditLogListOut(logs=logs, total=total)


@router.get("/articles/{article_id}/audit-logs", response_model=AuditLogListOut)
async def get_article_audit_logs(
    article_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Any = Depends(get_db),
):
    """Audit log filtered by Article — full version history of one article."""
    article = await loi_service.get_article(db, article_id)
    if not article:
        raise HTTPException(404, "Article not found")
    logs, total = await audit_service.get_audit_logs(
        db, article_id=article_id, skip=skip, limit=limit
    )
    return AuditLogListOut(logs=logs, total=total)


# ── Step 14 : Recalcul automatique ────────────────────────────────────────────


@router.post(
    "/lois/{loi_id}/recalculate",
    response_model=RecalculationResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def recalculate_loi(
    loi_id: str,
    db: Any = Depends(get_db),
):
    """
    Trigger the full recalculation pipeline for all active ArticleVersions of a Loi.

    Run this after applying amendments to ensure:
    - ✅ Exigences are re-extracted from updated article texts
    - ✅ Actions are re-extracted from new exigences
    - ✅ Criticality is recomputed for new actions
    - ✅ Roadmap auto-refreshes on next GET /company-profiles/{id}/roadmap

    Typically called after `POST /documents/{id}/apply-amendments`.
    """
    loi = await loi_service.get_loi(db, loi_id)
    if not loi:
        raise HTTPException(404, "Loi not found")
    try:
        result = await recalculation_service.recalculate_for_loi(db, loi_id)
        return result
    except Exception as e:
        logger.error(f"Recalculation error for loi {loi_id}: {e}")
        raise HTTPException(500, "Internal error during recalculation")


@router.post(
    "/lois/{loi_id}/recalculate-versions",
    response_model=RecalculationResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def recalculate_versions(
    loi_id: str,
    version_ids: list[str],
    db: Any = Depends(get_db),
):
    """
    Recalculate only specific ArticleVersions (targeted post-amendment refresh).

    Pass the `new_version_id` values returned by `POST /amendment-operations/{id}/apply`
    to restrict recalculation to only the affected articles.
    """
    loi = await loi_service.get_loi(db, loi_id)
    if not loi:
        raise HTTPException(404, "Loi not found")
    if not version_ids:
        raise HTTPException(422, "version_ids cannot be empty")
    try:
        result = await recalculation_service.recalculate_after_amendment(
            db, loi_id, version_ids
        )
        return result
    except Exception as e:
        logger.error(f"Targeted recalculation error: {e}")
        raise HTTPException(500, "Internal error during recalculation")


# ══════════════════════════════════════════════════════════════════════════════
# SPRINT 6 — ADMIN : STATS, VECTOR INDEX, PLATFORM MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/admin/stats", dependencies=[Depends(require_admin)])
async def get_admin_stats(db: Any = Depends(get_db)):
    """
    Global platform statistics for the admin dashboard.

    Returns counts for every major entity: documents, lois, articles,
    exigences, actions, criticalities, profiles, amendments, audit logs.
    """
    async def _count(collection_name: str, query: dict | None = None):
        return int(await db[collection_name].count_documents(query or {}))

    async def _count_by(collection_name: str, field: str, query: dict | None = None):
        rows = await db[collection_name].aggregate([
            {"$match": query or {}},
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
        ]).to_list(length=None)
        return {str(row["_id"]): row["count"] for row in rows if row.get("_id") is not None}

    total_docs = await _count("documents")
    docs_by_status = await _count_by("documents", "status")
    docs_by_type = await _count_by("documents", "document_type")
    docs_by_lang = await _count_by("documents", "language")

    total_chunks = await _count("chunks")

    total_lois = await _count("lois")

    total_articles = await _count("articles")
    total_versions = await _count("article_versions")
    versions_active = await _count("article_versions", {"status": "active"})
    versions_superseded = await _count("article_versions", {"status": "superseded"})
    versions_repealed = await _count("article_versions", {"status": "repealed"})

    total_exigences = await _count("exigences")
    exig_by_type = await _count_by("exigences", "exigence_type")

    total_actions = await _count("actions")
    actions_by_mod = await _count_by("actions", "modalite")
    total_crits = await _count("action_criticalities")
    crits_by_level = await _count_by("action_criticalities", "level")

    total_profiles = await _count("company_profiles")

    total_ops = await _count("amendment_operations")
    ops_by_status = await _count_by("amendment_operations", "status")
    ops_by_type = await _count_by("amendment_operations", "operation_type")

    total_logs = await _count("audit_logs")
    logs_by_event = await _count_by("audit_logs", "event_type")

    return {
        "documents": {
            "total": total_docs,
            "by_status": docs_by_status,
            "by_type": docs_by_type,
            "by_language": docs_by_lang,
        },
        "chunks": {"total": total_chunks},
        "lois": {"total": total_lois},
        "articles": {
            "total": total_articles,
            "versions": {
                "total": total_versions,
                "active": versions_active,
                "superseded": versions_superseded,
                "repealed": versions_repealed,
            },
        },
        "exigences": {"total": total_exigences, "by_type": exig_by_type},
        "actions": {
            "total": total_actions,
            "by_modalite": actions_by_mod,
            "criticalities": {"total": total_crits, "by_level": crits_by_level},
        },
        "profiles": {"total": total_profiles},
        "amendments": {
            "total": total_ops,
            "by_status": ops_by_status,
            "by_type": ops_by_type,
        },
        "audit_logs": {"total": total_logs, "by_event": logs_by_event},
    }


@router.get("/admin/vector-stats", dependencies=[Depends(require_admin)])
async def get_vector_stats(db: Any = Depends(get_db)):
    """
    Vector search status: backend availability, embedding counts, index info.
    """
    from app.services.search_service import get_vector_stats

    return await get_vector_stats(db)


@router.get("/admin/cache/stats", dependencies=[Depends(require_admin)])
async def get_cache_stats():
    return llm_cache.stats()


@router.post("/admin/cache/invalidate", dependencies=[Depends(require_admin)])
async def invalidate_cache():
    previous_size = len(llm_cache._store)
    llm_cache.invalidate_all()
    return {"cleared": True, "previous_size": previous_size}


@router.post("/admin/create-vector-index", status_code=201, dependencies=[Depends(require_admin)])
async def create_vector_index(
    index_type: str = Query("python-cosine", description="python-cosine"),
    db: Any = Depends(get_db),
):
    """
    Vector search is handled in Python over MongoDB embeddings in this deployment.
    """
    from app.services.search_service import create_vector_index

    return await create_vector_index(db, index_type=index_type)


@router.get("/admin/analytics", dependencies=[Depends(require_admin)])
async def get_analytics(
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    db: Any = Depends(get_db),
):
    """
    Dashboard analytics: Q&A usage, satisfaction, compliance coverage.

    Returns time-series data ready for charting (Chart.js / lightweight frontend).
    """
    from app.services.analytics_service import get_full_analytics

    return await get_full_analytics(db, days)


@router.post("/admin/reindex", dependencies=[Depends(require_admin)])
async def reindex_embeddings(
    db: Any = Depends(get_db),
):
    """
    Re-embed all documents from stored raw pages, rebuild chunks and FAISS index.

    This clears the chunks collection, rebuilds embeddings with the current model,
    then rebuilds the FAISS index.
    """
    from app.services.faiss_index import faiss_manager

    faiss_manager.mark_unavailable("reindexing")
    result = await document_service.reindex_all_documents(db)
    return {
        **result,
        "message": "Re-embedding complete; FAISS index rebuilt.",
    }


@router.get("/admin/notifications", dependencies=[Depends(require_admin)])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Any = Depends(get_db),
):
    """
    List alert notifications (amendment impacts, coverage drops, etc.).
    """
    from app.services.notification_service import list_notifications

    items, total = await list_notifications(db, skip=skip, limit=limit)
    return {"notifications": items, "total": total}


@router.post("/admin/notifications/{notification_id}/approve", dependencies=[Depends(require_admin)])
async def approve_notification(notification_id: str, db: Any = Depends(get_db)):
    notification = await db["notifications"].find_one({"id": notification_id})
    if not notification:
        raise HTTPException(404, "Notification not found")

    details = notification.get("details") or {}
    target_type = details.get("target_type")
    result: dict[str, Any] = {"notification_id": notification_id, "target_type": target_type}

    if notification.get("read"):
        return {**result, "status": "already_processed"}

    if target_type == "organization":
        org_id = details.get("organization_id")
        org = await auth_service.update_organization(org_id, {"status": "active"}) if org_id else None
        if not org:
            raise HTTPException(404, "Organization not found")
        result.update({"status": "approved", "organization_id": org_id})

    elif target_type == "invitation":
        invitation_id = details.get("invitation_id")
        inv = await auth_service.update_invitation_status(invitation_id, "pending") if invitation_id else None
        if not inv:
            raise HTTPException(404, "Invitation not found")
        org = await auth_service.get_organization(inv["organization_id"])
        await auth_service.update_invitation_expiry(invitation_id)
        await send_invitation_email(
            to_email=inv["email"],
            org_name=(org or {}).get("name", "Organisation"),
            token=inv["token"],
        )
        result.update({"status": "approved", "invitation_id": invitation_id})

    elif target_type == "document":
        doc_id = details.get("document_id")
        if not doc_id:
            raise HTTPException(422, "Missing document_id")
        processed = await document_service.approve_pending_document(db, doc_id)
        if processed.get("status") == "error":
            raise HTTPException(422, processed.get("error_message") or "Document processing failed")
        result.update({
            "status": "approved",
            "document_id": doc_id,
            "approved_document_id": processed.get("id"),
        })

    elif target_type == "amendment":
        doc_id = details.get("document_id")
        if not doc_id:
            raise HTTPException(422, "Missing document_id")
        processed = await document_service.approve_pending_amendment(db, doc_id)
        result.update({
            "status": "approved",
            "document_id": doc_id,
            "result": processed,
        })

    else:
        raise HTTPException(422, "Unsupported approval target")

    await db["notifications"].update_one(
        {"id": notification_id},
        {
            "$set": {
                "read": True,
                "details.approval_status": "approved",
                "details.approved_result": result,
                "processed_at": datetime.now(timezone.utc),
            }
        },
    )
    return result


@router.post("/admin/notifications/{notification_id}/reject", dependencies=[Depends(require_admin)])
async def reject_notification(notification_id: str, db: Any = Depends(get_db)):
    notification = await db["notifications"].find_one({"id": notification_id})
    if not notification:
        raise HTTPException(404, "Notification not found")

    details = notification.get("details") or {}
    target_type = details.get("target_type")
    result: dict[str, Any] = {"notification_id": notification_id, "target_type": target_type}

    if notification.get("read"):
        return {**result, "status": "already_processed"}

    if target_type == "organization":
        org_id = details.get("organization_id")
        org = await auth_service.update_organization(org_id, {"status": "rejected"}) if org_id else None
        if not org:
            raise HTTPException(404, "Organization not found")
        result.update({"status": "rejected", "organization_id": org_id})

    elif target_type == "invitation":
        invitation_id = details.get("invitation_id")
        inv = await auth_service.update_invitation_status(invitation_id, "rejected") if invitation_id else None
        if not inv:
            raise HTTPException(404, "Invitation not found")
        result.update({"status": "rejected", "invitation_id": invitation_id})

    elif target_type in ("document", "amendment"):
        doc_id = details.get("document_id")
        if not doc_id:
            raise HTTPException(422, "Missing document_id")
        rejected = await document_service.reject_pending_upload(db, doc_id)
        if not rejected:
            raise HTTPException(404, "Pending document not found")
        result.update({"status": "rejected", "document_id": doc_id})

    else:
        raise HTTPException(422, "Unsupported approval target")

    await db["notifications"].update_one(
        {"id": notification_id},
        {
            "$set": {
                "read": True,
                "details.approval_status": "rejected",
                "details.rejected_result": result,
                "processed_at": datetime.now(timezone.utc),
            }
        },
    )
    return result


@router.get("/admin/check-index-consistency", dependencies=[Depends(require_admin)])
async def check_index_consistency():
    """
    Check whether the FAISS index was built with the same embedding model
    that is currently configured.

    Returns a diagnostic JSON with ``ok=true`` if models match, or
    ``ok=false`` with a human-readable ``reason`` explaining the mismatch.
    This is a read-only diagnostic — it never modifies state.
    """
    from app.services.index_consistency_service import check_index_model_consistency

    result = await check_index_model_consistency()
    return {
        "ok": result.ok,
        "current_model": result.current_model,
        "current_dimension": result.current_dimension,
        "index_model": result.index_model,
        "index_dimension": result.index_dimension,
        "index_built_at": result.index_built_at,
        "message": result.reason,
    }


@router.post(
    "/company-profiles/{profile_id}/roadmap/export",
    dependencies=[Depends(require_api_key)],
)
async def export_roadmap(
    profile_id: str,
    format: str = Query("xlsx", description="Export format: xlsx | csv"),
    db: Any = Depends(get_db),
):
    """
    Export compliance roadmap as Excel (.xlsx) or CSV file.
    """
    from app.services.export_service import export_roadmap_file

    from fastapi.responses import Response

    content, media_type, filename = await export_roadmap_file(
        db, profile_id, format=format
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Chat History ─────────────────────────────────────────────────────────────


@router.get("/chat-history")
async def get_chat_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: str | None = Query(None),
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    """
    List chat history with role-based access:
    - member/viewer: own history only
    - admin/owner: all members of their organization
    - super_admin: no access (403)
    """
    if user["role"] == "super_admin":
        raise HTTPException(403, "Super admin cannot access company chat histories")

    query: dict = {}
    org_id = user.get("organization_id")

    if user["role"] in ("admin", "owner"):
        query["organization_id"] = org_id
        if user_id:
            query["user_id"] = user_id
    else:
        query["user_id"] = user["id"]

    total = await db["chat_history"].count_documents(query)
    cursor = db["chat_history"].find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    entries = await cursor.to_list(length=limit)

    user_ids = list({e["user_id"] for e in entries if e.get("user_id")})
    user_map: dict[str, str] = {}
    if user_ids:
        async for u in db["users"].find({"id": {"$in": user_ids}}, {"id": 1, "full_name": 1, "email": 1}):
            user_map[u["id"]] = u.get("full_name") or u.get("email", "?")

    for e in entries:
        e["user_name"] = user_map.get(e.get("user_id", ""), "?")
        if e.get("created_at"):
            e["created_at"] = e["created_at"].isoformat()

    return {"entries": entries, "total": total}


@router.delete("/chat-history/{entry_id}")
async def delete_chat_history_entry(
    entry_id: str,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_db),
):
    """Delete a single chat history entry (own entries or admin for org)."""
    entry = await db["chat_history"].find_one({"user_id": user["id"], "created_at": entry_id})
    if not entry:
        if user["role"] not in ("admin", "owner"):
            raise HTTPException(404, "Entry not found")
    result = await db["chat_history"].delete_one({"_id": entry["_id"]}) if entry else None
    if not result or result.deleted_count == 0:
        raise HTTPException(404, "Entry not found")
    return {"deleted": True}
