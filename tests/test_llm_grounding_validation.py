import unittest

from app.services import llm_service


class TestLlmGroundingValidation(unittest.TestCase):
    def test_extract_article_refs_supports_multiple_formats(self):
        text = (
            "Selon l'Article 12, puis Art. 34, et aussi المادة 56, "
            "les obligations sont applicables."
        )
        refs = llm_service._extract_answer_article_refs(text)
        self.assertEqual(refs, {"12", "34", "56"})

    def test_no_refs_and_language_ok_does_not_reground(self):
        chunks = [
            {
                "section": "Article 12",
                "text": "Les obligations légales générales s'appliquent.",
            }
        ]
        answer = "Cette obligation est applicable selon les extraits fournis."

        result = llm_service._validate_answer_grounding(answer, chunks, "fr")
        self.assertFalse(result["should_reground"])
        self.assertTrue(result["language_ok"])

    def test_unverified_refs_trigger_reground(self):
        chunks = [
            {
                "section": "Article 12",
                "text": "Exigences de conformité du dossier.",
            }
        ]
        answer = "La règle est fixée par Article 999."

        result = llm_service._validate_answer_grounding(answer, chunks, "fr")
        self.assertTrue(result["should_reground"])
        self.assertEqual(result["verified_refs"], set())
        self.assertEqual(result["unsupported_refs"], {"999"})

    def test_partial_verified_refs_do_not_force_reground(self):
        chunks = [
            {
                "section": "Article 12",
                "text": "Exigences de conformité du dossier.",
            }
        ]
        answer = "Voir Article 12 et Article 999 pour le cadre."

        result = llm_service._validate_answer_grounding(answer, chunks, "fr")
        self.assertFalse(result["should_reground"])
        self.assertEqual(result["verified_refs"], {"12"})
        self.assertEqual(result["unsupported_refs"], {"999"})

    def test_language_non_compliance_triggers_reground(self):
        chunks = [
            {
                "section": "Article 12",
                "text": "تتعلق هذه الأحكام بالامتثال القانوني.",
            }
        ]
        answer = "This answer is in English only."

        result = llm_service._validate_answer_grounding(answer, chunks, "ar")
        self.assertTrue(result["should_reground"])
        self.assertFalse(result["language_ok"])


class TestForeignWordContamination(unittest.TestCase):
    """Regression tests for observed LLM language contamination bugs."""

    def test_trabajar_detected_in_arabic(self):
        text = "تعتبر ساعات العمل الإضافية تلك التي ي trabajarها العامل أكثر"
        self.assertTrue(llm_service._has_foreign_word_contamination(text, "ar"))

    def test_magazine_du_travail_detected(self):
        text = "وفقًا للمادة 28 من Magazine du Travail، يقع على صاحب العمل مسؤولية"
        self.assertTrue(llm_service._has_foreign_word_contamination(text, "ar"))

    def test_clean_arabic_passes(self):
        text = "وفقًا للمادة 28 من مجلة الشغل يقع على صاحب العمل مسؤولية دفع الأجور"
        self.assertFalse(llm_service._has_foreign_word_contamination(text, "ar"))

    def test_sarl_allowed_in_arabic(self):
        text = "الشركة من نوع SARL في تونس"
        self.assertFalse(llm_service._has_foreign_word_contamination(text, "ar"))

    def test_inpdp_allowed_in_arabic(self):
        text = "يجب التصريح لدى INPDP حسب القانون"
        self.assertFalse(llm_service._has_foreign_word_contamination(text, "ar"))

    def test_not_triggered_for_french(self):
        text = "Voici les obligations selon la loi tunisienne."
        self.assertFalse(llm_service._has_foreign_word_contamination(text, "fr"))


class TestLanguageComplianceContamination(unittest.TestCase):
    """_is_language_compliant must reject contaminated Arabic and wrong-language answers."""

    def test_arabic_with_trabajar_fails(self):
        text = (
            "تعتبر ساعات العمل الإضافية تلك التي ي trabajarها العامل أكثر من الساعات "
            "المحددة في عقد العمل"
        )
        self.assertFalse(llm_service._is_language_compliant(text, "ar"))

    def test_arabic_with_magazine_fails(self):
        text = (
            "وفقًا للمادة 28 من Magazine du Travail، يقع على صاحب العمل مسؤولية "
            "دفع الأجور عن ساعات العمل الإضافية"
        )
        self.assertFalse(llm_service._is_language_compliant(text, "ar"))

    def test_english_answer_fails_french_check(self):
        text = (
            "The primary legal framework governing data protection in Tunisia is "
            "Law No. 63-2004 on the protection of personal data which aims to "
            "safeguard individuals privacy and personal information."
        )
        self.assertFalse(llm_service._is_language_compliant(text, "fr"))

    def test_clean_arabic_passes(self):
        text = "يجب على صاحب العمل دفع الأجور عن ساعات العمل الإضافية حسب مجلة الشغل"
        self.assertTrue(llm_service._is_language_compliant(text, "ar"))


class TestStripContaminatedLines(unittest.TestCase):
    """_strip_non_compliant_lines must remove lines with foreign words."""

    def test_strips_trabajar_line(self):
        answer = (
            "#### 1. الإطار القانوني\n"
            "تعتبر ساعات العمل الإضافية تلك التي ي trabajarها العامل\n"
            "يجب على صاحب العمل دفع الأجور حسب مجلة الشغل\n"
        )
        result = llm_service._strip_non_compliant_lines(answer, "ar")
        self.assertNotIn("trabajar", result)
        self.assertIn("مجلة الشغل", result)

    def test_strips_magazine_line(self):
        answer = (
            "المادة القانونية المادة 28 من Magazine du Travail\n"
            "يجب على صاحب العمل دفع الأجور حسب مجلة الشغل\n"
        )
        result = llm_service._strip_non_compliant_lines(answer, "ar")
        self.assertNotIn("Magazine", result)
        self.assertIn("مجلة الشغل", result)


if __name__ == "__main__":
    unittest.main()
