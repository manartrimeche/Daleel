"""Quick smoke tests for fine-tuned model integration.

These tests verify that reasoning_model_service and llm_style_formatter
load correctly and return fallback values when models are not configured.
"""
from app.services import reasoning_model_service, llm_style_formatter


class TestReasoningModelService:
    def test_is_enabled_without_env_returns_false(self, monkeypatch):
        monkeypatch.setenv("DALEEL_REASONING_MODEL_PATH", "")
        assert reasoning_model_service.is_enabled() is False

    def test_classify_domain_empty_text(self):
        domain, conf = reasoning_model_service.classify_domain("")
        assert domain is None
        assert conf == 0.0

    def test_classify_risk_short_text(self):
        risk, conf = reasoning_model_service.classify_risk("ok")
        assert risk is None
        assert conf == 0.0

    def test_is_confident_with_default_threshold(self):
        assert reasoning_model_service.is_confident(0.75) is True   # default threshold 0.7
        assert reasoning_model_service.is_confident(0.65) is False

    def test_extract_facts_empty(self):
        facts = reasoning_model_service.extract_facts("")
        assert facts["_source"] == "empty"
        assert facts["parties"] == []

    def test_extract_facts_regex_fallback(self):
        text = "Le contrat a été signé le 15/03/2024 pour un montant de 5000 TND."
        facts = reasoning_model_service.extract_facts(text)
        assert facts["_source"] == "regex_fallback"
        assert any("15/03/2024" in d for d in facts["dates"])
        assert any("5000" in a for a in facts["amounts"])


class TestLLMStyleFormatter:
    def test_system_prompt_fr_contains_sections(self):
        assert "7" in llm_style_formatter._SYSTEM_PROMPT_FR
        assert "N'INVENTE AUCUN" in llm_style_formatter._SYSTEM_PROMPT_FR

    def test_system_prompt_ar_contains_sections(self):
        assert "7" in llm_style_formatter._SYSTEM_PROMPT_AR
        assert "دليل" in llm_style_formatter._SYSTEM_PROMPT_AR

    def test_build_payload_from_orchestration(self):
        payload = llm_style_formatter.build_payload_from_orchestration(
            user_question="Test ?",
            language="fr",
            extracted_facts={"parties": ["A", "B"]},
            legal_context=[{"article_ref": "Art.1", "text": "texte"}],
            findings=[],
            actions=[{"title": "Act1", "priority": "high"}],
        )
        assert payload["user_question"] == "Test ?"
        assert payload["language"] == "fr"
        assert payload["actions"][0]["title"] == "Act1"

    def test_is_enabled_without_env_returns_false(self, monkeypatch):
        monkeypatch.setenv("DALEEL_STYLE_MODEL", "")
        assert llm_style_formatter.is_enabled() is False
