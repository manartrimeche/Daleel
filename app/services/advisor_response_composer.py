"""
Advisor Response Composer — Professional Legal Compliance Response Formatter.

Transforms technical orchestration outputs into structured, professional,
client-friendly legal compliance advice. Maintains a cautious, structured tone
suitable for legal advisory contexts.

Architecture:
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADVISOR RESPONSE COMPOSER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Inputs:                                                                    │
│    • Case facts and conversation context                                    │
│    • Legal context (retrieved articles, exigences)                          │
│    • Case findings (violations, gaps, risks)                              │
│    • Remediation actions with priorities                                    │
│    • Confidence and risk signals                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Processing:                                                                │
│    1. Context Synthesis    → What I understood                              │
│    2. Gap Analysis         → What is still missing                          │
│    3. Legal Grounding    → Legal basis                                    │
│    4. Risk Assessment      → Compliance risks                               │
│    5. Action Planning    → Recommended actions                            │
│    6. Evidence Mapping    → Required evidence                               │
│    7. Confidence Statement → Confidence level + disclaimer                  │
│    8. Review Recommendation → Human review if needed                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Output:                                                                    │
│    • StructuredAdvisorResponse (8 sections)                                 │
│    • Markdown-formatted advisory text                                       │
│    • LLM prompt templates for style consistency                             │
└─────────────────────────────────────────────────────────────────────────────┘

Integrates with:
  • compliance_case_orchestrator.py  → OrchestrationResult input
  • llm_service.py                    → Style refinement and language detection
  • case_schemas.py                   → Response schema validation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.config import get_settings
from app.services import llm_service, llm_style_formatter

logger = logging.getLogger(__name__)
settings = get_settings()


# ═══════════════════════════════════════════════════════════════════════════════
# Enums and Constants
# ═══════════════════════════════════════════════════════════════════════════════

class AdvisoryTone(str, Enum):
    """Tone variants for different client contexts."""
    FORMAL = "formal"          # Corporate legal departments
    PROFESSIONAL = "professional"  # Standard business advisory
    CAUTIOUS = "cautious"      # High-risk situations
    EDUCATIONAL = "educational"  # Training/explaining contexts


class ConfidenceIndicator(str, Enum):
    """Visual confidence indicators for UI rendering."""
    HIGH = "●●●"      # 3 dots
    MEDIUM = "●●○"    # 2 dots
    LOW = "●○○"       # 1 dot
    UNKNOWN = "○○○"   # 0 dots


class RiskIndicator(str, Enum):
    """Visual risk level indicators."""
    CRITICAL = "🔴"
    HIGH = "🟠"
    MEDIUM = "🟡"
    LOW = "🟢"
    UNKNOWN = "⚪"


# Section ordering and metadata
SECTION_ORDER = [
    "what_i_understood",
    "what_is_missing",
    "legal_basis",
    "compliance_risks",
    "recommended_actions",
    "required_evidence",
    "confidence_assessment",
    "human_review_recommendation",
]

SECTION_TITLES_FR = {
    "what_i_understood": "Ce que j'ai compris de votre situation",
    "what_is_missing": "Informations complémentaires nécessaires",
    "legal_basis": "Fondement juridique applicable",
    "compliance_risks": "Risques de conformité identifiés",
    "recommended_actions": "Actions recommandées",
    "required_evidence": "Documents et preuves requis",
    "confidence_assessment": "Niveau de confiance de l'analyse",
    "human_review_recommendation": "Recommandation d'expertise humaine",
}

SECTION_TITLES_AR = {
    "what_i_understood": "ما فهمته من وضعيتكم",
    "what_is_missing": "المعلومات الإضافية المطلوبة",
    "legal_basis": "الأساس القانوني المطبق",
    "compliance_risks": "المخاطر التنظيمية المحددة",
    "recommended_actions": "الإجراءات الموصى بها",
    "required_evidence": "المستندات والأدلة المطلوبة",
    "confidence_assessment": "مستوى ثقة التحليل",
    "human_review_recommendation": "توصية بمراجعة خبيرة بشرية",
}

SECTION_TITLES_EN = {
    "what_i_understood": "What I understood from your situation",
    "what_is_missing": "Additional information required",
    "legal_basis": "Applicable legal basis",
    "compliance_risks": "Identified compliance risks",
    "recommended_actions": "Recommended actions",
    "required_evidence": "Required documents and evidence",
    "confidence_assessment": "Analysis confidence level",
    "human_review_recommendation": "Human expert review recommendation",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class UnderstoodFact:
    """A fact extracted and understood from conversation."""
    fact: str
    source: str  # "user_statement", "document", "inferred"
    confidence: float = 1.0


@dataclass
class MissingInfoItem:
    """An item of missing information."""
    item: str
    importance: str  # "critical", "important", "helpful"
    reason: str  # Why this information is needed
    suggested_question: Optional[str] = None


@dataclass
class LegalBasisItem:
    """A legal basis reference."""
    article_reference: str
    law_name: Optional[str] = None
    summary: str = ""
    relevance: str = "direct"  # "direct", "analogous", "contextual"
    url: Optional[str] = None


@dataclass
class ComplianceRisk:
    """A compliance risk with severity and mitigation."""
    risk_description: str
    severity: str  # "critical", "high", "medium", "low"
    potential_impact: str
    likelihood: str  # "certain", "probable", "possible", "remote"
    legal_consequences: Optional[str] = None
    financial_consequences: Optional[str] = None
    operational_consequences: Optional[str] = None


@dataclass
class RecommendedAction:
    """A recommended remediation action."""
    action_description: str
    priority: str  # "critical", "high", "medium", "low"
    deadline: Optional[str] = None  # e.g., "30 days", "Before 2024-12-31"
    responsible_party: Optional[str] = None
    estimated_effort: Optional[str] = None  # "small", "medium", "large"
    related_finding: Optional[str] = None
    legal_basis: Optional[str] = None


@dataclass
class RequiredEvidence:
    """Required evidence/document for compliance."""
    evidence_type: str
    description: str
    purpose: str
    urgency: str  # "immediate", "soon", "eventually"
    format_hint: Optional[str] = None  # e.g., "signed PDF", "official stamp"


@dataclass
class ConfidenceAssessment:
    """Confidence assessment with explanation."""
    overall_score: float  # 0.0 to 1.0
    level: str  # "high", "medium", "low"
    indicator: str  # Visual indicator
    factors_supporting: list[str] = field(default_factory=list)
    factors_limiting: list[str] = field(default_factory=list)
    disclaimer: str = ""


@dataclass
class HumanReviewRecommendation:
    """Recommendation for human expert review."""
    is_recommended: bool
    reason: Optional[str] = None
    recommended_expertise: Optional[str] = None  # e.g., "labor_lawyer", "tax_advisor"
    urgency: Optional[str] = None


@dataclass
class StructuredAdvisorResponse:
    """
    Complete structured response from the legal compliance advisor.
    """
    # Core sections
    what_i_understood: list[UnderstoodFact]
    what_is_missing: list[MissingInfoItem]
    legal_basis: list[LegalBasisItem]
    compliance_risks: list[ComplianceRisk]
    recommended_actions: list[RecommendedAction]
    required_evidence: list[RequiredEvidence]
    confidence_assessment: ConfidenceAssessment
    human_review_recommendation: HumanReviewRecommendation

    # Metadata
    response_id: str
    case_id: str
    language: str = "fr"
    tone: AdvisoryTone = AdvisoryTone.PROFESSIONAL
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Raw LLM outputs for transparency/audit
    raw_synthesis: Optional[str] = None

    def to_markdown(self) -> str:
        """Render the response as professional markdown."""
        return render_response_as_markdown(self)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "response_id": self.response_id,
            "case_id": self.case_id,
            "language": self.language,
            "tone": self.tone.value,
            "generated_at": self.generated_at.isoformat(),
            "what_i_understood": [
                {"fact": f.fact, "source": f.source, "confidence": f.confidence}
                for f in self.what_i_understood
            ],
            "what_is_missing": [
                {
                    "item": m.item,
                    "importance": m.importance,
                    "reason": m.reason,
                    "suggested_question": m.suggested_question,
                }
                for m in self.what_is_missing
            ],
            "legal_basis": [
                {
                    "article_reference": basis.article_reference,
                    "law_name": basis.law_name,
                    "summary": basis.summary,
                    "relevance": basis.relevance,
                    "url": basis.url,
                }
                for basis in self.legal_basis
            ],
            "compliance_risks": [
                {
                    "risk_description": r.risk_description,
                    "severity": r.severity,
                    "potential_impact": r.potential_impact,
                    "likelihood": r.likelihood,
                    "legal_consequences": r.legal_consequences,
                    "financial_consequences": r.financial_consequences,
                    "operational_consequences": r.operational_consequences,
                }
                for r in self.compliance_risks
            ],
            "recommended_actions": [
                {
                    "action_description": a.action_description,
                    "priority": a.priority,
                    "deadline": a.deadline,
                    "responsible_party": a.responsible_party,
                    "estimated_effort": a.estimated_effort,
                    "related_finding": a.related_finding,
                    "legal_basis": a.legal_basis,
                }
                for a in self.recommended_actions
            ],
            "required_evidence": [
                {
                    "evidence_type": e.evidence_type,
                    "description": e.description,
                    "purpose": e.purpose,
                    "urgency": e.urgency,
                    "format_hint": e.format_hint,
                }
                for e in self.required_evidence
            ],
            "confidence_assessment": {
                "overall_score": self.confidence_assessment.overall_score,
                "level": self.confidence_assessment.level,
                "indicator": self.confidence_assessment.indicator,
                "factors_supporting": self.confidence_assessment.factors_supporting,
                "factors_limiting": self.confidence_assessment.factors_limiting,
                "disclaimer": self.confidence_assessment.disclaimer,
            },
            "human_review_recommendation": {
                "is_recommended": self.human_review_recommendation.is_recommended,
                "reason": self.human_review_recommendation.reason,
                "recommended_expertise": self.human_review_recommendation.recommended_expertise,
                "urgency": self.human_review_recommendation.urgency,
            },
            "markdown_rendering": self.to_markdown(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Prompt Templates for Style Consistency
# ═══════════════════════════════════════════════════════════════════════════════

ADVISORY_STYLE_INSTRUCTIONS = """
You are Daleel (دليل), an expert Tunisian legal advisor. Follow these style guidelines:

TONE AND MANNER:
- Speak like a warm, professional human advisor — not a search engine
- Always reformulate the user's problem before answering
- Use qualifying language: "il semble que", "selon les informations fournies",
  "il est recommandé de", "cette analyse suggère"
- Never make absolute guarantees about legal outcomes

LEGAL PRECISION:
- Always cite the precise article and the law you rely on
- Distinguish between mandatory obligations and recommended practices
- If you are unsure about an article, say so clearly

RISK COMMUNICATION:
- Be clear about severity levels (critical/high/medium/low)
- Explain potential consequences without being alarmist
- Provide concrete, actionable advice — not just theory

STRUCTURE:
- For simple questions: direct answer + law article + practical advice
- For complex situations: reformulate → legal basis → concrete advice → points of attention
- Bold important warnings or deadlines

DISCLAIMERS:
- You provide legal information, not formal legal opinions
- For serious disputes, always recommend consulting a licensed lawyer in Tunisia
- Never generate contracts or official documents without noting they require professional validation
""".strip()


SYNTHESIS_PROMPT_TEMPLATE = """{style_instructions}

Based on the following case information, compose the section: **{section_title}**

**Case Facts:**
{facts_known}

**Missing Information:**
{facts_missing}

**Document Analysis:**
{document_summary}

**Orchestration Results:**
{orchestration_result}

**Instructions for this section:**
{section_instructions}

**Language:** Write in {language} (ISO code: {language_code})

**Output format:**
{output_format}
"""


SECTION_INSTRUCTIONS = {
    "what_i_understood": """
Summarize what has been understood from the user's situation in 3-5 bullet points.
Each point should reflect a key fact about their business, legal context, or concern.
Indicate the confidence level for each understanding.
""".strip(),

    "what_is_missing": """
List the specific information still needed to provide complete advice.
For each item, explain:
1. Why it's needed
2. How critical it is (critical/important/helpful)
3. A suggested question to ask the user

If no critical information is missing, state that clearly.
""".strip(),

    "legal_basis": """
List the applicable legal provisions with:
- Full article reference (e.g., "Article 6 du Code du Travail tunisien")
- Brief summary of the requirement (1-2 sentences)
- Relevance to this case (direct/analogous/contextual)
- Link to official text if available

Order by relevance (most directly applicable first).
""".strip(),

    "compliance_risks": """
Identify and describe compliance risks with:
- Risk description (clear statement of the non-compliance)
- Severity (critical/high/medium/low)
- Potential impact (legal, financial, operational)
- Likelihood of occurrence
- Legal consequences if not addressed

Include both current violations and potential future risks.
""".strip(),

    "recommended_actions": """
Provide concrete, prioritized actions:
- Action description (specific and actionable)
- Priority level (critical/high/medium/low)
- Suggested deadline or timeframe
- Who should be responsible (HR, Legal, Management, etc.)
- Estimated effort
- Legal basis justifying the action

Order by priority and logical sequence.
""".strip(),

    "required_evidence": """
List documents and evidence needed to:
1. Prove current compliance status
2. Support remediation efforts
3. Demonstrate due diligence

For each item specify:
- Document type
- Purpose
- Urgency (immediate/soon/eventually)
- Preferred format if applicable
""".strip(),

    "confidence_assessment": """
Provide an honest assessment of confidence in this analysis:
- Overall confidence score (0.0-1.0)
- Confidence level (high/medium/low)
- Factors supporting the confidence (good document coverage, clear facts, etc.)
- Factors limiting confidence (missing information, ambiguous legal area, etc.)
- Appropriate disclaimer for the confidence level
""".strip(),

    "human_review_recommendation": """
Recommend whether human expert review is needed:
- Yes/No with clear reasoning
- If yes: what type of expertise (labor lawyer, tax specialist, etc.)
- Urgency level for obtaining this review
- What the human expert should focus on

Be conservative: when in doubt, recommend review.
""".strip(),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Core Composer Functions
# ═══════════════════════════════════════════════════════════════════════════════

async def compose_advisor_response(
    case_id: str,
    facts_known: list[str],
    facts_missing: list[str],
    document_analyses: list[dict],
    orchestration_result: dict,
    legal_context: list[dict],
    language: str = "fr",
    tone: AdvisoryTone = AdvisoryTone.PROFESSIONAL,
    use_llm_refinement: bool = True,
) -> StructuredAdvisorResponse:
    """
    Compose a structured legal compliance advisor response.

    This is the main entry point that transforms raw orchestration data
    into a professional advisory response.
    """
    import uuid

    response_id = f"adv-{uuid.uuid4().hex[:12]}"

    # Build each section from available data
    understood = _build_what_i_understood(
        facts_known, document_analyses, orchestration_result
    )

    missing = _build_what_is_missing(
        facts_missing, orchestration_result
    )

    legal_basis = _build_legal_basis(
        legal_context, orchestration_result
    )

    risks = _build_compliance_risks(
        orchestration_result
    )

    actions = _build_recommended_actions(
        orchestration_result
    )

    evidence = _build_required_evidence(
        orchestration_result, document_analyses
    )

    confidence = _build_confidence_assessment(
        orchestration_result, facts_known, facts_missing, document_analyses
    )

    review_rec = _build_human_review_recommendation(
        orchestration_result, confidence
    )

    response = StructuredAdvisorResponse(
        response_id=response_id,
        case_id=case_id,
        language=language,
        tone=tone,
        what_i_understood=understood,
        what_is_missing=missing,
        legal_basis=legal_basis,
        compliance_risks=risks,
        recommended_actions=actions,
        required_evidence=evidence,
        confidence_assessment=confidence,
        human_review_recommendation=review_rec,
    )

    # Optionally refine with LLM for stylistic consistency
    if use_llm_refinement:
        response = await _refine_with_llm(
            response=response,
            language=language,
            tone=tone,
            extracted_facts={"facts_known": facts_known, "facts_missing": facts_missing},
            legal_context=legal_context,
            orchestration_result=orchestration_result,
        )

    return response


def _build_what_i_understood(
    facts_known: list[str],
    document_analyses: list[dict],
    orchestration_result: dict,
) -> list[UnderstoodFact]:
    """Build the 'what I understood' section."""
    understood: list[UnderstoodFact] = []

    for fact in facts_known:
        understood.append(UnderstoodFact(
            fact=fact,
            source="user_statement",
            confidence=0.9,
        ))

    # Add insights from document analysis
    for doc in document_analyses:
        analysis = doc.get("analysis", {})
        entities = analysis.get("entities", {})

        if "parties" in entities:
            for party in entities["parties"]:
                understood.append(UnderstoodFact(
                    fact=f"Documented party: {party.get('name', 'Unknown')} "
                         f"({party.get('role', 'role not specified')})",
                    source="document",
                    confidence=analysis.get("confidence", 0.7),
                ))

        if "obligations" in entities:
            for obl in entities["obligations"]:
                understood.append(UnderstoodFact(
                    fact=f"Documented obligation: {obl.get('description', '')}",
                    source="document",
                    confidence=analysis.get("confidence", 0.7),
                ))

    # Add inferences from orchestration
    matter_type = orchestration_result.get("matter_type", "")
    if matter_type and matter_type != "unknown":
        understood.append(UnderstoodFact(
            fact=f"Legal matter identified as: {matter_type}",
            source="inferred",
            confidence=0.8,
        ))

    return understood


def _build_what_is_missing(
    facts_missing: list[str],
    orchestration_result: dict,
) -> list[MissingInfoItem]:
    """Build the 'what is missing' section."""
    missing: list[MissingInfoItem] = []

    for item in facts_missing:
        missing.append(MissingInfoItem(
            item=item,
            importance="important",
            reason="Required to assess full compliance scope",
            suggested_question=f"Pouvez-vous préciser : {item}?",
        ))

    # Add clarifications needed from orchestration
    if orchestration_result.get("decision") == "clarify":
        clarification_reason = orchestration_result.get("decision_reason", "")
        missing.append(MissingInfoItem(
            item="Clarification of identified contradictions",
            importance="critical",
            reason=clarification_reason,
            suggested_question="Pourriez-vous clarifier les points mentionnés?",
        ))

    return missing


def _build_legal_basis(
    legal_context: list[dict],
    orchestration_result: dict,
) -> list[LegalBasisItem]:
    """Build the legal basis section."""
    basis: list[LegalBasisItem] = []

    # From retrieved legal context
    for ctx in legal_context:
        basis.append(LegalBasisItem(
            article_reference=ctx.get("article_reference", "Unknown"),
            law_name=ctx.get("law_name"),
            summary=ctx.get("summary", ""),
            relevance=ctx.get("relevance", "direct"),
            url=ctx.get("url"),
        ))

    # From orchestration findings
    for finding in orchestration_result.get("proposed_findings", []):
        refs = finding.get("article_references", [])
        for ref in refs:
            if not any(b.article_reference == ref for b in basis):
                basis.append(LegalBasisItem(
                    article_reference=ref,
                    summary=finding.get("description", "")[:200],
                    relevance="direct",
                ))

    return basis


def _build_compliance_risks(
    orchestration_result: dict,
) -> list[ComplianceRisk]:
    """Build the compliance risks section."""
    risks: list[ComplianceRisk] = []

    for finding in orchestration_result.get("proposed_findings", []):
        severity = finding.get("severity", "observation")
        risk_level = "critical" if severity == "critical" else (
            "high" if severity == "major" else (
                "medium" if severity == "minor" else "low"
            )
        )

        risks.append(ComplianceRisk(
            risk_description=finding.get("title", finding.get("description", "Unknown risk")),
            severity=risk_level,
            potential_impact=_describe_impact(severity),
            likelihood="probable" if severity in ["critical", "major"] else "possible",
            legal_consequences=_describe_legal_consequences(severity) if severity in ["critical", "major"] else None,
        ))

    return risks


def _build_recommended_actions(
    orchestration_result: dict,
) -> list[RecommendedAction]:
    """Build the recommended actions section."""
    actions: list[RecommendedAction] = []

    for action in orchestration_result.get("proposed_actions", []):
        actions.append(RecommendedAction(
            action_description=action.get("title", action.get("description", "")),
            priority=action.get("priority", "medium"),
            deadline=action.get("due_date"),
            responsible_party=action.get("assigned_to", "À déterminer"),
            estimated_effort=action.get("estimated_effort", "medium"),
            related_finding=action.get("finding_idx"),
        ))

    # If no specific actions but findings exist, generate generic actions
    if not actions and orchestration_result.get("proposed_findings"):
        for finding in orchestration_result.get("proposed_findings", []):
            actions.append(RecommendedAction(
                action_description=f"Remediate: {finding.get('title', '')}",
                priority="high" if finding.get("severity") in ["critical", "major"] else "medium",
                related_finding=finding.get("title"),
                legal_basis=finding.get("article_references", [""])[0] if finding.get("article_references") else None,
            ))

    return actions


def _build_required_evidence(
    orchestration_result: dict,
    document_analyses: list[dict],
) -> list[RequiredEvidence]:
    """Build the required evidence section."""
    evidence: list[RequiredEvidence] = []

    # Evidence from orchestration
    for ev in orchestration_result.get("evidences_required", []):
        evidence.append(RequiredEvidence(
            evidence_type=ev.get("type", "document"),
            description=ev.get("description", ""),
            purpose=ev.get("purpose", "Compliance demonstration"),
            urgency=ev.get("urgency", "soon"),
            format_hint=ev.get("format"),
        ))

    # Infer missing evidence from gap analysis
    for finding in orchestration_result.get("proposed_findings", []):
        if finding.get("severity") in ["critical", "major"]:
            evidence.append(RequiredEvidence(
                evidence_type="compliance_proof",
                description=f"Documentation proving remediation of: {finding.get('title', '')}",
                purpose="Demonstrate compliance with legal requirement",
                urgency="immediate" if finding.get("severity") == "critical" else "soon",
            ))

    return evidence


def _build_confidence_assessment(
    orchestration_result: dict,
    facts_known: list[str],
    facts_missing: list[str],
    document_analyses: list[dict],
) -> ConfidenceAssessment:
    """Build the confidence assessment section."""
    base_score = orchestration_result.get("confidence_assessment", {}).get("overall", 0.5)

    factors_supporting: list[str] = []
    factors_limiting: list[str] = []

    # Supporting factors
    if len(facts_known) >= 5:
        factors_supporting.append("Comprehensive fact coverage from conversation")
    elif len(facts_known) >= 3:
        factors_supporting.append("Adequate basic facts established")

    if document_analyses:
        doc_count = len(document_analyses)
        factors_supporting.append(f"{doc_count} document(s) analyzed for evidence")

    if orchestration_result.get("applicable_exigences"):
        factors_supporting.append("Applicable legal requirements identified")

    # Limiting factors
    if facts_missing:
        factors_limiting.append(f"{len(facts_missing)} information gaps identified")

    if not document_analyses:
        factors_limiting.append("No documentary evidence reviewed")

    if base_score < 0.6:
        factors_limiting.append("Low confidence in automated analysis")

    # Determine level and indicator
    if base_score >= 0.85:
        level = "high"
        indicator = ConfidenceIndicator.HIGH
    elif base_score >= 0.60:
        level = "medium"
        indicator = ConfidenceIndicator.MEDIUM
    else:
        level = "low"
        indicator = ConfidenceIndicator.LOW

    # Generate appropriate disclaimer
    disclaimer = _generate_disclaimer(level, len(facts_missing))

    return ConfidenceAssessment(
        overall_score=base_score,
        level=level,
        indicator=indicator.value,
        factors_supporting=factors_supporting,
        factors_limiting=factors_limiting,
        disclaimer=disclaimer,
    )


def _build_human_review_recommendation(
    orchestration_result: dict,
    confidence: ConfidenceAssessment,
) -> HumanReviewRecommendation:
    """Build the human review recommendation."""
    # Determine if review is needed
    is_recommended = False
    reasons: list[str] = []
    expertise: Optional[str] = None
    urgency: Optional[str] = None

    # Critical findings with low confidence
    critical_findings = [
        f for f in orchestration_result.get("proposed_findings", [])
        if f.get("severity") == "critical"
    ]

    if critical_findings and confidence.level == "low":
        is_recommended = True
        reasons.append("Critical findings identified with low analysis confidence")
        expertise = "avocat_droit_travail"
        urgency = "urgent"

    # High severity findings
    elif any(f.get("severity") in ["critical", "major"] for f in orchestration_result.get("proposed_findings", [])):
        is_recommended = True
        reasons.append("Significant compliance violations detected")
        expertise = "conseiller_conformite"
        urgency = "high"

    # Low confidence overall
    elif confidence.level == "low":
        is_recommended = True
        reasons.append("Insufficient information for reliable automated analysis")
        expertise = "expert_juridique"
        urgency = "medium"

    # Decision is to review
    elif orchestration_result.get("decision") == "review":
        is_recommended = True
        reasons.append(orchestration_result.get("human_review_reason", "System recommendation"))
        expertise = "expert_juridique"
        urgency = "high"

    return HumanReviewRecommendation(
        is_recommended=is_recommended,
        reason="; ".join(reasons) if reasons else None,
        recommended_expertise=expertise,
        urgency=urgency,
    )


async def _refine_with_llm(
    response: StructuredAdvisorResponse,
    language: str,
    tone: AdvisoryTone,
    extracted_facts: dict[str, Any],
    legal_context: list[dict],
    orchestration_result: dict,
) -> StructuredAdvisorResponse:
    """
    Refine the markdown rendering using LLM for stylistic consistency.

    Sends the current markdown to the LLM with style instructions so the
    final advisory text feels written by a human compliance advisor rather
    than an automated system.  Only the ``raw_synthesis`` field is updated;
    the structured data sections are **not** mutated.
    """
    draft_md = response.to_markdown()

    # Use the fine-tuned style model if enabled
    if llm_style_formatter.is_enabled():
        try:
            payload = llm_style_formatter.build_payload_from_orchestration(
                user_question="",
                language=language,
                extracted_facts=extracted_facts,
                legal_context=legal_context,
                findings=orchestration_result.get("findings", []),
                actions=orchestration_result.get("remediation_plan", {}).get("actions", []),
                draft_answer=draft_md,
            )
            refined = await llm_style_formatter.format_advisor_answer(
                draft_markdown=draft_md,
                payload=payload,
                language=language,
            )
            response.raw_synthesis = refined.strip()
            return response
        except Exception as exc:
            logger.warning("Style formatter failed (non-fatal): %s", exc)
            # Fall through to general LLM / original draft

    lang_map = {"fr": "French", "ar": "Arabic", "en": "English"}
    tone_labels = {
        AdvisoryTone.FORMAL: "formal and institutional",
        AdvisoryTone.PROFESSIONAL: "professional and client-friendly",
        AdvisoryTone.CAUTIOUS: "cautious and conservative",
        AdvisoryTone.EDUCATIONAL: "educational and explanatory",
    }

    prompt = (
        f"{ADVISORY_STYLE_INSTRUCTIONS}\n\n"
        f"Please refine the following compliance advisory text.\n"
        f"Language: {lang_map.get(language, 'French')}\n"
        f"Tone: {tone_labels.get(tone, 'professional')}\n\n"
        f"--- BEGIN ADVISORY TEXT ---\n"
        f"{draft_md}\n"
        f"--- END ADVISORY TEXT ---\n\n"
        f"Return ONLY the refined markdown text, preserving all section headings "
        f"and factual content.  Do not add or remove sections."
    )

    try:
        refined = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": ADVISORY_STYLE_INSTRUCTIONS},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            base_url=settings.llm_base_url,
        )
        response.raw_synthesis = refined.strip()
    except Exception as exc:
        logger.warning("LLM refinement failed (non-fatal): %s", exc)
        # Fallback: keep original markdown, no crash
        response.raw_synthesis = draft_md

    return response


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _describe_impact(severity: str) -> str:
    """Generate impact description based on severity."""
    impacts = {
        "critical": "Significant legal, financial, and reputational damage",
        "major": "Substantial compliance breach with potential penalties",
        "minor": "Procedural or documentation gap",
        "observation": "Area for improvement, minimal immediate risk",
    }
    return impacts.get(severity, "Impact to be assessed")


def _describe_legal_consequences(severity: str) -> str:
    """Generate legal consequence description."""
    consequences = {
        "critical": "Potential criminal liability, significant fines, operational sanctions",
        "major": "Administrative penalties, fines, mandatory corrective actions",
    }
    return consequences.get(severity, "Legal consequences to be determined")


def _generate_disclaimer(confidence_level: str, missing_count: int) -> str:
    """Generate appropriate disclaimer based on confidence."""
    base = (
        "Cette analyse est fournie à titre indicatif et ne constitue pas un avis juridique définitif. "
        "Elle est basée sur les informations disponibles à ce jour."
    )

    if confidence_level == "low":
        base += (
            " **Attention** : Le niveau de confiance de cette analyse est faible en raison "
            f"d'informations manquantes ({missing_count} éléments). "
            "Une expertise humaine est fortement recommandée avant toute décision."
        )
    elif confidence_level == "medium":
        base += (
            " Cette analyse présente un niveau de confiance modéré. "
            "Il est recommandé de valider les conclusions importantes avec un conseiller juridique."
        )
    else:
        base += (
            " Cette analyse présente un niveau de confiance élevé, "
            "mais une validation par un professionnel reste prudent pour les décisions critiques."
        )

    return base


def _get_section_title(section: str, language: str) -> str:
    """Get localized section title."""
    if language == "ar":
        return SECTION_TITLES_AR.get(section, section)
    elif language == "fr":
        return SECTION_TITLES_FR.get(section, section)
    return SECTION_TITLES_EN.get(section, section)


# ═══════════════════════════════════════════════════════════════════════════════
# Markdown Rendering
# ═══════════════════════════════════════════════════════════════════════════════

def render_response_as_markdown(response: StructuredAdvisorResponse) -> str:
    """
    Render a StructuredAdvisorResponse as professional markdown.
    """
    lang = response.language
    sections: list[str] = []

    # Header
    sections.append(f"# {_get_section_title('what_i_understood', lang).split(' — ')[0]}")
    sections.append(f"\n**Référence**: `{response.response_id}` | **Généré**: {response.generated_at.strftime('%Y-%m-%d %H:%M')}")
    sections.append("---\n")

    # Section 1: What I understood
    sections.append(f"## {_get_section_title('what_i_understood', lang)}")
    for fact in response.what_i_understood:
        confidence_indicator = "✓" if fact.confidence >= 0.8 else "~" if fact.confidence >= 0.5 else "?"
        source_note = f" [source: {fact.source}]" if fact.source != "user_statement" else ""
        sections.append(f"- {confidence_indicator} **{fact.fact}**{source_note}")
    sections.append("")

    # Section 2: What is missing
    if response.what_is_missing:
        sections.append(f"## {_get_section_title('what_is_missing', lang)}")
        for item in response.what_is_missing:
            importance_icon = "🔴" if item.importance == "critical" else "🟡" if item.importance == "important" else "⚪"
            sections.append(f"- {importance_icon} **{item.item}** — {item.reason}")
            if item.suggested_question:
                sections.append(f"  *💡 Question suggérée: {item.suggested_question}*")
        sections.append("")

    # Section 3: Legal basis
    if response.legal_basis:
        sections.append(f"## {_get_section_title('legal_basis', lang)}")
        for basis in response.legal_basis:
            law = f" ({basis.law_name})" if basis.law_name else ""
            relevance = f" [{basis.relevance}]" if basis.relevance != "direct" else ""
            sections.append(f"- **{basis.article_reference}**{law}{relevance}")
            if basis.summary:
                sections.append(f"  > {basis.summary}")
            if basis.url:
                sections.append(f"  [Voir le texte officiel]({basis.url})")
        sections.append("")

    # Section 4: Compliance risks
    if response.compliance_risks:
        sections.append(f"## {_get_section_title('compliance_risks', lang)}")
        for risk in response.compliance_risks:
            risk_icon = RiskIndicator.CRITICAL.value if risk.severity == "critical" else (
                RiskIndicator.HIGH.value if risk.severity == "high" else (
                    RiskIndicator.MEDIUM.value if risk.severity == "medium" else RiskIndicator.LOW.value
                )
            )
            sections.append(f"### {risk_icon} {risk.risk_description}")
            sections.append(f"- **Gravité**: {risk.severity.upper()}")
            sections.append(f"- **Probabilité**: {risk.likelihood}")
            sections.append(f"- **Impact potentiel**: {risk.potential_impact}")
            if risk.legal_consequences:
                sections.append(f"- **Conséquences juridiques**: {risk.legal_consequences}")
            if risk.financial_consequences:
                sections.append(f"- **Conséquences financières**: {risk.financial_consequences}")
            sections.append("")

    # Section 5: Recommended actions
    if response.recommended_actions:
        sections.append(f"## {_get_section_title('recommended_actions', lang)}")
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_actions = sorted(
            response.recommended_actions,
            key=lambda a: priority_order.get(a.priority, 99)
        )
        for i, action in enumerate(sorted_actions, 1):
            priority_icon = "🔴" if action.priority == "critical" else "🟠" if action.priority == "high" else "🟡"
            sections.append(f"{i}. {priority_icon} **{action.action_description}**")
            details = []
            if action.deadline:
                details.append(f"Échéance: *{action.deadline}*")
            if action.responsible_party:
                details.append(f"Responsable: *{action.responsible_party}*")
            if action.estimated_effort:
                details.append(f"Effort estimé: *{action.estimated_effort}*")
            if action.legal_basis:
                details.append(f"Base légale: *{action.legal_basis}*")
            if details:
                sections.append(f"   — {' | '.join(details)}")
        sections.append("")

    # Section 6: Required evidence
    if response.required_evidence:
        sections.append(f"## {_get_section_title('required_evidence', lang)}")
        for ev in response.required_evidence:
            urgency_icon = "🚨" if ev.urgency == "immediate" else "⏰" if ev.urgency == "soon" else "📋"
            sections.append(f"- {urgency_icon} **{ev.evidence_type}**: {ev.description}")
            sections.append(f"  *Objectif: {ev.purpose}*")
            if ev.format_hint:
                sections.append(f"  *Format: {ev.format_hint}*")
        sections.append("")

    # Section 7: Confidence assessment
    sections.append(f"## {_get_section_title('confidence_assessment', lang)}")
    ca = response.confidence_assessment
    sections.append(f"**Niveau global**: {ca.indicator} {ca.level.upper()} ({ca.overall_score:.0%})")
    sections.append("")
    if ca.factors_supporting:
        sections.append("**Facteurs renforçant la confiance**:")
        for factor in ca.factors_supporting:
            sections.append(f"- ✓ {factor}")
    if ca.factors_limiting:
        sections.append("**Facteurs limitant la confiance**:")
        for factor in ca.factors_limiting:
            sections.append(f"- ⚠ {factor}")
    sections.append("")
    sections.append(f"> **Avis de non-responsabilité**: {ca.disclaimer}")
    sections.append("")

    # Section 8: Human review recommendation
    hrr = response.human_review_recommendation
    if hrr.is_recommended:
        sections.append(f"## {_get_section_title('human_review_recommendation', lang)}")
        urgency_icon = "🚨" if hrr.urgency == "urgent" else "⚠️" if hrr.urgency == "high" else "📌"
        sections.append(f"{urgency_icon} **Expertise humaine recommandée**")
        if hrr.reason:
            sections.append(f"*Motif: {hrr.reason}*")
        if hrr.recommended_expertise:
            sections.append(f"*Type d'expertise: {hrr.recommended_expertise}*")
        if hrr.urgency:
            sections.append(f"*Priorité: {hrr.urgency}*")
        sections.append("")

    # Footer
    sections.append("---")
    sections.append("*Cette analyse a été générée par Daleel, assistant de conformité juridique.*")
    sections.append("*Pour toute question, consultez un professionnel du droit qualifié.*")

    return "\n".join(sections)


# ═══════════════════════════════════════════════════════════════════════════════
# Integration with Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

async def compose_from_orchestration_result(
    case_id: str,
    orchestration_result: dict,
    conversation_context: dict,
    document_analyses: list[dict],
    legal_context: list[dict],
    language: str = "fr",
) -> StructuredAdvisorResponse:
    """
    Convenience function to compose a response directly from orchestrator output.
    """
    return await compose_advisor_response(
        case_id=case_id,
        facts_known=conversation_context.get("facts_known", []),
        facts_missing=conversation_context.get("facts_missing", []),
        document_analyses=document_analyses,
        orchestration_result=orchestration_result,
        legal_context=legal_context,
        language=language,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Export for API Integration
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Main classes
    "StructuredAdvisorResponse",
    "UnderstoodFact",
    "MissingInfoItem",
    "LegalBasisItem",
    "ComplianceRisk",
    "RecommendedAction",
    "RequiredEvidence",
    "ConfidenceAssessment",
    "HumanReviewRecommendation",
    "AdvisoryTone",
    "ConfidenceIndicator",
    "RiskIndicator",
    # Functions
    "compose_advisor_response",
    "compose_from_orchestration_result",
    "render_response_as_markdown",
    # Templates
    "ADVISORY_STYLE_INSTRUCTIONS",
    "SYNTHESIS_PROMPT_TEMPLATE",
    "SECTION_INSTRUCTIONS",
]
