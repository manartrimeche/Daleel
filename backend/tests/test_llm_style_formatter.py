"""Tests for llm_style_formatter — prompt selection, enablement, payload builder."""

import os
from unittest.mock import patch

from app.services.llm_style_formatter import (
    _system_prompt,
    _SYSTEM_PROMPT_FR,
    _SYSTEM_PROMPT_AR,
    _SYSTEM_PROMPT_EN,
    is_enabled,
    build_payload_from_orchestration,
)


class TestSystemPrompt:
    def test_french_default(self):
        assert _system_prompt("fr") == _SYSTEM_PROMPT_FR

    def test_arabic(self):
        assert _system_prompt("ar") == _SYSTEM_PROMPT_AR

    def test_english(self):
        assert _system_prompt("en") == _SYSTEM_PROMPT_EN

    def test_unknown_returns_french(self):
        assert _system_prompt("de") == _SYSTEM_PROMPT_FR
        assert _system_prompt("") == _SYSTEM_PROMPT_FR

    def test_prompts_are_nonempty(self):
        assert len(_SYSTEM_PROMPT_FR) > 100
        assert len(_SYSTEM_PROMPT_AR) > 100
        assert len(_SYSTEM_PROMPT_EN) > 100


class TestIsEnabled:
    def test_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=False):
            if "DALEEL_STYLE_MODEL" in os.environ:
                del os.environ["DALEEL_STYLE_MODEL"]
            assert is_enabled() is False

    def test_empty_env_var(self):
        with patch.dict(os.environ, {"DALEEL_STYLE_MODEL": ""}):
            assert is_enabled() is False

    def test_whitespace_env_var(self):
        with patch.dict(os.environ, {"DALEEL_STYLE_MODEL": "   "}):
            assert is_enabled() is False

    def test_nonexistent_path(self):
        with patch.dict(os.environ, {"DALEEL_STYLE_MODEL": "/tmp/nonexistent_model_xyz"}):
            assert is_enabled() is False


class TestBuildPayloadFromOrchestration:
    def test_minimal_payload(self):
        result = build_payload_from_orchestration(
            user_question="Test?",
            language="fr",
            extracted_facts=None,
            legal_context=None,
            findings=None,
            actions=None,
        )
        assert result["user_question"] == "Test?"
        assert result["language"] == "fr"
        assert result["extracted_facts"] == {}
        assert result["legal_context"] == []
        assert result["findings"] == []
        assert result["actions"] == []
        assert result["draft_answer"] == ""

    def test_with_data(self):
        result = build_payload_from_orchestration(
            user_question="Comment?",
            language="ar",
            extracted_facts={"sector": "IT"},
            legal_context=[{"article": "Art. 14"}],
            findings=[{"text": "finding"}],
            actions=[{"text": "action"}],
            draft_answer="Draft",
        )
        assert result["extracted_facts"]["sector"] == "IT"
        assert len(result["legal_context"]) == 1
        assert result["draft_answer"] == "Draft"

    def test_serializes_to_dict_objects(self):
        class FakeObj:
            def to_dict(self):
                return {"key": "val"}

        result = build_payload_from_orchestration(
            user_question="Q",
            language="fr",
            extracted_facts=None,
            legal_context=None,
            findings=[FakeObj()],
            actions=None,
        )
        assert result["findings"] == [{"key": "val"}]

    def test_serializes_dataclass_like_objects(self):
        class FakeDC:
            def __init__(self):
                self.field1 = "a"
                self.field2 = "b"
                self._private = "hidden"

        result = build_payload_from_orchestration(
            user_question="Q",
            language="fr",
            extracted_facts=None,
            legal_context=None,
            findings=None,
            actions=[FakeDC()],
        )
        assert result["actions"][0]["field1"] == "a"
        assert "_private" not in result["actions"][0]

    def test_none_question_becomes_empty(self):
        result = build_payload_from_orchestration(
            user_question=None,
            language="fr",
            extracted_facts=None,
            legal_context=None,
            findings=None,
            actions=None,
        )
        assert result["user_question"] == ""
