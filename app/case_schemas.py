"""
Pydantic schemas for the Compliance Case Management module.

Collections modelled:
  compliance_cases   — central case object
  case_messages      — conversational thread per case
  case_documents     — documents attached to a case
  case_findings      — legal / regulatory findings
  case_actions       — remediation actions linked to findings
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Status / priority enums as literal strings ──────────────────────────────

CASE_STATUSES = ("open", "in_progress", "under_review", "resolved", "closed")
CASE_PRIORITIES = ("critical", "high", "medium", "low")
FINDING_SEVERITIES = ("critical", "major", "minor", "observation")
FINDING_STATUSES = ("identified", "confirmed", "mitigated", "resolved")
CASE_ACTION_STATUSES = ("pending", "in_progress", "completed", "cancelled")
MESSAGE_ROLES = ("user", "assistant", "system")

# Document roles for case attachments
DOCUMENT_ROLES = (
    "incoming_request",
    "evidence",
    "policy",
    "contract",
    "authority_notice",
    "draft_response",
    "other",
)

# Document types for analysis
DOCUMENT_TYPES = (
    "legal_opinion",
    "regulatory_filing",
    "court_decision",
    "administrative_notice",
    "contract",
    "policy_document",
    "correspondence",
    "evidence_material",
    "identification_document",
    "financial_record",
    "unknown",
)


# ═══════════════════════════════════════════════════════════════════════════════
# Compliance Case
# ═══════════════════════════════════════════════════════════════════════════════

class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    description: Optional[str] = Field(None, max_length=4000)
    company_profile_id: Optional[str] = None
    priority: str = Field(default="medium", pattern=r"^(critical|high|medium|low)$")
    assigned_to: Optional[str] = Field(None, max_length=256)
    tags: List[str] = Field(default_factory=list)
    created_by: str = Field(default="system", max_length=256)


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    description: Optional[str] = Field(None, max_length=4000)
    company_profile_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(open|in_progress|under_review|resolved|closed)$")
    priority: Optional[str] = Field(None, pattern=r"^(critical|high|medium|low)$")
    assigned_to: Optional[str] = Field(None, max_length=256)
    tags: Optional[List[str]] = None


class CaseOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    company_profile_id: Optional[str] = None
    status: str
    priority: str
    assigned_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_by: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    # Aggregated counts (populated by service)
    message_count: int = 0
    document_count: int = 0
    finding_count: int = 0
    action_count: int = 0


class CaseListOut(BaseModel):
    cases: List[CaseOut]
    total: int


class CaseSummaryOut(BaseModel):
    total_cases: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]


# ═══════════════════════════════════════════════════════════════════════════════
# Case Messages (conversation thread)
# ═══════════════════════════════════════════════════════════════════════════════

class CaseMessageCreate(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=16000)
    metadata: Optional[Dict] = None


class CaseMessageOut(BaseModel):
    id: str
    case_id: str
    role: str
    content: str
    metadata: Optional[Dict] = None
    created_at: datetime


class CaseMessageListOut(BaseModel):
    messages: List[CaseMessageOut]
    total: int
    case_id: str


# ═══════════════════════════════════════════════════════════════════════════════
# Case Documents (attachments linking to existing documents)
# ═══════════════════════════════════════════════════════════════════════════════

class DeadlineInfo(BaseModel):
    description: str
    date: Optional[str] = None  # ISO 8601 date string
    urgent: bool = False


class ObligationInfo(BaseModel):
    description: str
    deadline: Optional[str] = None
    source: Optional[str] = None  # Article/section reference


class LegalReferenceInfo(BaseModel):
    type: str = Field(default="article", pattern=r"^(article|law|regulation|code|section)$")
    number: Optional[str] = None
    law: Optional[str] = None


class MonetaryAmountInfo(BaseModel):
    amount: str
    currency: str = Field(default="TND")
    context: Optional[str] = None


class EntityExtractionResult(BaseModel):
    parties: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    deadlines: List[DeadlineInfo] = Field(default_factory=list)
    obligations: List[ObligationInfo] = Field(default_factory=list)
    legal_references: List[LegalReferenceInfo] = Field(default_factory=list)
    monetary_amounts: List[MonetaryAmountInfo] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DocumentAnalysis(BaseModel):
    document_type: str = Field(default="unknown", pattern=r"^(legal_opinion|regulatory_filing|court_decision|administrative_notice|contract|policy_document|correspondence|evidence_material|identification_document|financial_record|unknown)$")
    language: str = Field(default="unknown")
    summary: str = Field(default="", max_length=2000)
    entities: EntityExtractionResult = Field(default_factory=EntityExtractionResult)
    ocr_used: bool = False
    analyzed_at: Optional[datetime] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    text_sample: Optional[str] = Field(None, max_length=1000)


class CaseDocumentAttach(BaseModel):
    """Attach an existing document to a case."""
    document_id: str
    role: str = Field(default="other", pattern=r"^(incoming_request|evidence|policy|contract|authority_notice|draft_response|other)$")
    label: Optional[str] = Field(None, max_length=256)
    attached_by: str = Field(default="system", max_length=256)
    run_analysis: bool = True


class CaseDocumentUpload(BaseModel):
    """Upload and attach a new document to a case."""
    role: str = Field(default="other", pattern=r"^(incoming_request|evidence|policy|contract|authority_notice|draft_response|other)$")
    label: Optional[str] = Field(None, max_length=256)
    attached_by: str = Field(default="system", max_length=256)
    run_analysis: bool = True


class CaseDocumentOut(BaseModel):
    id: str
    case_id: str
    document_id: str
    role: str = Field(default="other")
    label: Optional[str] = None
    attached_by: str
    attached_at: datetime
    analysis: Optional[DocumentAnalysis] = None


class CaseDocumentWithDetailsOut(BaseModel):
    """Case document with full document info and analysis."""
    id: str
    case_id: str
    document_id: str
    role: str
    label: Optional[str] = None
    attached_by: str
    attached_at: datetime
    analysis: Optional[DocumentAnalysis] = None
    document: Optional[dict] = None  # Simplified document info


class CaseDocumentListOut(BaseModel):
    documents: List[CaseDocumentOut]
    total: int
    case_id: str


class CaseDocumentUploadOut(BaseModel):
    """Response after uploading and attaching a document."""
    case_document: CaseDocumentOut
    document: dict  # Document processing result
    analysis: Optional[DocumentAnalysis] = None


class DocumentAnalysisOut(BaseModel):
    """Analysis result for a case document."""
    document_id: str
    case_document_id: str
    document_type: str
    language: str
    summary: str
    entities: EntityExtractionResult
    ocr_used: bool
    analyzed_at: datetime
    confidence: float


# ═══════════════════════════════════════════════════════════════════════════════
# Case Findings (legal / regulatory non-compliance findings)
# ═══════════════════════════════════════════════════════════════════════════════

class CaseFindingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    description: str = Field(..., min_length=1, max_length=8000)
    severity: str = Field(default="major", pattern=r"^(critical|major|minor|observation)$")
    exigence_id: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    article_references: List[str] = Field(default_factory=list)


class CaseFindingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    description: Optional[str] = Field(None, min_length=1, max_length=8000)
    severity: Optional[str] = Field(None, pattern=r"^(critical|major|minor|observation)$")
    status: Optional[str] = Field(None, pattern=r"^(identified|confirmed|mitigated|resolved)$")
    evidence_refs: Optional[List[str]] = None
    article_references: Optional[List[str]] = None


class CaseFindingOut(BaseModel):
    id: str
    case_id: str
    exigence_id: Optional[str] = None
    title: str
    description: str
    severity: str
    status: str
    evidence_refs: List[str] = Field(default_factory=list)
    article_references: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CaseFindingListOut(BaseModel):
    findings: List[CaseFindingOut]
    total: int
    case_id: str
    by_severity: Optional[Dict[str, int]] = None
    by_status: Optional[Dict[str, int]] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Case Actions (remediation / compliance tasks)
# ═══════════════════════════════════════════════════════════════════════════════

class CaseActionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    description: str = Field(..., min_length=1, max_length=8000)
    finding_id: Optional[str] = None
    action_id: Optional[str] = None  # FK to existing actions collection
    assigned_to: Optional[str] = Field(None, max_length=256)
    due_date: Optional[datetime] = None
    priority: str = Field(default="medium", pattern=r"^(critical|high|medium|low)$")


class CaseActionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    description: Optional[str] = Field(None, min_length=1, max_length=8000)
    status: Optional[str] = Field(None, pattern=r"^(pending|in_progress|completed|cancelled)$")
    assigned_to: Optional[str] = Field(None, max_length=256)
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, pattern=r"^(critical|high|medium|low)$")
    completion_notes: Optional[str] = Field(None, max_length=4000)


class CaseActionOut(BaseModel):
    id: str
    case_id: str
    finding_id: Optional[str] = None
    action_id: Optional[str] = None
    title: str
    description: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str
    priority: str
    completion_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class CaseActionListOut(BaseModel):
    actions: List[CaseActionOut]
    total: int
    case_id: str
    by_status: Optional[Dict[str, int]] = None
    by_priority: Optional[Dict[str, int]] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Case Conversation Workflow — progressive fact-gathering
# ═══════════════════════════════════════════════════════════════════════════════

MATTER_TYPES = (
    "labour_compliance",
    "corporate_formation",
    "corporate_governance",
    "contract_dispute",
    "regulatory_compliance",
    "tax_compliance",
    "intellectual_property",
    "data_protection",
    "other",
)

URGENCY_LEVELS = ("critical", "high", "medium", "low", "unknown")


class CaseConversationContext(BaseModel):
    """Structured context extracted progressively from the case conversation."""
    facts_known: List[str] = Field(default_factory=list)
    facts_missing: List[str] = Field(default_factory=list)
    matter_type: Optional[str] = None
    urgency: str = Field(default="unknown")
    next_question: Optional[str] = None
    article_references: List[str] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class ConversationStartIn(BaseModel):
    """Input for creating a new case from a user-described situation."""
    situation: str = Field(..., min_length=10, max_length=16000)
    company_profile_id: Optional[str] = None
    created_by: str = Field(default="user", max_length=256)


class ConversationMessageIn(BaseModel):
    """Input for sending a follow-up message in a case conversation."""
    content: str = Field(..., min_length=1, max_length=16000)


class ConversationTurnOut(BaseModel):
    """Output after each conversational exchange (user msg + assistant reply)."""
    case_id: str
    user_message: CaseMessageOut
    assistant_message: CaseMessageOut
    context: CaseConversationContext


class CaseConversationSummaryOut(BaseModel):
    """Structured summary of a case's conversational context."""
    case_id: str
    title: str
    status: str
    priority: str
    context: CaseConversationContext
    message_count: int
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# Case Orchestration Workflow — Sprint 10
# ═══════════════════════════════════════════════════════════════════════════════

ORCHESTRATION_DECISIONS = ("ask", "clarify", "act", "review")
CONFIDENCE_LEVELS = ("high", "medium", "low")
RISK_LEVELS = ("high", "medium", "low", "minimal", "unknown")


class ProposedFinding(BaseModel):
    """A finding proposed by the orchestrator."""
    title: str
    description: str
    severity: str = Field(pattern=r"^(critical|major|minor|observation)$")
    confidence: float = Field(ge=0.0, le=1.0)
    exigence_id: Optional[str] = None


class ProposedControl(BaseModel):
    """A control proposed for a finding."""
    control_type: str = Field(pattern=r"^(preventive|detective|corrective)$")
    title: str
    description: str
    frequency: str = Field(pattern=r"^(continuous|daily|weekly|monthly|quarterly|annual)$")
    automation: str = Field(pattern=r"^(manual|semi_automated|automated)$")
    owner_role: str
    evidence_type: str


class ProposedAction(BaseModel):
    """A remediation action proposed by the orchestrator."""
    title: str
    description: str
    priority: str = Field(pattern=r"^(critical|high|medium|low)$")
    due_date: Optional[datetime] = None
    finding_title: Optional[str] = None  # For linking to proposed finding


class RequiredEvidence(BaseModel):
    """Evidence required for compliance."""
    evidence_type: str = Field(pattern=r"^(document|record|process|attestation)$")
    description: str
    source_document_id: Optional[str] = None
    source_document_role: Optional[str] = None
    status: str = Field(pattern=r"^(available|partial|missing)$")
    acquisition_steps: List[str] = Field(default_factory=list)


class ConfidenceAssessment(BaseModel):
    """Confidence assessment for orchestration."""
    overall: float = Field(ge=0.0, le=1.0)
    level: str = Field(pattern=r"^(high|medium|low)$")
    evidence_sufficiency: str = Field(pattern=r"^(insufficient|partial|sufficient)$")


class OrchestrationIn(BaseModel):
    """Input for running case orchestration."""
    auto_create_findings: bool = Field(default=False, description="Automatically persist findings to database")
    auto_create_actions: bool = Field(default=False, description="Automatically persist actions to database")


class OrchestrationOut(BaseModel):
    """Output from case orchestration analysis."""
    case_id: str
    decision: str = Field(pattern=r"^(ask|clarify|act|review)$")
    decision_reason: str
    proposed_findings: List[ProposedFinding] = Field(default_factory=list)
    findings_created: List[CaseFindingOut] = Field(default_factory=list)
    proposed_actions: List[ProposedAction] = Field(default_factory=list)
    actions_created: List[CaseActionOut] = Field(default_factory=list)
    controls_proposed: List[ProposedControl] = Field(default_factory=list)
    evidences_required: List[RequiredEvidence] = Field(default_factory=list)
    clarification_question: Optional[str] = None
    human_review_reason: Optional[str] = None
    confidence_assessment: ConfidenceAssessment
    risk_level: str = Field(pattern=r"^(high|medium|low|minimal|unknown)$")
    next_steps: List[str] = Field(default_factory=list)


class OrchestrationStatusOut(BaseModel):
    """Status of case readiness for orchestration."""
    case_id: str
    status: str
    ready_for_orchestration: bool
    facts_known_count: int
    facts_missing_count: int
    findings_count: int
    actions_count: int
    orchestration_recommendation: str


class QuickAssessmentOut(BaseModel):
    """Quick assessment of case readiness."""
    case_id: str
    readiness_score: float
    readiness_level: str
    factors: dict
    suggestions: List[Optional[str]]
    estimated_analysis_quality: str


class NextQuestionsOut(BaseModel):
    """Suggested next clarification questions."""
    case_id: str
    questions: List[str]


# ═══════════════════════════════════════════════════════════════════════════════
# Advisor Response Composer Schemas (Sprint 10 Extension)
# ═══════════════════════════════════════════════════════════════════════════════

class UnderstoodFactOut(BaseModel):
    """A fact understood from conversation or documents."""
    fact: str
    source: str = Field(..., description="user_statement, document, or inferred")
    confidence: float = Field(..., ge=0.0, le=1.0)


class MissingInfoItemOut(BaseModel):
    """An item of missing information."""
    item: str
    importance: str = Field(..., pattern=r"^(critical|important|helpful)$")
    reason: str
    suggested_question: Optional[str] = None


class LegalBasisItemOut(BaseModel):
    """A legal basis reference."""
    article_reference: str
    law_name: Optional[str] = None
    summary: str = ""
    relevance: str = Field(default="direct", pattern=r"^(direct|analogous|contextual)$")
    url: Optional[str] = None


class ComplianceRiskOut(BaseModel):
    """A compliance risk with severity and impact."""
    risk_description: str
    severity: str = Field(..., pattern=r"^(critical|high|medium|low)$")
    potential_impact: str
    likelihood: str = Field(..., pattern=r"^(certain|probable|possible|remote)$")
    legal_consequences: Optional[str] = None
    financial_consequences: Optional[str] = None
    operational_consequences: Optional[str] = None


class RecommendedActionOut(BaseModel):
    """A recommended remediation action."""
    action_description: str
    priority: str = Field(..., pattern=r"^(critical|high|medium|low)$")
    deadline: Optional[str] = None
    responsible_party: Optional[str] = None
    estimated_effort: Optional[str] = Field(None, pattern=r"^(small|medium|large)$")
    related_finding: Optional[str] = None
    legal_basis: Optional[str] = None


class RequiredEvidenceOut(BaseModel):
    """Required evidence or document."""
    evidence_type: str
    description: str
    purpose: str
    urgency: str = Field(..., pattern=r"^(immediate|soon|eventually)$")
    format_hint: Optional[str] = None


class ConfidenceAssessmentOut(BaseModel):
    """Confidence assessment with factors."""
    overall_score: float = Field(..., ge=0.0, le=1.0)
    level: str = Field(..., pattern=r"^(high|medium|low)$")
    indicator: str
    factors_supporting: List[str] = Field(default_factory=list)
    factors_limiting: List[str] = Field(default_factory=list)
    disclaimer: str


class HumanReviewRecommendationOut(BaseModel):
    """Human expert review recommendation."""
    is_recommended: bool
    reason: Optional[str] = None
    recommended_expertise: Optional[str] = None
    urgency: Optional[str] = None


class AdvisorResponseOut(BaseModel):
    """Complete structured advisor response."""
    response_id: str
    case_id: str
    language: str = "fr"
    tone: str = Field(default="professional", pattern=r"^(formal|professional|cautious|educational)$")
    generated_at: datetime

    # Core sections
    what_i_understood: List[UnderstoodFactOut]
    what_is_missing: List[MissingInfoItemOut]
    legal_basis: List[LegalBasisItemOut]
    compliance_risks: List[ComplianceRiskOut]
    recommended_actions: List[RecommendedActionOut]
    required_evidence: List[RequiredEvidenceOut]
    confidence_assessment: ConfidenceAssessmentOut
    human_review_recommendation: HumanReviewRecommendationOut

    # Rendering
    markdown_rendering: str


class AdvisorResponseCreate(BaseModel):
    """Input for creating an advisor response."""
    case_id: str
    orchestration_result: Dict[str, Any]
    conversation_context: Dict[str, Any]
    document_analyses: List[Dict[str, Any]] = Field(default_factory=list)
    legal_context: List[Dict[str, Any]] = Field(default_factory=list)
    language: str = "fr"
    tone: str = Field(default="professional", pattern=r"^(formal|professional|cautious|educational)$")
    use_llm_refinement: bool = True
