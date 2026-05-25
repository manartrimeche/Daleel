"""Tests for text_utils — clean_text, clean_arabic_ocr_text, detect_language, detect_query_language, is_text_garbled, fix_arabic."""

import pytest

from app.processing.text_utils import (
    clean_text,
    clean_arabic_ocr_text,
    detect_language,
    detect_query_language,
    is_text_garbled,
    fix_arabic,
)


class TestCleanText:
    def test_strips_whitespace(self):
        assert clean_text("  hello  ") == "hello"

    def test_collapses_spaces(self):
        assert clean_text("a    b") == "a b"

    def test_collapses_newlines(self):
        assert clean_text("a\n\n\n\nb") == "a\n\nb"

    def test_removes_control_chars(self):
        assert clean_text("hello\x00world") == "helloworld"

    def test_unicode_normalize(self):
        result = clean_text("ﬁ")
        assert result == "fi"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_tabs_collapsed(self):
        assert clean_text("a\t\tb") == "a b"


class TestCleanArabicOcrText:
    def test_empty_string(self):
        assert clean_arabic_ocr_text("") == ""

    def test_invalid_ta_marbuta_form(self):
        with pytest.raises(ValueError):
            clean_arabic_ocr_text("test", ta_marbuta_form="x")

    def test_ta_marbuta_heh_form(self):
        result = clean_arabic_ocr_text("شركة", ta_marbuta_form="ه")
        assert "ه" in result

    def test_removes_diacritics(self):
        result = clean_arabic_ocr_text("كِتَابٌ")
        assert "ِ" not in result
        assert "َ" not in result

    def test_removes_tatweel(self):
        result = clean_arabic_ocr_text("كتـــاب")
        assert "ـ" not in result

    def test_normalizes_digits(self):
        result = clean_arabic_ocr_text("المادة ٥٠ من القانون التونسي")
        assert "50" in result

    def test_normalizes_punctuation(self):
        result = clean_arabic_ocr_text("نعم,")
        assert "،" in result

    def test_ocr_corrections(self):
        result = clean_arabic_ocr_text("التاسيسي")
        assert "التأسيسي" in result

    def test_strips_control_chars(self):
        result = clean_arabic_ocr_text("كتاب\x00نص")
        assert "\x00" not in result

    def test_triple_char_collapse(self):
        result = clean_arabic_ocr_text("كككتاب")
        assert "ككك" not in result

    def test_deterministic_output(self):
        raw = "ا ل ق ا ن و ن , نافذ؟"
        first = clean_arabic_ocr_text(raw)
        second = clean_arabic_ocr_text(raw)
        assert first == second

    def test_normalises_arabic_chars_punctuation_and_digits(self):
        raw = "إِنَّ  آحكام,القانون;  واضحة?  في المادة١٢."
        result = clean_arabic_ocr_text(raw)
        assert "12" in result
        assert "،" in result or "؛" in result


class TestDetectLanguage:
    def test_arabic(self):
        assert detect_language("يجب على المشغل احترام قانون الشغل") == "ar"

    def test_french(self):
        assert detect_language("Le droit du travail tunisien") == "fr"

    def test_empty(self):
        assert detect_language("") == "unknown"

    def test_numbers_only(self):
        assert detect_language("12345") == "unknown"

    def test_mixed(self):
        result = detect_language("Article 12 - الفصل الثاني عشر من القانون")
        assert result in ("ar", "ar+fr")


class TestDetectQueryLanguage:
    def test_empty(self):
        assert detect_query_language("") == "en"

    def test_arabic(self):
        assert detect_query_language("ما هو قانون الشغل") == "ar"

    def test_french_with_accents(self):
        assert detect_query_language("société") == "fr"

    def test_french_markers(self):
        assert detect_query_language("quelles sont les obligations juridiques") == "fr"

    def test_english(self):
        assert detect_query_language("what is the law") == "en"

    def test_single_arabic_char_not_enough(self):
        result = detect_query_language("a ع")
        assert result != "ar"


class TestIsTextGarbled:
    def test_short_text_never_garbled(self):
        assert is_text_garbled("short") is False

    def test_normal_text(self):
        assert is_text_garbled("This is a perfectly normal piece of text that is long enough to test.") is False

    def test_control_chars_garbled(self):
        text = "a" * 50 + "\x00" * 10
        assert is_text_garbled(text) is True

    def test_expect_arabic_but_latin(self):
        text = "This is all latin text with no arabic at all and is long enough to trigger detection."
        assert is_text_garbled(text, expect_arabic=True) is True

    def test_single_char_words_garbled(self):
        text = " ".join(list("abcdefghijklmnopq"))
        assert is_text_garbled(text) is True

    def test_raw_text_with_control_chars(self):
        raw = "This\x01is\x02some\x03text\x04that\x05is\x06garbled\x07and\x08bad"
        clean = "This is some text that appears clean after processing step now"
        assert is_text_garbled(clean, raw_text=raw) is True

    def test_raw_text_clean(self):
        text = "a" * 55
        raw = "a" * 55
        assert is_text_garbled(text, raw_text=raw) is False

    def test_arabic_text_not_garbled(self):
        text = "يجب على كل شركة تجارية ان تلتزم بالقانون التونسي المتعلق بالشركات التجارية"
        assert is_text_garbled(text, expect_arabic=True) is False


class TestFixArabic:
    def test_returns_string(self):
        result = fix_arabic("نص عربي")
        assert isinstance(result, str)

    def test_empty_string(self):
        result = fix_arabic("")
        assert result == ""
