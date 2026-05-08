"""Unit tests for app.processing.text_utils."""

import unittest

from app.processing.text_utils import (
    clean_arabic_ocr_text,
    clean_text,
    detect_language,
    is_text_garbled,
)


class TestCleanText(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(clean_text("hello   world"), "hello world")

    def test_strips_control_chars(self):
        self.assertEqual(clean_text("abc\x00\x01\x02def"), "abcdef")

    def test_normalises_unicode(self):
        result = clean_text("\ufb01")  # fi ligature
        self.assertEqual(result, "fi")

    def test_collapses_excessive_newlines(self):
        self.assertEqual(clean_text("a\n\n\n\n\nb"), "a\n\nb")

    def test_strips_leading_trailing(self):
        self.assertEqual(clean_text("  hello  "), "hello")

    def test_empty_string(self):
        self.assertEqual(clean_text(""), "")

    def test_tabs_collapsed(self):
        self.assertEqual(clean_text("a\t\tb"), "a b")


class TestCleanArabicOcrText(unittest.TestCase):
    def test_normalises_arabic_chars_punctuation_and_digits(self):
        raw = "إِنَّ  آحكام,القانون;  واضحة?  في المادة١٢."
        self.assertEqual(
            clean_arabic_ocr_text(raw),
            "ان احكام، القانون؛ واضحة؟ في المادة 12.",
        )

    def test_removes_noise_and_repairs_spaced_letters(self):
        raw = "ا ل ف ص ل   5 @#$ A Bx ينطبق"
        self.assertEqual(clean_arabic_ocr_text(raw), "الفصل 5 ينطبق")

    def test_ta_marbuta_mode_heh(self):
        raw = "شركة مساهمة تونسية"
        self.assertEqual(clean_arabic_ocr_text(raw, ta_marbuta_form="ه"), "شركه مساهمه تونسيه")

    def test_removes_short_latin_noise_but_keeps_longer_tokens(self):
        raw = "هذا نص OCR مع A B CDE"
        self.assertEqual(clean_arabic_ocr_text(raw), "هذا نص OCR مع CDE")

    def test_invalid_ta_marbuta_mode_raises(self):
        with self.assertRaises(ValueError):
            clean_arabic_ocr_text("نص", ta_marbuta_form="x")

    def test_deterministic_output(self):
        raw = "ا ل ق ا ن و ن , نافذ؟"
        first = clean_arabic_ocr_text(raw)
        second = clean_arabic_ocr_text(raw)
        self.assertEqual(first, second)


class TestDetectLanguage(unittest.TestCase):
    def test_french_text(self):
        self.assertEqual(
            detect_language("Les obligations du gerant de la societe sont definies par la loi."),
            "fr",
        )

    def test_arabic_text(self):
        self.assertEqual(
            detect_language("يجب على المسير ان يحترم القانون التونسي"),
            "ar",
        )

    def test_mixed_text(self):
        result = detect_language("Article 12 - الفصل الثاني عشر من القانون")
        self.assertIn(result, ("ar", "ar+fr"))

    def test_empty_text(self):
        self.assertEqual(detect_language(""), "unknown")

    def test_numbers_only(self):
        self.assertEqual(detect_language("123 456 789"), "unknown")


class TestIsTextGarbled(unittest.TestCase):
    def test_clean_french_is_not_garbled(self):
        text = "Les societes commerciales sont regies par le code des societes commerciales."
        self.assertFalse(is_text_garbled(text))

    def test_clean_arabic_is_not_garbled(self):
        text = "يجب على كل شركة تجارية ان تلتزم بالقانون التونسي المتعلق بالشركات التجارية"
        self.assertFalse(is_text_garbled(text, expect_arabic=True))

    def test_short_text_not_flagged(self):
        self.assertFalse(is_text_garbled("short"))

    def test_many_single_char_words_is_garbled(self):
        text = " ".join(list("a b c d e f g h i j k l m n o p q"))
        self.assertTrue(is_text_garbled(text))

    def test_control_chars_in_raw_triggers_garbled(self):
        clean = "This is some text that appears clean after processing step"
        raw = "This\x01is\x02some\x03text\x04that\x05is\x06garbled\x07and\x08bad"
        self.assertTrue(is_text_garbled(clean, raw_text=raw))

    def test_arabic_expected_but_latin_found(self):
        text = "This is entirely a Latin text document with no Arabic characters at all really"
        self.assertTrue(is_text_garbled(text, expect_arabic=True))


if __name__ == "__main__":
    unittest.main()
