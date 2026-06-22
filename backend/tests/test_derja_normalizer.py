"""
Tests for the Derja (Tunisian dialect) normalizer.
"""

import unittest

from app.processing.derja_normalizer import (
    detect_derja,
    normalize_derja_to_french,
    normalize_if_derja,
    build_derja_context_note,
)


class TestDetectDerja(unittest.TestCase):
    """Test derja detection heuristic."""

    def test_clear_derja_query_employment(self):
        """Typical Tunisian dialect query about employment."""
        text = "خدّام في شركة وما عطاونيش عقد خدمة، شنوة حقوقي؟"
        self.assertTrue(detect_derja(text))

    def test_clear_derja_query_unpaid(self):
        """Tunisian dialect about unpaid wages."""
        text = "باتروني ما خلّصنيش من 3 شهور، شنوة نعمل؟ نجّم نمشي للتفقدية؟"
        self.assertTrue(detect_derja(text))

    def test_clear_derja_query_company(self):
        """Tunisian dialect about opening a company."""
        text = "نحب نعرف شنوة الإجراءات باش نفتح شركة في تونس"
        self.assertTrue(detect_derja(text))

    def test_clear_derja_query_company_nhel(self):
        """Tunisian 'nhell charika' means open/create a company."""
        text = "شنوّة لازمني باش نحلّ شركة في تونس؟"
        self.assertTrue(detect_derja(text))

    def test_derja_with_why(self):
        """Derja question using 'علاش' (why)."""
        text = "علاش باتروني ما يحبش يعطيني عقد خدمة؟"
        self.assertTrue(detect_derja(text))

    def test_msa_not_detected(self):
        """Modern Standard Arabic should NOT trigger derja detection."""
        text = "ما هي حقوق العامل الذي لم يحصل على عقد عمل؟"
        self.assertFalse(detect_derja(text))

    def test_french_not_detected(self):
        """French text should not trigger derja detection."""
        text = "Quels sont les droits d'un employé sans contrat de travail ?"
        self.assertFalse(detect_derja(text))

    def test_english_not_detected(self):
        """English text should not trigger derja detection."""
        text = "What are the rights of a worker without a contract?"
        self.assertFalse(detect_derja(text))

    def test_empty_string(self):
        self.assertFalse(detect_derja(""))

    def test_single_derja_word_insufficient(self):
        """A single derja marker should NOT trigger (need >= 2)."""
        text = "شنوة"
        self.assertFalse(detect_derja(text))

    def test_mixed_derja_french(self):
        """Mixed derja + French (common in Tunisia) should be detected."""
        text = "نحب نعرف les droits متاعي باش نمشي للتفقدية"
        self.assertTrue(detect_derja(text))


class TestNormalizeDerjaToFrench(unittest.TestCase):
    """Test token-level replacement."""

    def test_basic_replacement(self):
        """Known tokens should be replaced with French equivalents."""
        result = normalize_derja_to_french("شنوة حقوقي")
        self.assertIn("quoi", result.lower())
        self.assertIn("mes droits", result.lower())

    def test_employer_replacement(self):
        """باتروني should become patron/employeur."""
        result = normalize_derja_to_french("باتروني ما خلّصنيش")
        self.assertIn("patron", result.lower())
        self.assertIn("payé", result.lower())

    def test_inspection_replacement(self):
        """التفقدية should become inspection du travail."""
        result = normalize_derja_to_french("نمشي للتفقدية")
        self.assertIn("inspection", result.lower())

    def test_unknown_words_preserved(self):
        """Words not in the dictionary should remain unchanged."""
        text = "كلمة_غريبة شنوة"
        result = normalize_derja_to_french(text)
        self.assertIn("كلمة_غريبة", result)

    def test_company_creation_nhel_replacement(self):
        """نحلّ شركة should normalize to company creation, not dissolution."""
        result = normalize_derja_to_french("شنوّة لازمني باش نحلّ شركة في تونس؟")
        self.assertIn("crée une société", result)


class TestNormalizeIfDerja(unittest.TestCase):
    """Test the main pipeline entry point."""

    def test_derja_returns_french_query(self):
        """Derja input → returns normalized French with context note."""
        effective, original, is_derja = normalize_if_derja(
            "خدّام في شركة وما عطاونيش عقد خدمة، شنوة حقوقي؟"
        )
        self.assertTrue(is_derja)
        self.assertIn("dialecte tunisien", effective)
        self.assertIn("خدّام", original)

    def test_french_passes_through(self):
        """French input → passthrough, is_derja=False."""
        text = "Quels sont mes droits sans contrat de travail ?"
        effective, original, is_derja = normalize_if_derja(text)
        self.assertFalse(is_derja)
        self.assertEqual(effective, text)
        self.assertEqual(original, text)

    def test_msa_passes_through(self):
        """MSA input → passthrough, is_derja=False."""
        text = "ما هي حقوق العامل في القانون التونسي؟"
        effective, original, is_derja = normalize_if_derja(text)
        self.assertFalse(is_derja)

    def test_effective_contains_both_original_and_normalized(self):
        """The context note should contain both original and translation."""
        effective, original, is_derja = normalize_if_derja(
            "باتروني ما خلّصنيش من 3 شهور، شنوة نعمل؟"
        )
        self.assertTrue(is_derja)
        # Contains the original derja
        self.assertIn("باتروني", effective)
        # Contains French translation keywords
        self.assertIn("Traduction approximative", effective)


class TestBuildDerjaContextNote(unittest.TestCase):
    """Test context note generation."""

    def test_note_structure(self):
        note = build_derja_context_note(
            "شنوة حقوقي",
            "quoi mes droits",
        )
        self.assertIn("dialecte tunisien", note)
        self.assertIn("شنوة حقوقي", note)
        self.assertIn("quoi mes droits", note)
        self.assertIn("Réponds en français", note)


if __name__ == "__main__":
    unittest.main()
