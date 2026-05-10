"""
FastAPI routes for the Compliance Case Orchestrator.

Prefix: /api/v1/cases/{case_id}/orchestrate

Endpoints:
  POST /cases/{id}/orchestrate           — Run orchestration analysis
  GET  /cases/{id}/orchestrate/status    — Check orchestration readiness
  GET  /cases/{id}/orchestrate/assess    — Quick assessment
  GET  /cases/{id}/orchestrate/questions — Suggested next questions
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import require_api_key
from app.case_schemas import (
    AdvisorResponseCreate,
    AdvisorResponseOut,
    NextQuestionsOut,
    OrchestrationIn,
    OrchestrationOut,
    OrchestrationStatusOut,
    QuickAssessmentOut,
)
from app.database import get_db
from app.services import compliance_case_orchestrator
from app.services import advisor_response_composer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["case-orchestration"])


def _orchestration_result_to_output(case_id: str, result) -> OrchestrationOut:
    """Convert internal OrchestrationResult to API output."""
    from app.case_schemas import (
        ConfidenceAssessment,
        ProposedFinding,
        ProposedAction,
        ProposedControl,
        RequiredEvidence,
    )

    return OrchestrationOut(
        case_id=case_id,
        decision=result.decision.value,
        decision_reason=result.decision_reason,
        proposed_findings=[
            ProposedFinding(
                title=f.get("title", ""),
                description=f.get("description", ""),
                severity=f.get("severity", "observation"),
                confidence=f.get("confidence", 0.0),
                exigence_id=f.get("exigence_id"),
            )
            for f in getattr(result, 'proposed_findings', []) or []
        ],
        findings_created=result.findings_created or [],
        proposed_actions=[
            ProposedAction(
                title=a.get("title", ""),
                description=a.get("description", ""),
                priority=a.get("priority", "medium"),
                due_date=a.get("due_date"),
                finding_title=a.get("finding_title"),
            )
            for a in getattr(result, 'proposed_actions', []) or []
        ],
        actions_created=result.actions_created or [],
        controls_proposed=[
            ProposedControl(
                control_type=c.get("control_type", "preventive"),
                title=c.get("title", ""),
                description=c.get("description", ""),
                frequency=c.get("frequency", "monthly"),
                automation=c.get("automation", "manual"),
                owner_role=c.get("owner_role", ""),
                evidence_type=c.get("evidence_type", ""),
            )
            for c in result.controls_proposed or []
        ],
        evidences_required=[
            RequiredEvidence(
                evidence_type=e.get("evidence_type", "document"),
                description=e.get("description", ""),
                source_document_id=e.get("source_document_id"),
                source_document_role=e.get("source_document_role"),
                status=e.get("status", "missing"),
                acquisition_steps=e.get("acquisition_steps", []),
            )
            for e in result.evidences_required or []
        ],
        clarification_question=result.clarification_question,
        human_review_reason=result.human_review_reason,
        confidence_assessment=ConfidenceAssessment(
            overall=result.confidence_assessment.get("overall", 0.0),
            level=result.confidence_assessment.get("level", "low"),
            evidence_sufficiency=result.confidence_assessment.get("evidence_sufficiency", "insufficient"),
        ),
        risk_level=result.risk_level,
        next_steps=result.next_steps or [],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Orchestration Analysis
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/{case_id}/orchestrate",
    response_model=OrchestrationOut,
    summary="Run compliance case orchestration analysis",
)
async def run_orchestration(
    case_id: str,
    body: OrchestrationIn,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """
    Analyze a compliance case and determine findings, actions, and next steps.

    The orchestrator:
    1. Reads case facts and conversation context
    2. Analyzes attached documents
    3. Determines applicable legal requirements
    4. Identifies compliance gaps and violations
    5. Proposes findings, controls, and remediation actions
    6. Maps required evidences
    7. Recommends next steps (ask/clarify/act/review)

    **Auto-create options:**
    - `auto_create_findings=true` — Persist findings to database
    - `auto_create_actions=true` — Persist actions to database (only if findings created)

    **Decision outcomes:**
    - `ask` — Need more information from user (clarification_question provided)
    - `clarify` — Document contradictions need resolution
    - `act` — Analysis complete, findings/actions proposed or created
    - `review` — Low confidence or critical findings need human review
    """
    try:
        result = await compliance_case_orchestrator.analyze_and_orchestrate(
            db,
            case_id,
            auto_create_findings=body.auto_create_findings,
            auto_create_actions=body.auto_create_actions,
            actor=_key or "api",
        )
        return _orchestration_result_to_output(case_id, result)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error("Orchestration failed for case %s: %s", case_id, e)
        raise HTTPException(500, "Internal error during orchestration analysis")


# ═══════════════════════════════════════════════════════════════════════════════
# Orchestration Status & Utilities
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{case_id}/orchestrate/status",
    response_model=OrchestrationStatusOut,
    summary="Get orchestration readiness status",
)
async def get_orchestration_status(
    case_id: str,
    db: Any = Depends(get_db),
):
    """
    Check whether a case is ready for orchestration.

    Returns:
    - `ready_for_orchestration` — Boolean indicating if case has enough context
    - `orchestration_recommendation` — "ready" or "needs_more_info"
    - Fact counts, document counts, existing findings/actions
    """
    status = await compliance_case_orchestrator.get_orchestration_status(db, case_id)
    if "error" in status:
        raise HTTPException(404, status["error"])

    return OrchestrationStatusOut(
        case_id=status["case_id"],
        status=status["status"],
        ready_for_orchestration=status["ready_for_orchestration"],
        facts_known_count=status["facts_known_count"],
        facts_missing_count=status["facts_missing_count"],
        findings_count=status["findings_count"],
        actions_count=status["actions_count"],
        orchestration_recommendation=status["orchestration_recommendation"],
    )


@router.get(
    "/{case_id}/orchestrate/assess",
    response_model=QuickAssessmentOut,
    summary="Quick assessment of case readiness",
)
async def quick_assess(
    case_id: str,
    db: Any = Depends(get_db),
):
    """
    Get a quick heuristic assessment of case readiness for analysis.

    Returns a readiness score (0.0-1.0) based on:
    - Number of known facts
    - Document support
    - Estimated analysis quality

    This is a lightweight endpoint for UI readiness indicators.
    """
    try:
        assessment = await compliance_case_orchestrator.quick_assess(db, case_id)
        return QuickAssessmentOut(
            case_id=assessment["case_id"],
            readiness_score=assessment["readiness_score"],
            readiness_level=assessment["readiness_level"],
            factors=assessment["factors"],
            suggestions=assessment["suggestions"],
            estimated_analysis_quality=assessment["estimated_analysis_quality"],
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get(
    "/{case_id}/orchestrate/questions",
    response_model=NextQuestionsOut,
    summary="Get suggested next clarification questions",
)
async def suggest_questions(
    case_id: str,
    count: int = 3,
    db: Any = Depends(get_db),
):
    """
    Get suggested clarification questions for the case.

    These questions target missing facts that would most improve
    the compliance analysis.

    Args:
        count: Number of questions to suggest (default 3, max 5)
    """
    if count < 1:
        count = 1
    if count > 5:
        count = 5

    try:
        questions = await compliance_case_orchestrator.suggest_next_questions(
            db, case_id, count=count
        )
        return NextQuestionsOut(
            case_id=case_id,
            questions=questions,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Advisor Response Composer
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/{case_id}/orchestrate/advise",
    response_model=AdvisorResponseOut,
    summary="Compose a structured legal advisor response",
)
async def compose_advisor_response(
    case_id: str,
    body: AdvisorResponseCreate,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_api_key),
):
    """
    Compose a structured, professional legal compliance advisory response.

    Takes orchestration results (from POST ``/orchestrate``) and formats them
    into 8 advisor sections:

    1. **What I understood** — facts acknowledged
    2. **What is still missing** — information gaps
    3. **Legal basis** — applicable articles / codes
    4. **Compliance risks** — identified risks with severity
    5. **Recommended actions** — prioritised remediation plan
    6. **Required evidence** — documents and proofs needed
    7. **Confidence level** — analysis reliability assessment
    8. **Human review recommendation** — whether an expert should review

    Returns both structured data and a ready-to-display **markdown rendering**.
    """
    try:
        tone = advisor_response_composer.AdvisoryTone(body.tone)
    except ValueError:
        tone = advisor_response_composer.AdvisoryTone.PROFESSIONAL

    try:
        response = await advisor_response_composer.compose_advisor_response(
            case_id=case_id,
            facts_known=body.conversation_context.get("facts_known", []),
            facts_missing=body.conversation_context.get("facts_missing", []),
            document_analyses=body.document_analyses,
            orchestration_result=body.orchestration_result,
            legal_context=body.legal_context,
            language=body.language,
            tone=tone,
            use_llm_refinement=body.use_llm_refinement,
        )

        out = response.to_dict()
        out["case_id"] = case_id
        return AdvisorResponseOut(**out)

    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error("Advisor response composition failed for case %s: %s", case_id, e)
        raise HTTPException(500, "Internal error during advisor response composition")
