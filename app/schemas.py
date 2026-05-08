"""
Pydantic schemas for API request / response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, ConfigDict, Field


# ── Document ──

class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    language: Optional[str] = None
    total_pages: Optional[int] = None
    total_chunks: int = 0
    ocr_used: bool = False
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentListOut(BaseModel):
    documents: List[DocumentOut]
    total: int


class DocumentSourceOut(BaseModel):
    id: str
    document_id: str
    source_path: str
    file_hash: str
    language: Optional[str] = None
    uploaded_at: datetime


# ── Chunk ──

class ChunkOut(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    text: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    language: Optional[str] = None
    ocr_used: bool = False
    char_count: Optional[int] = None


class ChunkListOut(BaseModel):
    chunks: List[ChunkOut]
    total: int
    document_id: str


class RawPageOut(BaseModel):
    id: str
    document_id: str
    page_number: int
    raw_text: str
    ocr_used: bool = False
    extracted_at: datetime


class RawPageListOut(BaseModel):
    raw_pages: List[RawPageOut]
    total: int
    document_id: str


class CleanedTextOut(BaseModel):
    id: str
    document_id: str
    page_number: int
    raw_page_id: Optional[str] = None
    version: int = 1
    cleaned_text: str
    transformation_rules: List[dict]
    rules_summary: Optional[str] = None
    cleaned_at: datetime


class CleanedTextListOut(BaseModel):
    cleaned_pages: List[CleanedTextOut]
    total: int
    document_id: str


class ExigenceOut(BaseModel):
    id: str
    document_id: str
    cleaned_text_id: Optional[str] = None
    page_number: int
    article_reference: Optional[str] = None
    exigence_type: str  # obligation|prohibition|condition|sanction
    text: str
    confidence_score: float
    source_citation: Optional[str] = None
    extracted_at: datetime


class ExigenceListOut(BaseModel):
    exigences: List[ExigenceOut]
    total: int
    document_id: str
    by_type: Optional[dict] = None  # e.g., {"obligation": 5, "prohibition": 3, ...}


# ── Search ──

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=100)
    language_filter: Optional[str] = Field(default=None, pattern=r"^(ar|fr|en|ar\+fr|unknown)$")
    document_id: Optional[str] = None


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    text: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    language: Optional[str] = None
    score: float  # cosine similarity


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


# ── Processing config override ──

class ProcessingConfig(BaseModel):
    chunk_size: int = Field(default=1000, ge=100, le=5000)
    chunk_overlap: int = Field(default=120, ge=0, le=500)


# ── Bulk upload ──

class BulkUploadResponse(BaseModel):
    total_files: int
    succeeded: int
    failed: int
    total_chunks: int
    documents: List[DocumentOut]


# ── LLM Q&A ──

class ChatMessage(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "Bonjour, je constitue une SARL et je veux connaître les obligations du gérant.",
            }
        }
    )

    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1)


class AskRequest(BaseModel):
    """POST /api/v1/ask — RAG sur les documents indexés."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": (
                    "Quelles sont les obligations du gérant d'une SARL "
                    "au regard du Code des sociétés commerciales ?"
                ),
                "top_k": 5,
                "language_filter": "fr",
                "document_id": None,
                "llm_model": None,
                "temperature": 0.3,
                "history": [
                    {
                        "role": "user",
                        "content": "Je prépare les statuts d'une SARL en Tunisie.",
                    },
                    {
                        "role": "assistant",
                        "content": "Sur quels aspects du gérant souhaitez-vous des précisions ?",
                    },
                ],
            }
        }
    )

    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    language_filter: Optional[str] = Field(default=None, pattern=r"^(ar|fr|en|ar\+fr|unknown)$")
    document_id: Optional[str] = None
    llm_model: Optional[str] = Field(default=None, min_length=1, max_length=120)
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)
    # Sprint 6+ toggles for domain-aware RAG and quality guard
    use_domain_router: bool = Field(default=True)
    use_quality_guard: Optional[bool] = Field(default=None)
    intent: Optional[str] = Field(default=None)


class SourceInfo(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "084c048f-7c98-48aa-bd59-d9ac00aeed1a",
                "filename": "Code des sociétés commerciales.pdf",
                "page_number": 12,
                "section": "Article 318",
                "language": "fr",
                "relevance_score": 0.87,
            }
        }
    )

    document_id: str
    filename: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    language: Optional[str] = None
    relevance_score: float


class AskResponse(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "answer": (
                    "D'après les extraits fournis [Source 1], le gérant doit agir avec "
                    "loyauté et diligence dans l'intérêt de la société. "
                    "Les sources citées détaillent également…"
                ),
                "sources": [
                    {
                        "document_id": "084c048f-7c98-48aa-bd59-d9ac00aeed1a",
                        "filename": "Code des sociétés commerciales.pdf",
                        "page_number": 12,
                        "section": "Article 318",
                        "language": "fr",
                        "relevance_score": 0.87,
                    }
                ],
                "model": "qwen2.5:7b",
                "chunks_used": 5,
            }
        }
    )

    answer: str
    sources: List[SourceInfo]
    model: str
    chunks_used: int
    # ── Sprint 6+ metadata (optional, backward-compatible) ──
    domain: Optional[str] = None
    quality_guard_status: Optional[str] = None
    quality_guard_issues: Optional[List[str]] = None
    kg_enriched: Optional[bool] = None


class AgenticAskResponse(AskResponse):
    reasoning_steps: List[str] = Field(default_factory=list)
    retrieval_attempts: int = 0
    rewritten_query: Optional[str] = None
    intent: Optional[str] = None
    route_decision: Optional[str] = None
    timings_ms: Optional[Dict[str, float]] = None
    selected_mode: Optional[str] = None
    auto_reason: Optional[str] = None


# ── Learning from user feedback ──

class FeedbackCreate(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    corrected_answer: str = Field(..., min_length=10, max_length=12000)
    language: Optional[str] = Field(default=None, pattern=r"^(ar|fr|en)$")
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    notes: Optional[str] = Field(default=None, max_length=2000)
    source_document_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list, max_length=20)


class FeedbackOut(BaseModel):
    id: str
    question: str
    corrected_answer: str
    language: str
    rating: Optional[int] = None
    notes: Optional[str] = None
    source_document_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class FeedbackListOut(BaseModel):
    items: List[FeedbackOut]
    total: int


# ── SPRINT 2 : PROFIL & APPLICABILITÉ ──

class CompanyProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    sector: Optional[str] = Field(None, max_length=128)
    size: Optional[str] = Field(None, pattern=r"^(micro|small|medium|large)$")
    employees: Optional[int] = Field(None, ge=0)
    activities: Optional[str] = None
    jurisdiction: str = Field(default="tunisia", max_length=64)
    notes: Optional[str] = None


class CompanyProfileOut(BaseModel):
    id: str
    name: str
    sector: Optional[str] = None
    size: Optional[str] = None
    employees: Optional[int] = None
    activities: Optional[str] = None
    jurisdiction: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CompanyProfileListOut(BaseModel):
    profiles: List[CompanyProfileOut]
    total: int


class ExigenceApplicabilityOut(BaseModel):
    id: str
    profile_id: str
    exigence_id: str
    is_applicable: bool
    explanation: Optional[str] = None
    confidence: float
    reasoning: dict
    calculated_at: datetime
    calculated_by: str


class ExigenceApplicabilityListOut(BaseModel):
    applicabilities: List[ExigenceApplicabilityOut]
    total: int
    applicable_count: int
    not_applicable_count: int


class ApplicabilityEvalRequest(BaseModel):
    """Request to evaluate applicability of exigences to a company profile"""
    profile_id: str
    exigence_ids: Optional[List[str]] = None  # If None, evaluate all exigences
    document_id: Optional[str] = None  # Filter by document


class ApplicabilityEvalResponse(BaseModel):
    """Response from applicability evaluation"""
    profile_id: str
    evaluated_exigences: int
    applicable: int
    not_applicable: int
    avg_confidence: float
    by_type: dict  # {obligation: {applicable: N, not_applicable: M}, ...}
    message: str


# ── SPRINT 3 : LOI → ARTICLE → ARTICLE_VERSION → ACTION ──────────────────

class LoiCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=32, description="Short unique code, e.g. 'CT', 'CS', 'LP63'")
    name: str = Field(..., min_length=1, max_length=512, description="Full name, e.g. 'Code du Travail'")
    jurisdiction: str = Field(default="tunisia", max_length=64)
    language: str = Field(default="fr", pattern=r"^(fr|ar|fr\+ar)$")
    description: Optional[str] = None
    version_label: Optional[str] = Field(None, max_length=128)


class LoiUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=512)
    jurisdiction: Optional[str] = Field(None, max_length=64)
    language: Optional[str] = Field(None, pattern=r"^(fr|ar|fr\+ar)$")
    description: Optional[str] = None
    version_label: Optional[str] = Field(None, max_length=128)


class LoiOut(BaseModel):
    id: str
    code: str
    name: str
    jurisdiction: str
    language: str
    description: Optional[str] = None
    version_label: Optional[str] = None
    total_articles: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class LoiListOut(BaseModel):
    lois: List[LoiOut]
    total: int


class HierarchyOut(BaseModel):
    titre: Optional[str] = None
    chapitre: Optional[str] = None
    section: Optional[str] = None


class ArticleOut(BaseModel):
    id: str
    loi_id: str
    article_key: str
    article_number: str
    article_heading: str
    hierarchy: HierarchyOut
    active_version_id: Optional[str] = None
    total_versions: Optional[int] = None
    created_at: datetime


class ArticleListOut(BaseModel):
    articles: List[ArticleOut]
    total: int
    loi_id: str


class ArticleVersionOut(BaseModel):
    id: str
    article_id: str
    article_key: Optional[str] = None
    version_num: int
    text: str
    status: str   # active | superseded | repealed
    language: str
    source_document_id: Optional[str] = None
    source_pages: List[int] = []
    effective_date: Optional[datetime] = None
    total_exigences: Optional[int] = None
    total_actions: Optional[int] = None
    created_at: datetime


class ArticleVersionListOut(BaseModel):
    versions: List[ArticleVersionOut]
    total: int
    article_id: str


class ActionOut(BaseModel):
    id: str
    exigence_id: str
    article_version_id: str
    modalite: str       # obligation | interdiction | sanction | condition
    action_precise: str
    conditions: List[str] = []
    preuve: Optional[str] = None
    confidence: float
    extracted_at: datetime


class ActionListOut(BaseModel):
    actions: List[ActionOut]
    total: int
    by_modalite: Optional[dict] = None


class SegmentDocumentRequest(BaseModel):
    document_id: str = Field(..., description="UUID of an already-uploaded document")
    language_override: Optional[str] = Field(
        None,
        pattern=r"^(fr|ar|fr\+ar)$",
        description="Override language detection for segmentation",
    )
    auto_extract_exigences: bool = Field(
        True,
        description=(
            "If true, extract exigences per newly created ArticleVersion immediately "
            "after segmentation."
        ),
    )
    auto_extract_actions: bool = Field(
        True,
        description=(
            "If true, also extract actions from newly extracted exigences. "
            "Ignored when auto_extract_exigences is false."
        ),
    )


class SegmentDocumentResponse(BaseModel):
    loi_id: str
    document_id: str
    articles_created: int
    articles_updated: int
    total_articles: int
    exigences_extracted: int = 0
    actions_extracted: int = 0
    message: str


class ExtractActionsRequest(BaseModel):
    exigence_ids: Optional[List[str]] = Field(
        None,
        description="Specific exigence IDs to extract actions from. If None, extract for all exigences of this ArticleVersion.",
    )


class ExtractActionsResponse(BaseModel):
    article_version_id: str
    exigences_processed: int
    actions_created: int
    message: str


# ── SPRINT 4 : CRITICITÉ & FEUILLE DE ROUTE ──────────────────────────────────

class ActionCriticalityOut(BaseModel):
    id: str
    action_id: str
    level: str          # critique | importante | secondaire
    score: float        # 0.0 – 1.0
    factors: List[str]
    computed_at: datetime
    computed_by: str    # rule-engine | llm


class ActionWithCriticalityOut(BaseModel):
    """Action enriched with its criticality level."""
    id: str
    exigence_id: str
    article_version_id: str
    modalite: str
    action_precise: str
    conditions: List[str] = []
    preuve: Optional[str] = None
    confidence: float
    extracted_at: datetime
    # Criticality (None if not yet computed)
    criticality_level: Optional[str] = None    # critique | importante | secondaire
    criticality_score: Optional[float] = None
    criticality_factors: Optional[List[str]] = None


class ComputeCriticalityRequest(BaseModel):
    action_ids: Optional[List[str]] = Field(
        None,
        description="Specific action IDs to compute. If None, compute for all actions of the scope.",
    )
    recompute: bool = Field(
        default=False,
        description="If true, recompute even if a criticality record already exists.",
    )


class ComputeCriticalityResponse(BaseModel):
    computed: int
    skipped: int
    by_level: dict   # {"critique": N, "importante": M, "secondaire": K}
    message: str


class ActionDependencyCreate(BaseModel):
    action_id: str
    depends_on_id: str
    dependency_type: str = Field(
        ...,
        pattern=r"^(prerequis|sequence|maintien)$",
        description="prerequis | sequence | maintien",
    )
    reason: Optional[str] = None


class ActionDependencyOut(BaseModel):
    id: str
    action_id: str
    depends_on_id: str
    dependency_type: str
    reason: Optional[str] = None
    created_at: datetime


class RoadmapActionOut(BaseModel):
    """One action in the ordered compliance roadmap."""
    position: int                         # 1-based order in the plan
    action_id: str
    article_version_id: str
    article_key: Optional[str] = None
    loi_code: Optional[str] = None
    modalite: str
    action_precise: str
    conditions: List[str] = []
    preuve: Optional[str] = None
    criticality_level: str                # critique | importante | secondaire
    criticality_score: float
    depends_on_ids: List[str] = []        # IDs of prerequisite actions


class RoadmapOut(BaseModel):
    """Dynamic compliance action plan for a company profile."""
    profile_id: str
    profile_name: str
    total_actions: int
    by_level: dict                        # {critique: N, importante: M, secondaire: K}
    ordered_plan: List[RoadmapActionOut]
    generated_at: datetime
    message: str


# ── SPRINT 5 : AMENDEMENTS & AUDIT ────────────────────────────────────────────

class ClassifyDocumentRequest(BaseModel):
    document_type: str = Field(
        ...,
        pattern=r"^(loi_principale|modificatif|autre)$",
        description="loi_principale | modificatif | autre",
    )
    loi_id: Optional[str] = Field(
        None,
        description="Associate document with a Loi (required for modificatif type)",
    )


class AmendmentOperationOut(BaseModel):
    id: str
    amendment_doc_id: str
    loi_id: str
    operation_type: str          # ADD | REPLACE | MODIFY | REPEAL
    target_article_key: str      # "CT-Art-95"
    target_article_number: str   # "95"
    new_text: Optional[str] = None
    proof_extract: str
    legal_reference: Optional[str] = None
    confidence: float
    status: str                  # pending | applied | rejected
    applied_at: Optional[datetime] = None
    old_version_id: Optional[str] = None
    new_version_id: Optional[str] = None
    created_at: datetime


class AmendmentOperationListOut(BaseModel):
    operations: List[AmendmentOperationOut]
    total: int
    document_id: str
    by_type: Optional[dict] = None      # {ADD: N, REPLACE: M, MODIFY: K, REPEAL: J}
    by_status: Optional[dict] = None    # {pending: N, applied: M, rejected: K}


class ExtractAmendmentsRequest(BaseModel):
    loi_id: str = Field(..., description="UUID of the Loi being amended")
    language_override: Optional[str] = Field(
        None,
        pattern=r"^(fr|ar|fr\+ar)$",
    )


class ExtractAmendmentsResponse(BaseModel):
    document_id: str
    loi_id: str
    operations_extracted: int
    by_type: dict
    message: str


class ApplyAmendmentResponse(BaseModel):
    operation_id: str
    operation_type: str
    target_article_key: str
    old_version_id: Optional[str] = None
    new_version_id: Optional[str] = None
    status: str
    message: str


class ApplyAllAmendmentsResponse(BaseModel):
    document_id: str
    total_pending: int
    applied: int
    failed: int
    results: List[ApplyAmendmentResponse]
    message: str


class AuditLogOut(BaseModel):
    id: str
    actor: str
    event_type: str
    loi_id: Optional[str] = None
    article_id: Optional[str] = None
    old_version_id: Optional[str] = None
    new_version_id: Optional[str] = None
    amendment_op_id: Optional[str] = None
    proof_extract: Optional[str] = None
    legal_reference: Optional[str] = None
    confidence: float
    details: dict
    created_at: datetime


class AuditLogListOut(BaseModel):
    logs: List[AuditLogOut]
    total: int


class RecalculationResponse(BaseModel):
    loi_id: str
    versions_processed: int
    exigences_extracted: int
    actions_extracted: int
    criticalities_computed: int
    message: str
