"""Tests for criticality_service — scoring engine and helpers."""

from app.services.criticality_service import (
    compute_criticality_score,
    score_to_level,
    _crit_to_dict,
    _BASE_SCORES,
)


class TestScoreToLevel:
    def test_critique(self):
        assert score_to_level(0.75) == "critique"
        assert score_to_level(0.90) == "critique"
        assert score_to_level(1.0) == "critique"

    def test_importante(self):
        assert score_to_level(0.50) == "importante"
        assert score_to_level(0.74) == "importante"

    def test_secondaire(self):
        assert score_to_level(0.49) == "secondaire"
        assert score_to_level(0.0) == "secondaire"


class TestComputeCriticalityScore:
    def test_obligation_base_score(self):
        score, factors = compute_criticality_score({"modalite": "obligation"})
        assert score == _BASE_SCORES["obligation"]
        assert any("obligation" in f for f in factors)

    def test_sanction_base_score(self):
        score, factors = compute_criticality_score({"modalite": "sanction"})
        assert score == _BASE_SCORES["sanction"]

    def test_interdiction_base_score(self):
        score, factors = compute_criticality_score({"modalite": "interdiction"})
        assert score == _BASE_SCORES["interdiction"]

    def test_condition_base_score(self):
        score, factors = compute_criticality_score({"modalite": "condition"})
        assert score == _BASE_SCORES["condition"]

    def test_unknown_modalite_default(self):
        score, _ = compute_criticality_score({"modalite": "weird"})
        assert score == 0.50

    def test_no_modalite(self):
        score, _ = compute_criticality_score({})
        assert score == 0.50

    def test_sanction_keyword_boost(self):
        action = {
            "modalite": "obligation",
            "action_precise": "amende de 5000 dinars",
        }
        score, factors = compute_criticality_score(action)
        assert score > _BASE_SCORES["obligation"]
        assert any("Sanction" in f for f in factors)

    def test_monetary_amount_boost(self):
        action = {
            "modalite": "condition",
            "action_precise": "paiement de 10000 DT",
        }
        score, factors = compute_criticality_score(action)
        assert score > _BASE_SCORES["condition"]
        assert any("Montant" in f for f in factors)

    def test_domain_boost_donnees_personnelles(self):
        action = {
            "modalite": "obligation",
            "action_precise": "protection des données personnelles",
        }
        score, factors = compute_criticality_score(action)
        assert score > _BASE_SCORES["obligation"]
        assert any("données personnelles" in f for f in factors)

    def test_domain_boost_sante(self):
        action = {
            "modalite": "obligation",
            "action_precise": "hygiène et sécurité au travail",
        }
        score, factors = compute_criticality_score(action)
        assert score > _BASE_SCORES["obligation"]

    def test_domain_boost_fiscal(self):
        action = {
            "modalite": "obligation",
            "action_precise": "déclaration fiscale TVA",
        }
        score, factors = compute_criticality_score(action)
        assert score > _BASE_SCORES["obligation"]

    def test_domain_boost_travail_clandestin(self):
        action = {
            "modalite": "obligation",
            "action_precise": "lutte contre le travail non déclaré",
        }
        score, factors = compute_criticality_score(action)
        assert score > _BASE_SCORES["obligation"]

    def test_conditional_language_penalty(self):
        action = {
            "modalite": "obligation",
            "action_precise": "le cas échéant, remettre un document",
        }
        score, factors = compute_criticality_score(action)
        assert score < _BASE_SCORES["obligation"]
        assert any("conditionnel" in f for f in factors)

    def test_score_capped_at_1(self):
        action = {
            "modalite": "sanction",
            "action_precise": "amende 50000 DT pour travail non déclaré données personnelles sécurité au travail",
        }
        score, _ = compute_criticality_score(action)
        assert score <= 1.0

    def test_score_minimum_zero(self):
        action = {
            "modalite": "condition",
            "action_precise": "le cas échéant, éventuellement, si applicable, sous réserve",
        }
        score, _ = compute_criticality_score(action)
        assert score >= 0.0

    def test_conditions_and_preuve_included(self):
        action = {
            "modalite": "condition",
            "conditions": ["amende en cas de non-respect"],
            "preuve": "procès-verbal de contravention",
        }
        score, factors = compute_criticality_score(action)
        assert score > _BASE_SCORES["condition"]

    def test_arabic_sanction_keyword(self):
        action = {
            "modalite": "obligation",
            "action_precise": "عقوبة السجن",
        }
        score, factors = compute_criticality_score(action)
        assert score > _BASE_SCORES["obligation"]

    def test_arabic_domain_donnees(self):
        action = {
            "modalite": "obligation",
            "action_precise": "حماية البيانات الشخصية",
        }
        score, _ = compute_criticality_score(action)
        assert score > _BASE_SCORES["obligation"]

    def test_emprisonnement_keyword(self):
        action = {
            "modalite": "obligation",
            "action_precise": "passible d'emprisonnement",
        }
        score, _ = compute_criticality_score(action)
        assert score > _BASE_SCORES["obligation"]

    def test_multiple_boosts_stack(self):
        action = {
            "modalite": "sanction",
            "action_precise": "amende 10000 DT et données personnelles",
        }
        score_multi, _ = compute_criticality_score(action)
        action_single = {
            "modalite": "sanction",
            "action_precise": "simple infraction",
        }
        score_single, _ = compute_criticality_score(action_single)
        assert score_multi >= score_single


class TestCritToDict:
    def test_full_record(self):
        rec = {
            "id": "c1",
            "action_id": "a1",
            "level": "critique",
            "score": 0.85,
            "factors": ["f1"],
            "computed_at": "2026-01-01",
            "computed_by": "rule-engine",
        }
        result = _crit_to_dict(rec)
        assert result["id"] == "c1"
        assert result["level"] == "critique"
        assert result["factors"] == ["f1"]
        assert result["computed_by"] == "rule-engine"

    def test_missing_fields(self):
        result = _crit_to_dict({})
        assert result["id"] is None
        assert result["factors"] == []
        assert result["action_id"] is None

    def test_null_factors_returns_empty_list(self):
        result = _crit_to_dict({"factors": None})
        assert result["factors"] == []

    def test_extra_fields_not_leaked(self):
        result = _crit_to_dict({"id": "c1", "internal_data": "secret"})
        assert "internal_data" not in result
