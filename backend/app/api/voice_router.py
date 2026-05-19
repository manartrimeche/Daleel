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
    except Exception as exc:
        logger.exception("TTS failed")
        raise HTTPException(status_code=503, detail=f"Voice synthesis unavailable: {exc}")
    content_type = "audio/mpeg" if language == "ar" else "audio/wav"

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
    except Exception as exc:
        logger.exception("Audio transcription failed")
        raise HTTPException(status_code=503, detail=f"Voice transcription unavailable: {exc}")
    user_text = transcription["text"]
    detected_lang = transcription["language"]

    if not user_text.strip():
        raise HTTPException(status_code=400, detail="No speech detected")

    # 2. Ask the agentic LLM
    result = await llm_service.ask_agentic(db, question=user_text)
    answer_text = result.get("answer", "")

    # 3. Synthesize response audio
    import base64

    audio_b64 = None
    content_type = None
    try:
        audio_response = await synthesize_speech(answer_text, detected_lang)
        content_type = "audio/mpeg" if detected_lang == "ar" else "audio/wav"
        audio_b64 = base64.b64encode(audio_response).decode()
    except Exception:
        logger.exception("TTS failed; returning text-only voice answer")

    return {
        "transcription": user_text,
        "language": detected_lang,
        "answer": answer_text,
        "audio_base64": audio_b64,
        "audio_content_type": content_type,
        "sources": result.get("sources", []),
    }
