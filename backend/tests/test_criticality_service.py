"""
Unit tests for app.services.criticality_service — rule-based criticality scoring.
"""

import unittest

from app.services.criticality_service import compute_criticality_score, score_to_level


class TestScoreToLevel(unittest.TestCase):
    def test_critique(self):
        self.assertEqual(score_to_level(0.75), "critique")
        self.assertEqual(score_to_level(0.90), "critique")
        self.assertEqual(score_to_level(1.0), "critique")

    def test_importante(self):
        self.assertEqual(score_to_level(0.50), "importante")
        self.assertEqual(score_to_level(0.74), "importante")

    def test_secondaire(self):
        self.assertEqual(score_to_level(0.49), "secondaire")
        self.assertEqual(score_to_level(0.0), "secondaire")


class TestComputeCriticalityScore(unittest.TestCase):
    def test_sanction_modalite_high_base(self):
        action = {"modalite": "sanction", "action_precise": "Amende de 5000 DT."}
        score, factors = compute_criticality_score(action)
        self.assertGreaterEqual(score, 0.75)
        self.assertEqual(score_to_level(score), "critique")

    def test_obligation_modalite(self):
        action = {"modalite": "obligation", "action_precise": "Déposer les comptes annuels."}
        score, factors = compute_criticality_score(action)
        self.assertGreaterEqual(score, 0.50)
        self.assertGreater(len(factors), 0)

    def test_condition_modalite_low(self):
        action = {"modalite": "condition", "action_precise": "Si applicable, informer le registre."}
        score, factors = compute_criticality_score(action)
        self.assertLess(score, 0.50)

    def test_sanction_keywords_boost(self):
        base_action = {"modalite": "obligation", "action_precise": "Respecter les délais."}
        base_score, _ = compute_criticality_score(base_action)

        boosted_action = {"modalite": "obligation", "action_precise": "Respecter les délais sous peine d'amende."}
        boosted_score, factors = compute_criticality_score(boosted_action)
        self.assertGreater(boosted_score, base_score)
        self.assertTrue(any("sanction" in f.lower() or "pénalité" in f.lower() for f in factors))

    def test_monetary_amount_boost(self):
        base_action = {"modalite": "obligation", "action_precise": "Payer la cotisation."}
        base_score, _ = compute_criticality_score(base_action)

        money_action = {"modalite": "obligation", "action_precise": "Amende de 10000 DT."}
        money_score, _ = compute_criticality_score(money_action)
        self.assertGreater(money_score, base_score)

    def test_domain_boost_personal_data(self):
        action = {"modalite": "obligation", "action_precise": "Protection des données personnelles conformément à l'INPDP."}
        score, factors = compute_criticality_score(action)
        self.assertTrue(any("données personnelles" in f.lower() for f in factors))

    def test_domain_boost_health_safety(self):
        action = {"modalite": "obligation", "action_precise": "Assurer la santé au travail et fournir les EPI."}
        score, factors = compute_criticality_score(action)
        self.assertTrue(any("santé" in f.lower() or "sécurité" in f.lower() for f in factors))

    def test_conditional_language_penalty(self):
        action = {"modalite": "obligation", "action_precise": "Le cas échéant, déposer une déclaration complémentaire."}
        score, factors = compute_criticality_score(action)
        self.assertTrue(any("conditionnel" in f.lower() or "facultatif" in f.lower() for f in factors))

    def test_arabic_sanction_keyword(self):
        action = {"modalite": "obligation", "action_precise": "يعاقب بغرامة مالية كل من يخالف أحكام هذا القانون"}
        score, factors = compute_criticality_score(action)
        self.assertGreaterEqual(score, 0.65)

    def test_unknown_modalite_gets_default(self):
        action = {"modalite": "unknown_type", "action_precise": "Something."}
        score, factors = compute_criticality_score(action)
        self.assertIsInstance(score, float)
        self.assertGreater(len(factors), 0)

    def test_score_capped_at_one(self):
        action = {
            "modalite": "sanction",
            "action_precise": "Amende de 50000 DT et emprisonnement. Protection des données personnelles.",
        }
        score, _ = compute_criticality_score(action)
        self.assertLessEqual(score, 1.0)

    def test_score_minimum_zero(self):
        action = {"modalite": "condition", "action_precise": "Le cas échéant, éventuellement, si applicable, sous réserve."}
        score, _ = compute_criticality_score(action)
        self.assertGreaterEqual(score, 0.0)


if __name__ == "__main__":
    unittest.main()
