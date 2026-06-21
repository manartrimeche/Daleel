"""Tests for voice_service — enums, constants, and helpers."""

from app.services.voice_service import (
    Language,
    EDGE_TTS_VOICES,
    PIPER_VOICES,
    _resolve_piper_executable,
    assess_transcription_confidence,
)


class TestLanguageEnum:
    def test_values(self):
        assert Language.FR == "fr"
        assert Language.EN == "en"
        assert Language.AR == "ar"

    def test_is_str(self):
        assert isinstance(Language.FR, str)


class TestVoiceConstants:
    def test_edge_tts_has_arabic(self):
        assert "ar" in EDGE_TTS_VOICES
        assert "TN" in EDGE_TTS_VOICES["ar"]

    def test_piper_has_fr_en(self):
        assert "fr" in PIPER_VOICES
        assert "en" in PIPER_VOICES

    def test_piper_paths_are_onnx(self):
        for lang, path in PIPER_VOICES.items():
            assert path.endswith(".onnx"), f"{lang} path should end with .onnx"


class TestResolvePiperExecutable:
    def test_returns_string(self):
        result = _resolve_piper_executable()
        assert isinstance(result, str)

    def test_fallback_is_piper(self):
        result = _resolve_piper_executable()
        assert "piper" in result.lower()


class TestTranscriptionConfidence:
    def test_accepts_clear_transcription(self):
        result = assess_transcription_confidence(
            "Quelles sont les obligations du gerant ?",
            language_probability=0.92,
            segments=[
                {
                    "avg_logprob": -0.25,
                    "no_speech_prob": 0.05,
                    "compression_ratio": 1.1,
                }
            ],
        )

        assert result["is_confident"] is True
        assert result["confidence_reasons"] == []

    def test_rejects_likely_silence_hallucination(self):
        result = assess_transcription_confidence(
            "Sous-titres realises par la communaute",
            language_probability=0.22,
            segments=[
                {
                    "avg_logprob": -1.9,
                    "no_speech_prob": 0.94,
                    "compression_ratio": 1.3,
                }
            ],
        )

        assert result["is_confident"] is False
        assert "low_language_probability" in result["confidence_reasons"]
        assert "likely_silence" in result["confidence_reasons"]
