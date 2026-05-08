"""Tests for amendment_service.py (Sprint 5).

Covers Arabic numeral normalisation helper.
Note: Service functions using global mongo_db are tested via integration tests.
"""
from app.services import amendment_service as ams


# ─────────────────────────────────────────────────────────────
# Helpers — Arabic numeral normalisation
# ─────────────────────────────────────────────────────────────

class TestArabicDigitNormalisation:
    def test_arabic_to_western_digits(self):
        assert ams._norm_article_num("٩٥") == "95"
        assert ams._norm_article_num("١٥") == "15"
        assert ams._norm_article_num("٠١٢٣٤٥٦٧٨٩") == "0123456789"

    def test_mixed_text_preserved(self):
        text = "المادة ٩٥ من القانون"
        assert ams._norm_article_num(text) == "المادة 95 من القانون"

    def test_western_digits_unchanged(self):
        assert ams._norm_article_num("Article 95") == "Article 95"

    def test_empty_string(self):
        assert ams._norm_article_num("") == ""
