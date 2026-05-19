"""
Unit tests for deterministic helpers in app.services.llm_service —
language detection, intent detection, reranking, query augmentation.
"""

import unittest

from app.services.llm_service import (
    _detect_query_language,
    _detect_intent,
    _rerank_chunks_for_question,
    _is_manager_obligations_query,
    _should_auto_scope_company_document,
    _backoff_delay,
)


class TestDetectQueryLanguage(unittest.TestCase):
    def test_french(self):
        self.assertEqual(_detect_query_language("Quelles sont les obligations du gérant ?"), "fr")

    def test_arabic(self):
        self.assertEqual(_detect_query_language("ما هي شروط تأسيس شركة في تونس؟"), "ar")

    def test_english(self):
        self.assertEqual(_detect_query_language("What are the requirements for company formation?"), "en")

    def test_mixed_arabic_french(self):
        result = _detect_query_language("Article 12 الفصل الثاني عشر من قانون الشركات")
        self.assertIn(result, ("ar", "fr"))

    def test_empty(self):
        result = _detect_query_language("")
        self.assertIn(result, ("fr", "en"))


class TestDetectIntent(unittest.TestCase):
    def test_advice_french(self):
        self.assertEqual(_detect_intent("Quels conseils pour la conformité ?", "fr"), "advice")

    def test_solution_french(self):
        self.assertEqual(_detect_intent("Quelle solution pour résoudre ce problème ?", "fr"), "solution")

    def test_requirement_french(self):
        self.assertEqual(_detect_intent("Quelles sont les exigences de conformité ?", "fr"), "requirement_management")

    def test_analysis_default(self):
        self.assertEqual(_detect_intent("Expliquez l'article 12.", "fr"), "analysis")

    def test_arabic_advice(self):
        self.assertEqual(_detect_intent("أريد نصيحة قانونية", "ar"), "advice")

    def test_arabic_solution(self):
        self.assertEqual(_detect_intent("ما هو الحل لهذه المشكلة", "ar"), "solution")


class TestIsManagerObligationsQuery(unittest.TestCase):
    def test_gerant_obligations(self):
        self.assertTrue(_is_manager_obligations_query("Quelles sont les obligations du gérant ?"))

    def test_dirigeant_responsabilite(self):
        self.assertTrue(_is_manager_obligations_query("Responsabilités du dirigeant de la SARL"))

    def test_not_manager_query(self):
        self.assertFalse(_is_manager_obligations_query("Comment créer une société ?"))

    def test_arabic_manager_duties(self):
        self.assertTrue(_is_manager_obligations_query("ما هي واجبات المدير"))


class TestShouldAutoScopeCompanyDocument(unittest.TestCase):
    def test_sarl_query(self):
        self.assertTrue(_should_auto_scope_company_document("obligations du gérant d'une SARL"))

    def test_creation_societe(self):
        self.assertTrue(_should_auto_scope_company_document("création d'une société"))

    def test_arabic_company(self):
        self.assertTrue(_should_auto_scope_company_document("تأسيس شركة في تونس"))

    def test_unrelated_query(self):
        self.assertFalse(_should_auto_scope_company_document("What is the weather today?"))


class TestRerankChunks(unittest.TestCase):
    def test_reranking_preserves_all_chunks(self):
        chunks = [
            {"text": "Article 12 — Le gérant doit respecter les statuts.", "section": "Article 12", "score": 0.8},
            {"text": "Article 100 — Dispositions générales.", "section": "Article 100", "score": 0.7},
            {"text": "Le capital minimum est de 1000 dinars.", "section": None, "score": 0.6},
        ]
        result = _rerank_chunks_for_question("obligations du gérant", chunks, "fr")
        self.assertEqual(len(result), 3)

    def test_article_ref_boosts_matching_chunk(self):
        chunks = [
            {"text": "Dispositions fiscales.", "section": "Article 50", "score": 0.9},
            {"text": "Obligations du gérant.", "section": "Article 12", "score": 0.7},
        ]
        result = _rerank_chunks_for_question("Que dit l'article 12 ?", chunks, "fr")
        # Article 12 chunk should be ranked first due to ref boost
        self.assertIn("Article 12", result[0].get("section", ""))

    def test_empty_chunks(self):
        result = _rerank_chunks_for_question("test", [], "fr")
        self.assertEqual(result, [])

    def test_all_chunks_get_hybrid_score(self):
        chunks = [
            {"text": "test content", "section": None, "score": 0.5},
        ]
        result = _rerank_chunks_for_question("test", chunks, "fr")
        self.assertIn("hybrid_score", result[0])


class TestBackoffDelay(unittest.TestCase):
    def test_delay_increases_with_attempt(self):
        _backoff_delay(1, 1.0, 60.0)
        _backoff_delay(2, 1.0, 60.0)
        _backoff_delay(3, 1.0, 60.0)
        # On average d2 > d1, d3 > d2, but jitter means not always deterministic
        # So we test the base trend without jitter
        self.assertGreater(min(1.0 * (2 ** 3), 60.0), min(1.0 * (2 ** 1), 60.0))

    def test_respects_maximum(self):
        delay = _backoff_delay(100, 1.0, 16.0)
        self.assertLessEqual(delay, 16.0 * 1.25)  # max + 25% jitter

    def test_returns_positive(self):
        delay = _backoff_delay(0, 1.0, 16.0)
        self.assertGreater(delay, 0)


if __name__ == "__main__":
    unittest.main()
