"""
Voice assistant service — STT (faster-whisper) + TTS (Piper / Edge-TTS).
"""

import asyncio
import io
import logging
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


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    with _whisper_lock:
        if _whisper_model is not None:
            return _whisper_model
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            "medium",
            device="cpu",
            compute_type="int8",
        )
        logger.info("faster-whisper model loaded (medium, CPU/int8)")
    return _whisper_model


async def transcribe_audio(audio_bytes: bytes) -> dict:
    """Transcribe audio bytes to text. Returns {text, language, segments}."""
    loop = asyncio.get_event_loop()

    def _transcribe():
        model = _get_whisper_model()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        segments, info = model.transcribe(
            tmp_path,
            beam_size=5,
            language=None,  # auto-detect from audio
            vad_filter=True,
        )
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        Path(tmp_path).unlink(missing_ok=True)

        return {
            "text": " ".join(text_parts),
            "language": info.language,
            "language_probability": info.language_probability,
        }

    return await loop.run_in_executor(None, _transcribe)


# ─── TTS: Piper (FR/EN) + Edge-TTS (AR tunisien) ──────────────────────────────

EDGE_TTS_VOICES = {
    "ar": "ar-TN-ReemNeural",  # Tunisien femme
    "ar_male": "ar-TN-HediNeural",  # Tunisien homme
}

PIPER_VOICES_DIR = Path.home()

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


async def synthesize_speech(text: str, language: str = "fr") -> bytes:
    """Convert text to speech audio (WAV/MP3 bytes)."""
    lang = language[:2].lower()

    if lang == "ar":
        return await _tts_edge(text, EDGE_TTS_VOICES["ar"])
    elif lang in PIPER_VOICES:
        return await _tts_piper(text, PIPER_VOICES[lang])
    else:
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
