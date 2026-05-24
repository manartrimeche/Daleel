"""
FastAPI routes for the Case Conversation Workflow.

Prefix: /api/v1/cases  (mounted alongside the existing case_router)

Endpoints:
  POST /cases/from-conversation               — create a case from a user situation
  POST /cases/{id}/converse                    — send a follow-up message (conversational)
  GET  /cases/{id}/summary                     — structured case conversation summary
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.auth import get_optional_current_user, require_api_key_or_roles
from app.case_schemas import (
    CaseConversationSummaryOut,
    ConversationMessageIn,
    ConversationStartIn,
    ConversationTurnOut,
)
from app.database import get_db
from app.limiter import limiter
from app.services import case_conversation_service

logger = logging.getLogger(__name__)

require_case_user = require_api_key_or_roles("super_admin", "owner", "admin", "member")
router = APIRouter(prefix="/cases", tags=["case-conversation"])


def _organization_scope(user: dict | None) -> str | None:
    if not user or user.get("role") == "super_admin":
        return None
    return user.get("organization_id")


# ═══════════════════════════════════════════════════════════════════════════════
# Create case from initial conversation
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/from-conversation",
    response_model=ConversationTurnOut,
    status_code=201,
    summary="Create a compliance case from a user-described situation",
)
@limiter.limit("6/minute")
async def create_case_from_conversation(
    request: Request,
    body: ConversationStartIn,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """
    Analyse the user's situation description, extract structured facts,
    create a compliance case, and return the first clarification question.
    """
    try:
        result = await case_conversation_service.create_case_from_conversation(
            db,
            situation=body.situation,
            company_profile_id=body.company_profile_id,
            created_by=body.created_by,
            organization_id=_organization_scope(current_user),
        )
        return result
    except ValueError as e:
        raise HTTPException(422, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Conversational message exchange
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/{case_id}/converse",
    response_model=ConversationTurnOut,
    status_code=201,
    summary="Send a follow-up message in the case conversation",
)
@limiter.limit("10/minute")
async def send_conversation_message(
    request: Request,
    case_id: str,
    body: ConversationMessageIn,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """
    Process a user follow-up message: extract new facts, update the case
    context, and return the assistant's next clarification or analysis.
    """
    try:
        result = await case_conversation_service.process_user_message(
            db,
            case_id,
            content=body.content,
            organization_id=_organization_scope(current_user),
        )
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Case conversation summary
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{case_id}/summary",
    response_model=CaseConversationSummaryOut,
    summary="Get the structured conversational summary of a case",
)
@limiter.limit("15/minute")
async def get_case_conversation_summary(
    request: Request,
    case_id: str,
    db: Any = Depends(get_db),
    _key: str | None = Depends(require_case_user),
    current_user: dict | None = Depends(get_optional_current_user),
):
    """
    Return the case's current conversational context: known facts,
    missing facts, matter type, urgency, and next question.
    """
    result = await case_conversation_service.get_case_conversation_summary(
        db,
        case_id,
        organization_id=_organization_scope(current_user),
    )
    if result is None:
        raise HTTPException(404, "Case not found")
    return result
