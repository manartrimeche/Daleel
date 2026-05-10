"""
Compliance Case Orchestrator — Sprint 10: Unified Case Workflow.

Transforms a live compliance case into findings, controls, and remediation items
by integrating conversation context, document analysis, and legal requirement
evaluation.

Architecture:
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLIANCE CASE ORCHESTRATOR                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Inputs:                                                                    │
│    • Case facts (from conversation_context)                                 │
│    • Message history                                                        │
│    • Attached documents with analysis                                       │
│    • Company profile (optional)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Processing Pipeline:                                                       │
│    1. Context Gathering      → case_service, case_conversation_service   │
│    2. Gap Analysis            → LLM evaluation of missing requirements     │
│    3. Applicability Check     → applicability_service                      │
│    4. Finding Generation      → LLM-powered non-compliance detection       │
│    5. Criticality Scoring   → criticality_service                        │
│    6. Action Prioritization → roadmap_service                            │
│    7. Evidence Mapping       → case_document_service                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Outputs:                                                                   │
│    • Case findings (legal/regulatory non-compliance)                       │
│    • Proposed controls                                                     │
│    • Remediation actions                                                   │
│    • Required evidences                                                    │
│    • Confidence/risk assessment                                            │
│    • Decision recommendation (ask/clarify/act/review)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Decision Triggers:                                                         │
│    • ASK        → facts_missing > threshold OR confidence < 0.6            │
│    • CLARIFY    → document analysis reveals contradictions                 │
│    • ACT        → sufficient facts + applicable exigences identified       │
│    • REVIEW     → critical finding with low confidence                   │
└─────────────────────────────────────────────────────────────────────────────┘

Integrates with:
  • llm_service.py           → Legal analysis and structured extraction
  • applicability_service.py → Determine applicable legal requirements
  • action_service.py        → Extract and manage compliance actions
  • criticality_service.py   → Score risk/criticality levels
  • roadmap_service.py       → Generate prioritized remediation plans
  • case_service.py          → CRUD for cases, findings, actions
  • case_document_service.py → Document analysis and evidence extraction
  • case_conversation_service.py → Context extraction from conversations
  • audit_service.py         → Audit logging
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.config import get_settings
from app.database import get_collection
from app.services import (
    action_service,
    applicability_service,
    audit_service,
    case_conversation_service,
    case_document_service,
    case_service,
    llm_service,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration & Constants
# ═══════════════════════════════════════════════════════════════════════════════

class OrchestratorDecision(str, Enum):
    """Decision types for case progression."""
    ASK = "ask"              # Request more information from user
    CLARIFY = "clarify"      # Resolve contradictions/ambiguities
    ACT = "act"              # Proceed with findings and actions
    REVIEW = "review"        # Recommend human expert review


class ConfidenceLevel(str, Enum):
    """Confidence assessment for findings."""
    HIGH = "high"      # ≥ 0.85
    MEDIUM = "medium"  # 0.60 - 0.84
    LOW = "low"        # < 0.60


# Thresholds for decision triggers
MIN_FACTS_FOR_ANALYSIS = 3          # Minimum known facts to proceed
MAX_MISSING_FACTS_TOLERANCE = 2     # Max missing facts before asking
MIN_CONFIDENCE_FOR_AUTO_ACT = 0.70  # Minimum confidence for automatic action
MIN_CONFIDENCE_FOR_FINDING = 0.60   # Minimum confidence to create a finding


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes for Internal State
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OrchestrationContext:
    """Internal context container for orchestration workflow."""
    case_id: str
    company_profile_id: Optional[str] = None
    facts_known: list[str] = field(default_factory=list)
    facts_missing: list[str] = field(default_factory=list)
    matter_type: str = "unknown"
    urgency: str = "unknown"
    article_references: list[str] = field(default_factory=list)
    document_analyses: list[dict] = field(default_factory=list)
    applicable_exigences: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    language: str = "fr"


@dataclass
class CaseGapAnalysis:
    """Result of gap analysis between case facts and legal requirements."""
    gaps: list[dict] = field(default_factory=list)
    violations: list[dict] = field(default_factory=list)
    recommendations: list[dict] = field(default_factory=list)
    overall_confidence: float = 0.0
    evidence_sufficiency: str = "insufficient"  # insufficient, partial, sufficient


@dataclass
class ProposedFinding:
    """A proposed finding ready for persistence."""
    title: str
    description: str
    severity: str  # critical, major, minor, observation
    exigence_id: Optional[str] = None
    article_references: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = ""  # conversation, document, combined


@dataclass
class ProposedAction:
    """A proposed remediation action."""
    title: str
    description: str
    finding_idx: int  # Index in proposed_findings list
    priority: str  # critical, high, medium, low
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    evidence_required: list[str] = field(default_factory=list)
    estimated_effort: str = "medium"  # small, medium, large


@dataclass
class OrchestrationResult:
    """Complete result of orchestration analysis."""
    decision: OrchestratorDecision
    decision_reason: str
    findings_created: list[dict] = field(default_factory=list)
    actions_created: list[dict] = field(default_factory=list)
    controls_proposed: list[dict] = field(default_factory=list)
    evidences_required: list[dict] = field(default_factory=list)
    proposed_findings: list[dict] = field(default_factory=list)
    proposed_actions: list[dict] = field(default_factory=list)
    clarification_question: Optional[str] = None
    human_review_reason: Optional[str] = None
    confidence_assessment: dict = field(default_factory=dict)
    risk_level: str = "unknown"
    next_steps: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def _confidence_to_level(score: float) -> ConfidenceLevel:
    if score >= 0.85:
        return ConfidenceLevel.HIGH
    if score >= 0.60:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _severity_from_gap(gap: dict) -> str:
    """Map gap type to finding severity."""
    gap_type = gap.get("type", "")
    if gap_type in ("violation", "non_compliance", "prohibition_breach"):
        return "critical" if gap.get("has_penalty", False) else "major"
    if gap_type in ("missing_document", "missing_process"):
        return "major"
    if gap_type == "recommendation":
        return "minor"
    return "observation"


def _detect_language(text: str) -> str:
    """Detect dominant language for prompts."""
    arabic_chars = len([c for c in text if "\u0600" <= c <= "\u06FF"])
    if arabic_chars >= 2:
        return "ar"
    # French-specific accented characters are strong indicators
    french_accents = set("àâãäæçèéêëîïôœùûüÿ")
    if any(c.lower() in french_accents for c in text):
        return "fr"
    french_markers = ["le", "la", "les", "des", "une", "est", "sont", "avec", "pour", "que", "qui"]
    lower = text.lower()
    french_count = sum(1 for m in french_markers if f" {m} " in f" {lower} ")
    if french_count >= 2:
        return "fr"
    return "en"


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Prompts
# ═══════════════════════════════════════════════════════════════════════════════

_GAP_ANALYSIS_PROMPT = """You are a Tunisian legal compliance expert performing a gap analysis.

**Case Context:**
Known Facts:
{facts_known}

Missing Information:
{facts_missing}

Matter Type: {matter_type}
Urgency: {urgency}
Article References: {article_refs}

**Document Analysis Summary:**
{document_summary}

**Applicable Legal Requirements (Exigences):**
{exigences_text}

**Your Task:**
Analyze the case context against the applicable legal requirements. Identify:
1. Gaps: missing compliance elements (documents, processes, actions)
2. Violations: actual or potential legal violations
3. Recommendations: best practice improvements

Respond ONLY with valid JSON:
{{
  "gaps": [
    {{
      "type": "violation|missing_document|missing_process|missing_action|recommendation",
      "description": "Clear description of the gap",
      "exigence_id": "ID if linked to specific exigence",
      "article_reference": "Art. X of Code Y",
      "has_penalty": true/false,
      "penalty_description": "Description of potential sanctions",
      "confidence": 0.0-1.0
    }}
  ],
  "violations": [
    {{
      "description": "Description of violation",
      "severity": "critical|major|minor",
      "article_reference": "Art. X of Code Y",
      "confidence": 0.0-1.0
    }}
  ],
  "recommendations": [
    {{
      "description": "Recommendation text",
      "priority": "high|medium|low",
      "rationale": "Why this helps"
    }}
  ],
  "overall_confidence": 0.0-1.0,
  "evidence_sufficiency": "insufficient|partial|sufficient"
}}

Rules:
- Be conservative: only identify gaps with reasonable certainty
- Confidence < 0.60 suggests need for more information
- evidence_sufficiency = sufficient only if documents clearly prove/disprove compliance
"""


_CONTROL_PROPOSAL_PROMPT = """You are a compliance control design expert.

**Finding:**
Title: {finding_title}
Description: {finding_description}
Severity: {severity}

**Case Context:**
{case_context}

**Your Task:**
Design compliance controls to prevent, detect, or remediate this finding.

Respond ONLY with valid JSON array:
[
  {{
    "control_type": "preventive|detective|corrective",
    "title": "Control title",
    "description": "How the control works",
    "frequency": "continuous|daily|weekly|monthly|quarterly|annual",
    "automation": "manual|semi_automated|automated",
    "owner_role": "Who should own this control",
    "evidence_type": "What evidence the control produces"
  }}
]
"""


_EVIDENCE_MAPPING_PROMPT = """You are mapping case findings to required evidence.

**Finding:**
{finding_description}

**Available Documents:**
{available_docs}

**Your Task:**
Identify what evidence is needed to prove remediation, and map to available documents.

Respond ONLY with valid JSON:
{{
  "evidences_required": [
    {{
      "evidence_type": "document|record|process|attestation",
      "description": "What evidence is needed",
      "source_document_id": "ID if matched to existing doc",
      "source_document_role": "evidence|policy|contract|other",
      "status": "available|partial|missing",
      "acquisition_steps": ["Step 1", "Step 2"]
    }}
  ]
}}
"""


_CLARIFICATION_QUESTION_PROMPT = """You are a legal compliance assistant. The case lacks sufficient information for a complete analysis.

**Case Context:**
Known Facts: {facts_known}
Missing Facts: {facts_missing}
Matter Type: {matter_type}

**Gap Analysis Result:**
{gap_summary}

**Your Task:**
Formulate ONE precise clarification question that will most improve the analysis.
The question should:
- Target a specific missing legal element
- Be answerable by the user (not requiring legal expertise)
- Help determine applicability of regulations
- Be professional and concise

Respond ONLY with valid JSON:
{{
  "question": "The clarification question",
  "target_info": "What information this seeks",
  "expected_impact": "How this improves analysis"
}}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Core Orchestration Functions
# ═══════════════════════════════════════════════════════════════════════════════

async def _gather_case_context(
    db,
    case_id: str,
) -> OrchestrationContext:
    """Gather all relevant context for the case."""
    # Get case basic info
    case = await case_service.get_case(db, case_id)
    if not case:
        raise ValueError(f"Case '{case_id}' not found")

    # Get conversation context
    conv_context = await case_conversation_service._load_conversation_context(case_id)

    # Get document analyses
    docs, _ = await case_document_service.list_case_documents_with_analysis(db, case_id)
    document_analyses = [d.get("analysis", {}) for d in docs if d.get("analysis")]

    # Detect language
    facts_text = " ".join(conv_context.get("facts_known", []))
    language = _detect_language(facts_text) if facts_text else "fr"

    return OrchestrationContext(
        case_id=case_id,
        company_profile_id=case.get("company_profile_id"),
        facts_known=conv_context.get("facts_known", []),
        facts_missing=conv_context.get("facts_missing", []),
        matter_type=conv_context.get("matter_type", "unknown"),
        urgency=conv_context.get("urgency", "unknown"),
        article_references=conv_context.get("article_references", []),
        document_analyses=document_analyses,
        language=language,
    )


async def _evaluate_applicability(
    ctx: OrchestrationContext,
) -> list[dict]:
    """Determine which legal requirements apply to this case."""
    if not ctx.company_profile_id:
        # No company profile - can't evaluate applicability
        # Return generic exigences based on matter_type
        return await _get_generic_exigences_for_matter(ctx.matter_type)

    # Get company profile
    profile = await applicability_service.get_company_profile(None, ctx.company_profile_id)
    if not profile:
        return await _get_generic_exigences_for_matter(ctx.matter_type)

    # Find relevant exigences based on matter type and article references
    exigence_query = {}
    if ctx.article_references:
        # Search for exigences linked to referenced articles
        # This is a simplified approach - in practice, you'd use more sophisticated matching
        exigence_query["article_reference"] = {"$in": ctx.article_references}

    exigences = await _collection("exigences").find(exigence_query).to_list(length=50)

    if not exigences:
        # Fallback: get exigences for matter type
        return await _get_generic_exigences_for_matter(ctx.matter_type)

    # Evaluate applicability for each
    applicable = []
    for ex in exigences:
        eval_result = await applicability_service.evaluate_exigence_applicability(
            profile, ex
        )
        if eval_result.get("is_applicable") and eval_result.get("confidence", 0) >= 0.6:
            applicable.append({
                "exigence": ex,
                "evaluation": eval_result,
            })

    return applicable


async def _get_generic_exigences_for_matter(matter_type: str) -> list[dict]:
    """Get generic exigences when no company profile exists."""
    # Map matter types to loi codes
    loi_mapping = {
        "labour_compliance": "code_travail",
        "corporate_formation": "code_societes",
        "corporate_governance": "code_societes",
        "contract_dispute": "code_obligations",
        "regulatory_compliance": None,
        "tax_compliance": "code_fiscal",
    }

    loi_code = loi_mapping.get(matter_type)
    if not loi_code:
        return []

    loi = await _collection("lois").find_one({"code": loi_code})
    if not loi:
        return []

    # Get some key articles
    articles = await _collection("articles").find(
        {"loi_id": loi["id"]}
    ).limit(10).to_list(length=None)

    article_ids = [a["id"] for a in articles]
    versions = await _collection("article_versions").find(
        {"article_id": {"$in": article_ids}, "status": "active"}
    ).to_list(length=None)

    version_ids = [v["id"] for v in versions]
    exigences = await _collection("exigences").find(
        {"article_version_id": {"$in": version_ids}}
    ).limit(20).to_list(length=None)

    return [{"exigence": ex, "evaluation": {"is_applicable": True, "confidence": 0.7}}
            for ex in exigences]


async def _perform_gap_analysis(
    ctx: OrchestrationContext,
    applicable_exigences: list[dict],
) -> CaseGapAnalysis:
    """Perform LLM-based gap analysis."""
    if not applicable_exigences:
        return CaseGapAnalysis(
            overall_confidence=0.3,
            evidence_sufficiency="insufficient",
            gaps=[],
            violations=[],
            recommendations=[],
        )

    # Build document summary
    doc_summaries = []
    for i, analysis in enumerate(ctx.document_analyses, 1):
        summary = analysis.get("summary", "")
        doc_type = analysis.get("document_type", "unknown")
        entities = analysis.get("entities", {})
        doc_summaries.append(
            f"Document {i} ({doc_type}): {summary[:200]}...\n"
            f"  Parties: {entities.get('parties', [])}\n"
            f"  Deadlines: {entities.get('deadlines', [])}\n"
            f"  Obligations: {entities.get('obligations', [])}"
        )

    # Build exigences text
    exigences_text = []
    for item in applicable_exigences[:10]:  # Limit to avoid token overflow
        ex = item["exigence"]
        exigences_text.append(
            f"- [{ex.get('id')}] {ex.get('exigence_type')}: {ex.get('text', '')[:300]}\n"
            f"  Article: {ex.get('article_reference', 'N/A')}"
        )

    prompt = _GAP_ANALYSIS_PROMPT.format(
        facts_known="\n".join(f"- {f}" for f in ctx.facts_known),
        facts_missing="\n".join(f"- {f}" for f in ctx.facts_missing),
        matter_type=ctx.matter_type,
        urgency=ctx.urgency,
        article_refs=", ".join(ctx.article_references) or "None",
        document_summary="\n\n".join(doc_summaries) or "No documents analyzed",
        exigences_text="\n".join(exigences_text),
    )

    try:
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a Tunisian legal compliance expert. Return ONLY valid JSON."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            base_url=settings.llm_base_url,
        )

        # Parse JSON
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text.strip())

        return CaseGapAnalysis(
            gaps=result.get("gaps", []),
            violations=result.get("violations", []),
            recommendations=result.get("recommendations", []),
            overall_confidence=result.get("overall_confidence", 0.5),
            evidence_sufficiency=result.get("evidence_sufficiency", "insufficient"),
        )
    except Exception as e:
        logger.error("Gap analysis LLM call failed: %s", e)
        return CaseGapAnalysis(
            overall_confidence=0.3,
            evidence_sufficiency="insufficient",
        )


async def _generate_findings(
    ctx: OrchestrationContext,
    gap_analysis: CaseGapAnalysis,
) -> list[ProposedFinding]:
    """Generate proposed findings from gap analysis."""
    findings = []

    # Generate from gaps
    for gap in gap_analysis.gaps:
        confidence = gap.get("confidence", 0.5)
        if confidence < MIN_CONFIDENCE_FOR_FINDING:
            continue

        findings.append(ProposedFinding(
            title=_generate_finding_title(gap),
            description=gap.get("description", ""),
            severity=_severity_from_gap(gap),
            exigence_id=gap.get("exigence_id"),
            article_references=[gap.get("article_reference")] if gap.get("article_reference") else [],
            confidence=confidence,
            source="gap_analysis",
        ))

    # Generate from violations
    for violation in gap_analysis.violations:
        confidence = violation.get("confidence", 0.5)
        if confidence < MIN_CONFIDENCE_FOR_FINDING:
            continue

        findings.append(ProposedFinding(
            title=f"Violation: {violation.get('description', '')[:80]}...",
            description=violation.get("description", ""),
            severity=violation.get("severity", "major"),
            article_references=[violation.get("article_reference")] if violation.get("article_reference") else [],
            confidence=confidence,
            source="violation_detection",
        ))

    return findings


def _generate_finding_title(gap: dict) -> str:
    """Generate a concise title for a finding."""
    gap_type = gap.get("type", "")
    description = gap.get("description", "")

    if gap_type == "missing_document":
        return f"Missing required document: {description[:60]}"
    if gap_type == "missing_process":
        return f"Process gap: {description[:60]}"
    if gap_type == "violation":
        return f"Potential violation: {description[:60]}"

    return f"Compliance gap: {description[:70]}"


async def _propose_controls(
    finding: ProposedFinding,
    ctx: OrchestrationContext,
) -> list[dict]:
    """Propose controls for a finding using LLM."""
    case_context = {
        "facts_known": ctx.facts_known,
        "matter_type": ctx.matter_type,
        "urgency": ctx.urgency,
    }

    prompt = _CONTROL_PROPOSAL_PROMPT.format(
        finding_title=finding.title,
        finding_description=finding.description,
        severity=finding.severity,
        case_context=json.dumps(case_context, ensure_ascii=False),
    )

    try:
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a compliance control design expert. Return ONLY valid JSON."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            base_url=settings.llm_base_url,
        )

        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        controls = json.loads(text.strip())
        return controls if isinstance(controls, list) else []
    except Exception as e:
        logger.warning("Control proposal failed: %s", e)
        return []


async def _generate_remediation_actions(
    finding: ProposedFinding,
    ctx: OrchestrationContext,
) -> list[ProposedAction]:
    """Generate remediation actions for a finding."""
    # First, try to find existing actions linked to the exigence
    actions = []
    if finding.exigence_id:
        existing = await action_service.get_actions_by_exigence(None, finding.exigence_id)
        for act in existing:
            actions.append(ProposedAction(
                title=act.get("action_precise", "")[:100],
                description=act.get("action_precise", ""),
                finding_idx=-1,  # Will be set by caller
                priority=_criticality_to_priority(act.get("criticality", {})),
                evidence_required=[act.get("preuve")] if act.get("preuve") else [],
            ))

    # If no existing actions, propose generic ones based on finding type
    if not actions:
        if finding.severity == "critical":
            actions.append(ProposedAction(
                title=f"Immediate remediation: {finding.title[:80]}",
                description=f"Address critical finding: {finding.description}",
                finding_idx=-1,
                priority="critical",
                due_date=_calculate_due_date(days=7),
            ))
        elif finding.severity == "major":
            actions.append(ProposedAction(
                title=f"Remediate: {finding.title[:80]}",
                description=f"Address finding: {finding.description}",
                finding_idx=-1,
                priority="high",
                due_date=_calculate_due_date(days=30),
            ))

    return actions


def _criticality_to_priority(criticality: dict) -> str:
    """Map criticality to action priority."""
    level = criticality.get("level", "secondaire")
    mapping = {
        "critique": "critical",
        "importante": "high",
        "secondaire": "medium",
    }
    return mapping.get(level, "medium")


def _calculate_due_date(days: int) -> datetime:
    """Calculate a due date N days from now."""
    from datetime import timedelta
    return _now() + timedelta(days=days)


async def _map_evidences(
    finding: ProposedFinding,
    ctx: OrchestrationContext,
) -> list[dict]:
    """Map finding to required and available evidences."""
    # Build available docs list
    available_docs = []
    for i, analysis in enumerate(ctx.document_analyses, 1):
        available_docs.append({
            "index": i,
            "type": analysis.get("document_type", "unknown"),
            "summary": analysis.get("summary", "")[:200],
        })

    prompt = _EVIDENCE_MAPPING_PROMPT.format(
        finding_description=finding.description,
        available_docs=json.dumps(available_docs, ensure_ascii=False),
    )

    try:
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a compliance evidence expert. Return ONLY valid JSON."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            base_url=settings.llm_base_url,
        )

        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text.strip())
        return result.get("evidences_required", [])
    except Exception as e:
        logger.warning("Evidence mapping failed: %s", e)
        return []


async def _determine_decision(
    ctx: OrchestrationContext,
    gap_analysis: CaseGapAnalysis,
    findings: list[ProposedFinding],
) -> tuple[OrchestratorDecision, str, Optional[str]]:
    """Determine the orchestration decision and reasoning."""
    # Check for insufficient facts
    if len(ctx.facts_missing) > MAX_MISSING_FACTS_TOLERANCE:
        if ctx.facts_missing:
            question = await _generate_clarification_question(ctx, gap_analysis)
            return (
                OrchestratorDecision.ASK,
                f"Missing {len(ctx.facts_missing)} critical facts needed for analysis",
                question,
            )

    # Check confidence
    if gap_analysis.overall_confidence < MIN_CONFIDENCE_FOR_AUTO_ACT:
        if len(ctx.facts_known) < MIN_FACTS_FOR_ANALYSIS:
            question = await _generate_clarification_question(ctx, gap_analysis)
            return (
                OrchestratorDecision.ASK,
                f"Insufficient confidence ({gap_analysis.overall_confidence:.2f}) and limited facts ({len(ctx.facts_known)})",
                question,
            )
        return (
            OrchestratorDecision.REVIEW,
            f"Low confidence in analysis ({gap_analysis.overall_confidence:.2f}) - human review recommended",
            None,
        )

    # Check for critical findings with low confidence
    critical_low_conf = [f for f in findings if f.severity == "critical" and f.confidence < 0.75]
    if critical_low_conf:
        return (
            OrchestratorDecision.REVIEW,
            "Critical findings with uncertain confidence require human review",
            None,
        )

    # Check for contradictions in documents
    if ctx.document_analyses:
        contradictions = _detect_document_contradictions(ctx.document_analyses)
        if contradictions:
            return (
                OrchestratorDecision.CLARIFY,
                f"Document contradictions detected: {contradictions[0]}",
                None,
            )

    # Sufficient information to act
    if findings:
        return (
            OrchestratorDecision.ACT,
            f"Analysis complete with {len(findings)} findings identified",
            None,
        )

    # No findings but sufficient info
    return (
        OrchestratorDecision.ACT,
        "Analysis complete - no compliance gaps identified",
        None,
    )


async def _generate_clarification_question(
    ctx: OrchestrationContext,
    gap_analysis: CaseGapAnalysis,
) -> str:
    """Generate a targeted clarification question."""
    gap_summary = f"Gaps: {len(gap_analysis.gaps)}, Violations: {len(gap_analysis.violations)}"

    prompt = _CLARIFICATION_QUESTION_PROMPT.format(
        facts_known=", ".join(ctx.facts_known),
        facts_missing=", ".join(ctx.facts_missing),
        matter_type=ctx.matter_type,
        gap_summary=gap_summary,
    )

    try:
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal compliance assistant. Return ONLY valid JSON."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            base_url=settings.llm_base_url,
        )

        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text.strip())
        return result.get("question", ctx.facts_missing[0] if ctx.facts_missing else "Please provide more details about your situation.")
    except Exception as e:
        logger.warning("Clarification question generation failed: %s", e)
        return ctx.facts_missing[0] if ctx.facts_missing else "Please provide more details about your situation."


def _detect_document_contradictions(analyses: list[dict]) -> list[str]:
    """Detect contradictions between document analyses."""
    # Simple heuristic: look for conflicting obligation dates
    contradictions = []

    deadlines = []
    for analysis in analyses:
        entities = analysis.get("entities", {})
        for deadline in entities.get("deadlines", []):
            deadlines.append({
                "date": deadline.get("date"),
                "description": deadline.get("description"),
            })

    # Check for same description, different dates
    from collections import defaultdict
    by_desc = defaultdict(list)
    for d in deadlines:
        # Normalize description
        desc = d["description"].lower().strip() if d["description"] else ""
        by_desc[desc].append(d["date"])

    for desc, dates in by_desc.items():
        unique_dates = set(d for d in dates if d)
        if len(unique_dates) > 1:
            contradictions.append(f"Conflicting deadlines for '{desc}': {unique_dates}")

    return contradictions


def _assess_risk_level(
    ctx: OrchestrationContext,
    findings: list[ProposedFinding],
    gap_analysis: CaseGapAnalysis,
) -> str:
    """Assess overall risk level."""
    from app.services import reasoning_model_service
    text = " ".join(ctx.facts_known)
    pred_risk, conf = reasoning_model_service.classify_risk(text)
    if pred_risk and reasoning_model_service.is_confident(conf):
        return pred_risk

    if any(f.severity == "critical" for f in findings):
        return "high"
    if any(f.severity == "major" for f in findings):
        return "medium"
    if gap_analysis.recommendations:
        return "low"
    return "minimal"


# ═══════════════════════════════════════════════════════════════════════════════
# Persistence Functions
# ═══════════════════════════════════════════════════════════════════════════════

async def _persist_findings(
    db,
    case_id: str,
    findings: list[ProposedFinding],
) -> list[dict]:
    """Persist proposed findings to database."""
    created = []
    for finding in findings:
        try:
            result = await case_service.create_finding(
                db,
                case_id,
                title=finding.title,
                description=finding.description,
                severity=finding.severity,
                exigence_id=finding.exigence_id,
                evidence_refs=finding.evidence_refs,
                article_references=finding.article_references,
            )
            created.append(result)
        except Exception as e:
            logger.error("Failed to create finding: %s", e)
    return created


async def _persist_actions(
    db,
    case_id: str,
    actions: list[ProposedAction],
    finding_ids: list[str],
) -> list[dict]:
    """Persist proposed actions to database."""
    created = []
    for action in actions:
        # Map finding_idx to actual finding_id
        finding_id = None
        if 0 <= action.finding_idx < len(finding_ids):
            finding_id = finding_ids[action.finding_idx]

        try:
            result = await case_service.create_case_action(
                db,
                case_id,
                title=action.title,
                description=action.description,
                finding_id=finding_id,
                priority=action.priority,
                due_date=action.due_date,
                assigned_to=action.assigned_to,
            )
            created.append(result)
        except Exception as e:
            logger.error("Failed to create action: %s", e)
    return created


# ═══════════════════════════════════════════════════════════════════════════════
# Main Orchestration Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

async def analyze_and_orchestrate(
    db,
    case_id: str,
    *,
    auto_create_findings: bool = False,
    auto_create_actions: bool = False,
    actor: str = "system",
) -> OrchestrationResult:
    """
    Main orchestration entry point.

    Analyzes a compliance case and determines the appropriate next steps,
    optionally creating findings and actions automatically.

    Args:
        db: Database connection
        case_id: The compliance case ID
        auto_create_findings: If True, persist findings to database
        auto_create_actions: If True, persist actions to database
        actor: Actor identifier for audit logging

    Returns:
        OrchestrationResult with decision, findings, actions, and next steps
    """
    logger.info("Starting orchestration for case %s", case_id)

    # Step 1: Gather context
    ctx = await _gather_case_context(db, case_id)

    # Step 2: Evaluate applicability
    applicable = await _evaluate_applicability(ctx)
    ctx.applicable_exigences = applicable

    # Step 3: Perform gap analysis
    gap_analysis = await _perform_gap_analysis(ctx, applicable)

    # Step 4: Generate findings
    proposed_findings = await _generate_findings(ctx, gap_analysis)

    # Step 5: Determine decision
    decision, decision_reason, clarification = await _determine_decision(
        ctx, gap_analysis, proposed_findings
    )

    # Prepare result
    result = OrchestrationResult(
        decision=decision,
        decision_reason=decision_reason,
        clarification_question=clarification,
        confidence_assessment={
            "overall": gap_analysis.overall_confidence,
            "level": _confidence_to_level(gap_analysis.overall_confidence).value,
            "evidence_sufficiency": gap_analysis.evidence_sufficiency,
        },
        risk_level=_assess_risk_level(ctx, proposed_findings, gap_analysis),
    )

    # Handle decision outcomes
    if decision == OrchestratorDecision.ASK:
        result.next_steps = ["Await user response to clarification question"]

    elif decision == OrchestratorDecision.CLARIFY:
        result.next_steps = ["Resolve document contradictions", "Request clarification from user"]

    elif decision == OrchestratorDecision.REVIEW:
        result.human_review_reason = decision_reason
        result.next_steps = [
            "Assign to compliance expert for review",
            "Flag case for manual analysis",
        ]

    elif decision == OrchestratorDecision.ACT:
        # Generate controls and actions
        controls = []
        actions = []
        evidences = []

        for i, finding in enumerate(proposed_findings):
            # Propose controls
            finding_controls = await _propose_controls(finding, ctx)
            controls.extend(finding_controls)

            # Generate remediation actions
            finding_actions = await _generate_remediation_actions(finding, ctx)
            for act in finding_actions:
                act.finding_idx = i
            actions.extend(finding_actions)

            # Map evidences
            finding_evidences = await _map_evidences(finding, ctx)
            evidences.extend(finding_evidences)

        result.controls_proposed = controls
        result.evidences_required = evidences
        result.proposed_findings = [
            {
                "title": f.title,
                "description": f.description,
                "severity": f.severity,
                "confidence": f.confidence,
                "exigence_id": f.exigence_id,
            }
            for f in proposed_findings
        ]
        result.proposed_actions = [
            {
                "title": a.title,
                "description": a.description,
                "priority": a.priority,
                "due_date": a.due_date,
            }
            for a in actions
        ]

        # Auto-create if requested and confidence sufficient
        if auto_create_findings and gap_analysis.overall_confidence >= MIN_CONFIDENCE_FOR_FINDING:
            created_findings = await _persist_findings(db, case_id, proposed_findings)
            result.findings_created = created_findings

            if auto_create_actions and created_findings:
                finding_ids = [f["id"] for f in created_findings]
                # Re-map actions to created finding IDs
                for action in actions:
                    if 0 <= action.finding_idx < len(finding_ids):
                        pass  # finding_idx already correct
                created_actions = await _persist_actions(db, case_id, actions, finding_ids)
                result.actions_created = created_actions

            # Log audit event
            await audit_service.log_event(
                db,
                "case_orchestrated",
                actor=actor,
                details={
                    "case_id": case_id,
                    "decision": decision.value,
                    "findings_created": len(result.findings_created),
                    "actions_created": len(result.actions_created),
                    "confidence": gap_analysis.overall_confidence,
                },
            )

        result.next_steps = [
            f"Review {len(proposed_findings)} identified findings",
            f"Prioritize {len(actions)} remediation actions",
            "Assign actions to responsible parties",
            "Schedule follow-up assessment",
        ]

    logger.info(
        "Orchestration complete for case %s: decision=%s, findings=%d, actions=%d",
        case_id,
        decision.value,
        len(result.findings_created) if hasattr(result, 'findings_created') else len(proposed_findings),
        len(result.actions_created) if hasattr(result, 'actions_created') else len(actions) if hasattr(result, 'proposed_actions') else 0,
    )

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Additional Utility Functions
# ═══════════════════════════════════════════════════════════════════════════════

async def get_orchestration_status(
    db,
    case_id: str,
) -> dict:
    """Get the current orchestration status for a case."""
    case = await case_service.get_case(db, case_id)
    if not case:
        return {"error": "Case not found"}

    # Get counts
    findings, findings_total, _, _ = await case_service.list_findings(db, case_id)
    actions, actions_total, _, _ = await case_service.list_case_actions(db, case_id)

    # Get conversation context
    conv_context = await case_conversation_service._load_conversation_context(case_id)

    return {
        "case_id": case_id,
        "status": case.get("status"),
        "ready_for_orchestration": (
            len(conv_context.get("facts_known", [])) >= MIN_FACTS_FOR_ANALYSIS or
            case.get("document_count", 0) > 0
        ),
        "facts_known_count": len(conv_context.get("facts_known", [])),
        "facts_missing_count": len(conv_context.get("facts_missing", [])),
        "findings_count": findings_total,
        "actions_count": actions_total,
        "orchestration_recommendation": (
            "ready" if len(conv_context.get("facts_known", [])) >= MIN_FACTS_FOR_ANALYSIS
            else "needs_more_info"
        ),
    }


async def suggest_next_questions(
    db,
    case_id: str,
    count: int = 3,
) -> list[str]:
    """Suggest next clarification questions for the case."""
    ctx = await _gather_case_context(db, case_id)

    if not ctx.facts_missing:
        return []

    # Return top N missing facts as questions
    suggestions = []
    for fact in ctx.facts_missing[:count]:
        # Convert fact statement to question
        if ctx.language == "fr":
            suggestions.append(f"Pouvez-vous préciser : {fact}?")
        elif ctx.language == "ar":
            suggestions.append(f"هل يمكنك التوضيح: {fact}؟")
        else:
            suggestions.append(f"Can you clarify: {fact}?")

    return suggestions


async def quick_assess(
    db,
    case_id: str,
) -> dict:
    """Quick assessment of case readiness and likely outcomes."""
    ctx = await _gather_case_context(db, case_id)

    # Simple heuristic assessment
    fact_score = min(len(ctx.facts_known) / MIN_FACTS_FOR_ANALYSIS, 1.0)
    doc_score = min(len(ctx.document_analyses) / 2, 1.0)  # 2+ docs = full score

    readiness = (fact_score * 0.6) + (doc_score * 0.4)

    return {
        "case_id": case_id,
        "readiness_score": round(readiness, 2),
        "readiness_level": "ready" if readiness >= 0.8 else "partial" if readiness >= 0.5 else "insufficient",
        "factors": {
            "facts_sufficiency": round(fact_score, 2),
            "document_support": round(doc_score, 2),
        },
        "suggestions": [
            "Add more context about the situation" if fact_score < 1.0 else None,
            "Attach supporting documents" if doc_score < 1.0 else None,
        ],
        "estimated_analysis_quality": (
            "high" if readiness >= 0.8 else
            "medium" if readiness >= 0.6 else
            "low"
        ),
    }
