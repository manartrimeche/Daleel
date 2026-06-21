"""
Voice assistant API router — handles audio transcription, TTS, and full voice Q&A.
"""

import logging
from typing import Any

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends
from fastapi.responses import Response

from app.services.voice_service import transcribe_audio, synthesize_speech
from app.services import llm_service
from app.api.auth import get_current_user
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

SUPPORTED_VOICE_LANGUAGES = {"fr", "en", "ar"}


def _organization_scope(user: dict | None) -> str | None:
    """Return the organization_id for tenant scoping (None for super_admin)."""
    if not user or user.get("role") == "super_admin":
        return None
    return user.get("organization_id")


@router.post("/transcribe")
async def voice_transcribe(
    audio: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """Transcribe uploaded audio to text using faster-whisper."""
    audio_bytes = await audio.read()

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file too large (max 25MB)")

    result = await transcribe_audio(audio_bytes)
    return result


@router.post("/tts")
async def voice_tts(
    text: str = Query(..., min_length=1, max_length=5000),
    language: str = Query(default="fr", pattern="^(fr|en|ar)$"),
    user=Depends(get_current_user),
):
    """Convert text to speech audio."""
    try:
        audio_bytes = await synthesize_speech(text, language)
    except Exception:
        logger.exception("TTS failed")
        raise HTTPException(status_code=503, detail="Voice synthesis unavailable")
    content_type = "audio/mpeg"

    return Response(
        content=audio_bytes,
        media_type=content_type,
        headers={"Content-Disposition": "inline; filename=response.audio"},
    )


@router.post("/ask")
async def voice_ask(
    audio: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Any = Depends(get_db),
):
    """Full voice pipeline: transcribe → ask agent → TTS response JSON."""
    audio_bytes = await audio.read()

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # 1. Transcribe — langue détectée automatiquement depuis l'audio
    try:
        transcription = await transcribe_audio(audio_bytes)
    except Exception:
        logger.exception("Audio transcription failed")
        raise HTTPException(status_code=503, detail="Voice transcription unavailable")
    user_text = transcription["text"]
    detected_lang = transcription["language"]

    if not user_text.strip():
        raise HTTPException(status_code=400, detail="No speech detected")

    if detected_lang not in SUPPORTED_VOICE_LANGUAGES:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Voice language unsupported or unclear",
                "language": detected_lang,
                "language_probability": transcription.get("language_probability"),
            },
        )

    if not transcription.get("is_confident", True):
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Speech was too unclear to answer reliably",
                "reasons": transcription.get("confidence_reasons", []),
                "language": detected_lang,
                "language_probability": transcription.get("language_probability"),
            },
        )

    # 2. Ask the agentic LLM (pass detected language + org scope so the answer matches)
    result = await llm_service.ask_agentic(
        db,
        question=user_text,
        response_language=detected_lang,
        organization_id=_organization_scope(user),
        use_quality_guard=True,
    )
    answer_text = result.get("answer", "")

    # 3. Synthesize response audio
    import base64

    audio_b64 = None
    content_type = None
    try:
        audio_response = await synthesize_speech(answer_text, detected_lang)
        content_type = "audio/mpeg"
        audio_b64 = base64.b64encode(audio_response).decode()
    except Exception:
        logger.exception("TTS failed; returning text-only voice answer")

    return {
        "transcription": user_text,
        "language": detected_lang,
        "transcription_confidence": {
            "is_confident": transcription.get("is_confident", True),
            "language_probability": transcription.get("language_probability"),
            "avg_logprob": transcription.get("avg_logprob"),
            "no_speech_probability": transcription.get("no_speech_probability"),
            "compression_ratio": transcription.get("compression_ratio"),
        },
        "answer": answer_text,
        "audio_base64": audio_b64,
        "audio_content_type": content_type,
        "sources": result.get("sources", []),
    }
