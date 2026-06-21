"""
Pydantic schemas for the Compliance Steering module.

Collections modelled:
  compliance_assessments     — gap analysis exercises
  controls                   — internal compliance controls
  control_evidences          — proof artifacts for controls
  requirement_control_links  — many-to-many requirement ↔ control join
  exception_register         — risk acceptances, waivers, deferred items
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Enum-like constants ───────────────────────────────────────────────────────

ASSESSMENT_STATUSES = ("draft", "in_progress", "completed", "archived")
ASSESSMENT_TYPES = ("initial", "periodic", "triggered")
CONTROL_TYPES = ("preventive", "detective", "corrective")
CONTROL_IMPL_STATUSES = ("planned", "in_progress", "implemented", "not_effective")
EVIDENCE_TYPES = ("document", "screenshot", "log", "certificate", "attestation", "report")
EVIDENCE_STATUSES = ("pending", "accepted", "rejected", "expired")
COVERAGE_STATUSES = ("not_covered", "partially_covered", "fully_covered")
EXCEPTION_TYPES = ("risk_acceptance", "compensating_control", "deferred", "waiver")
EXCEPTION_STATUSES = ("requested", "approved", "rejected", "expired", "remediated")
RISK_LEVELS = ("critical", "high", "medium", "low")
REVIEW_FREQUENCIES = ("monthly", "quarterly", "semi_annual", "annual")


# ═══════════════════════════════════════════════════════════════════════════════
# Compliance Assessments
# ═══════════════════════════════════════════════════════════════════════════════

class AssessmentCreate(BaseModel):
    company_profile_id: str
    title: str = Field(..., min_length=1, max_length=512)
    description: Optional[str] = Field(None, max_length=4000)
    assessment_type: str = Field(
        default="initial",
        pattern=r"^(initial|periodic|triggered)$",
    )
    owner: Optional[str] = Field(None, max_length=256)
    risk_level: str = Field(
        default="medium",
        pattern=r"^(critical|high|medium|low)$",
    )
    review_frequency: str = Field(
        default="annual",
        pattern=r"^(monthly|quarterly|semi_annual|annual)$",
    )
    due_date: Optional[datetime] = None
    created_by: str = Field(default="system", max_length=256)


class AssessmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    description: Optional[str] = Field(None, max_length=4000)
    status: Optional[str] = Field(
        None,
        pattern=r"^(draft|in_progress|completed|archived)$",
    )
    owner: Optional[str] = Field(None, max_length=256)
    risk_level: Optional[str] = Field(
        None,
        pattern=r"^(critical|high|medium|low)$",
    )
    review_frequency: Optional[str] = Field(
        None,
        pattern=r"^(monthly|quarterly|semi_annual|annual)$",
    )
    due_date: Optional[datetime] = None


class AssessmentOut(BaseModel):
    id: str
    company_profile_id: str
    title: str
    description: Optional[str] = None
    assessment_type: str
    status: str
    owner: Optional[str] = None
    risk_level: str
    overall_coverage_score: float = 0.0
    review_frequency: str
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    link_count: int = 0


class AssessmentListOut(BaseModel):
    assessments: List[AssessmentOut]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Controls
# ═══════════════════════════════════════════════════════════════════════════════

class ControlCreate(BaseModel):
    company_profile_id: str
    title: str = Field(..., min_length=1, max_length=512)
    description: str = Field(..., min_length=1, max_length=8000)
    control_type: str = Field(
        default="preventive",
        pattern=r"^(preventive|detective|corrective)$",
    )
    owner: Optional[str] = Field(None, max_length=256)
    risk_level: str = Field(
        default="medium",
        pattern=r"^(critical|high|medium|low)$",
    )
    review_frequency: str = Field(
        default="quarterly",
        pattern=r"^(monthly|quarterly|semi_annual|annual)$",
    )


class ControlUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    description: Optional[str] = Field(None, min_length=1, max_length=8000)
    control_type: Optional[str] = Field(
        None,
        pattern=r"^(preventive|detective|corrective)$",
    )
    implementation_status: Optional[str] = Field(
        None,
        pattern=r"^(planned|in_progress|implemented|not_effective)$",
    )
    owner: Optional[str] = Field(None, max_length=256)
    risk_level: Optional[str] = Field(
        None,
        pattern=r"^(critical|high|medium|low)$",
    )
    effectiveness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    review_frequency: Optional[str] = Field(
        None,
        pattern=r"^(monthly|quarterly|semi_annual|annual)$",
    )
    last_reviewed_at: Optional[datetime] = None
    next_review_date: Optional[datetime] = None


class ControlOut(BaseModel):
    id: str
    company_profile_id: str
    title: str
    description: str
    control_type: str
    implementation_status: str
    owner: Optional[str] = None
    risk_level: str
    effectiveness_score: float = 0.0
    review_frequency: str
    last_reviewed_at: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0
    linked_requirement_count: int = 0


class ControlListOut(BaseModel):
    controls: List[ControlOut]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Control Evidences
# ═══════════════════════════════════════════════════════════════════════════════

class EvidenceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    description: Optional[str] = Field(None, max_length=4000)
    evidence_type: str = Field(
        default="document",
        pattern=r"^(document|screenshot|log|certificate|attestation|report)$",
    )
    file_reference: Optional[str] = Field(None, max_length=1024)
    document_id: Optional[str] = None
    collected_by: str = Field(default="system", max_length=256)
    collected_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class EvidenceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    description: Optional[str] = Field(None, max_length=4000)
    status: Optional[str] = Field(
        None,
        pattern=r"^(pending|accepted|rejected|expired)$",
    )
    review_notes: Optional[str] = Field(None, max_length=4000)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class EvidenceOut(BaseModel):
    id: str
    control_id: str
    title: str
    description: Optional[str] = None
    evidence_type: str
    file_reference: Optional[str] = None
    document_id: Optional[str] = None
    collected_by: str
    collected_at: datetime
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: str
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EvidenceListOut(BaseModel):
    evidences: List[EvidenceOut]
    total: int
    control_id: str


# ═══════════════════════════════════════════════════════════════════════════════
# Requirement–Control Links
# ═══════════════════════════════════════════════════════════════════════════════

class ReqControlLinkCreate(BaseModel):
    exigence_id: str
    control_id: str
    assessment_id: Optional[str] = None
    coverage_status: str = Field(
        default="not_covered",
        pattern=r"^(not_covered|partially_covered|fully_covered)$",
    )
    coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    gap_description: Optional[str] = Field(None, max_length=4000)
    justification: Optional[str] = Field(None, max_length=4000)
    linked_by: str = Field(default="system", max_length=256)


class ReqControlLinkUpdate(BaseModel):
    coverage_status: Optional[str] = Field(
        None,
        pattern=r"^(not_covered|partially_covered|fully_covered)$",
    )
    coverage_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    gap_description: Optional[str] = Field(None, max_length=4000)
    justification: Optional[str] = Field(None, max_length=4000)


class ReqControlLinkOut(BaseModel):
    id: str
    exigence_id: str
    control_id: str
    assessment_id: Optional[str] = None
    coverage_status: str
    coverage_score: float
    gap_description: Optional[str] = None
    justification: Optional[str] = None
    linked_by: str
    created_at: datetime
    updated_at: datetime


class ReqControlLinkListOut(BaseModel):
    links: List[ReqControlLinkOut]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Exception Register
# ═══════════════════════════════════════════════════════════════════════════════

class ExceptionCreate(BaseModel):
    exigence_id: str
    company_profile_id: str
    control_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=512)
    description: str = Field(..., min_length=1, max_length=8000)
    exception_type: str = Field(
        default="risk_acceptance",
        pattern=r"^(risk_acceptance|compensating_control|deferred|waiver)$",
    )
    risk_level: str = Field(
        default="medium",
        pattern=r"^(critical|high|medium|low)$",
    )
    justification: str = Field(..., min_length=1, max_length=4000)
    expiry_date: Optional[datetime] = None
    remediation_action_id: Optional[str] = None
    review_frequency: str = Field(
        default="quarterly",
        pattern=r"^(monthly|quarterly|semi_annual|annual)$",
    )


class ExceptionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    description: Optional[str] = Field(None, min_length=1, max_length=8000)
    status: Optional[str] = Field(
        None,
        pattern=r"^(requested|approved|rejected|expired|remediated)$",
    )
    risk_level: Optional[str] = Field(
        None,
        pattern=r"^(critical|high|medium|low)$",
    )
    justification: Optional[str] = Field(None, min_length=1, max_length=4000)
    approved_by: Optional[str] = Field(None, max_length=256)
    expiry_date: Optional[datetime] = None
    remediation_action_id: Optional[str] = None


class ExceptionOut(BaseModel):
    id: str
    exigence_id: str
    company_profile_id: str
    control_id: Optional[str] = None
    title: str
    description: str
    exception_type: str
    status: str
    risk_level: str
    justification: str
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    remediation_action_id: Optional[str] = None
    review_frequency: str
    created_at: datetime
    updated_at: datetime


class ExceptionListOut(BaseModel):
    exceptions: List[ExceptionOut]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Compliance Posture (read-only computed views)
# ═══════════════════════════════════════════════════════════════════════════════

class RequirementGap(BaseModel):
    exigence_id: str
    exigence_title: Optional[str] = None
    coverage_status: str
    best_coverage_score: float = 0.0
    linked_controls: int = 0
    has_exception: bool = False


class RequirementCoverRequest(BaseModel):
    control_title: Optional[str] = Field(None, min_length=1, max_length=512)
    justification: Optional[str] = Field(None, max_length=4000)
    linked_by: str = Field(default="system", max_length=256)


class CoverageEvidenceMatch(BaseModel):
    source_type: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    control_id: Optional[str] = None
    evidence_id: Optional[str] = None
    document_id: Optional[str] = None
    score: float = 0.0


class CoverageSuggestion(BaseModel):
    exigence_id: str
    exigence_title: Optional[str] = None
    suggested_status: str
    confidence: float = 0.0
    rationale: str
    matches: List[CoverageEvidenceMatch] = Field(default_factory=list)


class CoverageSuggestionListOut(BaseModel):
    company_profile_id: str
    suggestions: List[CoverageSuggestion] = Field(default_factory=list)
    analyzed: int = 0
    generated_at: datetime


class CompliancePosture(BaseModel):
    company_profile_id: str
    total_applicable: int
    fully_covered: int
    partially_covered: int
    not_covered: int
    excepted: int
    overall_coverage_score: float = 0.0
    gaps: List[RequirementGap] = Field(default_factory=list)


class RemediationActionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    description: str = Field(..., min_length=1, max_length=8000)
    company_profile_id: str
    exigence_id: Optional[str] = None
    exception_id: Optional[str] = None
    assigned_to: Optional[str] = Field(None, max_length=256)
    due_date: Optional[datetime] = None
    priority: str = Field(
        default="medium",
        pattern=r"^(critical|high|medium|low)$",
    )
