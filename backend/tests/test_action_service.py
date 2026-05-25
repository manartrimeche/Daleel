"""Tests for action_service — _action_to_dict helper and prompt structure."""

from app.services.action_service import _action_to_dict, _ACTION_PROMPT


class TestActionToDict:
    def test_full_action(self):
        action = {
            "id": "act-1",
            "exigence_id": "exig-1",
            "article_version_id": "av-1",
            "modalite": "obligation",
            "action_precise": "Remettre un contrat de travail",
            "conditions": ["dès le premier salarié"],
            "preuve": "Contrat signé",
            "confidence": 0.92,
            "extracted_at": "2026-01-01",
        }
        result = _action_to_dict(action)
        assert result["id"] == "act-1"
        assert result["modalite"] == "obligation"
        assert result["confidence"] == 0.92
        assert isinstance(result["conditions"], list)

    def test_missing_fields_return_none(self):
        result = _action_to_dict({})
        assert result["id"] is None
        assert result["modalite"] is None
        assert result["conditions"] == []
        assert result["preuve"] is None

    def test_null_conditions_returns_empty_list(self):
        result = _action_to_dict({"conditions": None})
        assert result["conditions"] == []

    def test_extra_fields_ignored(self):
        result = _action_to_dict({"id": "x", "extra_field": "ignored"})
        assert "extra_field" not in result
        assert result["id"] == "x"


class TestActionPrompt:
    def test_prompt_has_placeholders(self):
        assert "{exigence_type}" in _ACTION_PROMPT
        assert "{article_reference}" in _ACTION_PROMPT
        assert "{exigence_text}" in _ACTION_PROMPT

    def test_prompt_mentions_json(self):
        assert "JSON" in _ACTION_PROMPT

    def test_prompt_defines_valid_modalites(self):
        for m in ["obligation", "interdiction", "sanction", "condition"]:
            assert m in _ACTION_PROMPT

    def test_prompt_format_works(self):
        result = _ACTION_PROMPT.format(
            exigence_type="obligation",
            article_reference="Art. 14",
            exigence_text="L'employeur doit remettre un contrat",
        )
        assert "obligation" in result
        assert "Art. 14" in result
