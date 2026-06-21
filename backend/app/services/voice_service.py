"""
Voice assistant service — STT (faster-whisper) + TTS (Piper / Edge-TTS).
"""

import asyncio
import io
import logging
import os
import re
import shutil
import sys
import tempfile
import threading
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class Language(str, Enum):
    FR = "fr"
    EN = "en"
    AR = "ar"


# ─── STT: faster-whisper ───────────────────────────────────────────────────────

_whisper_model = None
_whisper_lock = threading.Lock()

MIN_TRANSCRIPTION_LANGUAGE_PROBABILITY = 0.35
MIN_TRANSCRIPTION_AVG_LOGPROB = -1.25
MAX_TRANSCRIPTION_NO_SPEECH_PROBABILITY = 0.75
MAX_TRANSCRIPTION_COMPRESSION_RATIO = 2.4


def _segment_value(segment, name: str):
    if isinstance(segment, dict):
        return segment.get(name)
    return getattr(segment, name, None)


def assess_transcription_confidence(
    text: str,
    language_probability: float | None,
    segments: list[dict],
) -> dict:
    """Return a conservative confidence assessment for Whisper output."""
    clean_text = (text or "").strip()
    reasons: list[str] = []

    avg_logprobs = [
        float(v)
        for segment in segments
        if (v := _segment_value(segment, "avg_logprob")) is not None
    ]
    no_speech_probs = [
        float(v)
        for segment in segments
        if (v := _segment_value(segment, "no_speech_prob")) is not None
    ]
    compression_ratios = [
        float(v)
        for segment in segments
        if (v := _segment_value(segment, "compression_ratio")) is not None
    ]

    avg_logprob = sum(avg_logprobs) / len(avg_logprobs) if avg_logprobs else None
    no_speech_probability = (
        sum(no_speech_probs) / len(no_speech_probs) if no_speech_probs else None
    )
    compression_ratio = max(compression_ratios) if compression_ratios else None

    if not clean_text:
        reasons.append("no_text")
    if language_probability is not None and language_probability < MIN_TRANSCRIPTION_LANGUAGE_PROBABILITY:
        reasons.append("low_language_probability")
    if avg_logprob is not None and avg_logprob < MIN_TRANSCRIPTION_AVG_LOGPROB:
        reasons.append("low_log_probability")
    if (
        no_speech_probability is not None
        and no_speech_probability > MAX_TRANSCRIPTION_NO_SPEECH_PROBABILITY
    ):
        reasons.append("likely_silence")
    if (
        compression_ratio is not None
        and compression_ratio > MAX_TRANSCRIPTION_COMPRESSION_RATIO
    ):
        reasons.append("repetitive_or_unstable_audio")

    return {
        "is_confident": not reasons,
        "confidence_reasons": reasons,
        "avg_logprob": avg_logprob,
        "no_speech_probability": no_speech_probability,
        "compression_ratio": compression_ratio,
    }


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    with _whisper_lock:
        if _whisper_model is not None:
            return _whisper_model
        from faster_whisper import WhisperModel
        device = "cpu"
        compute = "int8"
        try:
            import torch
            if torch.cuda.is_available():
                import ctypes
                ctypes.CDLL("cublas64_12.dll")
                device = "cuda"
                compute = "float16"
        except (ImportError, OSError):
            pass
        model_name = os.getenv("DALEEL_WHISPER_MODEL", "small")
        _whisper_model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute,
        )
        logger.info("faster-whisper model loaded (%s, %s/%s)", model_name, device, compute)
    return _whisper_model


async def transcribe_audio(audio_bytes: bytes) -> dict:
    """Transcribe audio bytes to text. Returns {text, language, segments}."""
    loop = asyncio.get_event_loop()

    def _transcribe():
        model = _get_whisper_model()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            segments, info = model.transcribe(
                tmp_path,
                beam_size=5,
                language=None,  # auto-detect from audio
                vad_filter=True,
                condition_on_previous_text=False,
            )
            text_parts = []
            segment_metrics = []
            for segment in segments:
                text_parts.append(segment.text.strip())
                segment_metrics.append(
                    {
                        "avg_logprob": getattr(segment, "avg_logprob", None),
                        "no_speech_prob": getattr(segment, "no_speech_prob", None),
                        "compression_ratio": getattr(segment, "compression_ratio", None),
                    }
                )

            text = " ".join(text_parts).strip()
            language_probability = getattr(info, "language_probability", None)
            confidence = assess_transcription_confidence(
                text,
                language_probability,
                segment_metrics,
            )

            return {
                "text": text,
                "language": info.language,
                "language_probability": language_probability,
                **confidence,
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    return await loop.run_in_executor(None, _transcribe)


# ─── TTS: Piper (FR/EN) + Edge-TTS (AR tunisien) ──────────────────────────────

EDGE_TTS_VOICES = {
    "ar": "ar-TN-ReemNeural",
    "fr": "fr-FR-DeniseNeural",
    "en": "en-US-JennyNeural",
}

PIPER_VOICES_DIR = Path(os.getenv("PIPER_VOICES_DIR", str(Path.home())))
ONLINE_TTS_ENABLED = os.getenv("DALEEL_TTS_ONLINE_ENABLED", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

PIPER_VOICES = {
    "fr": str(PIPER_VOICES_DIR / "fr_FR-siwis-medium.onnx"),
    "en": str(PIPER_VOICES_DIR / "en_US-lessac-medium.onnx"),
}


def _resolve_piper_executable() -> str:
    """Find Piper even when the virtual environment was not shell-activated."""
    candidates = [
        shutil.which("piper"),
        str(Path(sys.executable).with_name("piper.exe")),
        str(Path(sys.executable).with_name("piper")),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return "piper"


def _clean_for_tts(text: str) -> str:
    """Strip markdown, emojis and formatting so TTS reads only plain text."""
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    text = re.sub(r'~~([^~]+)~~', r'\1', text)
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[>|]', '', text)
    text = re.sub(
        r'[\U0001F600-\U0001F64F'
        r'\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF'
        r'\U0001F1E0-\U0001F1FF'
        r'\U00002700-\U000027BF'
        r'\U0001F900-\U0001F9FF'
        r'\U0001FA00-\U0001FA6F'
        r'\U0001FA70-\U0001FAFF'
        r'\U00002600-\U000026FF'
        r'\U0000FE00-\U0000FE0F'
        r'\U0000200D]+', '', text)
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


async def synthesize_speech(text: str, language: str = "fr") -> bytes:
    """Convert text to speech audio (WAV/MP3 bytes). Uses Edge-TTS with Piper fallback."""
    text = _clean_for_tts(text)
    lang = language[:2].lower()
    edge_voice = EDGE_TTS_VOICES.get(lang, EDGE_TTS_VOICES["fr"])

    if ONLINE_TTS_ENABLED:
        try:
            return await _tts_edge(text, edge_voice)
        except Exception:
            logger.warning("Edge-TTS failed for %s, trying Piper fallback", lang)
    else:
        logger.info("Online TTS disabled; using Piper fallback for %s", lang)

    if lang in PIPER_VOICES:
        return await _tts_piper(text, PIPER_VOICES[lang])
    return await _tts_piper(text, PIPER_VOICES["fr"])


async def _tts_edge(text: str, voice: str) -> bytes:
    """Use edge-tts for Arabic/Tunisian voice."""
    import edge_tts

    text = re.sub(r'[\ud800-\udfff]', '', text).strip()
    communicate = edge_tts.Communicate(text, voice)
    audio_buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])

    return audio_buffer.getvalue()


async def _tts_piper(text: str, model_path: str) -> bytes:
    """Use Piper TTS for French/English."""
    import wave

    # Supprimer les surrogates et caractères invalides
    text = re.sub(r'[\ud800-\udfff]', '', text).strip()

    if not Path(model_path).exists():
        raise RuntimeError(
            f"Piper voice model not found: {model_path}. "
            f"Download it from huggingface.co/rhasspy/piper-voices"
        )

    proc = await asyncio.create_subprocess_exec(
        _resolve_piper_executable(),
        "--model", model_path,
        "--output-raw",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    text_bytes = text.encode("utf-8", errors="replace")
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(input=text_bytes), timeout=30.0)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError("Piper TTS timed out after 30 seconds")

    if proc.returncode != 0:
        logger.error("Piper TTS error: %s", stderr.decode())
        raise RuntimeError(f"Piper TTS failed: {stderr.decode()}")

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(22050)
        wav_file.writeframes(stdout)

    return wav_buffer.getvalue()
