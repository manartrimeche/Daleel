"""Tests for voice_service — enums, constants, and helpers."""

from app.services.voice_service import (
    Language,
    EDGE_TTS_VOICES,
    PIPER_VOICES,
    _resolve_piper_executable,
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
