"""Tests for amendment_service — helpers and prompt."""

from app.services.amendment_service import (
    _norm_article_num,
    _op_to_dict,
    _EXTRACTION_PROMPT,
)


class TestNormArticleNum:
    def test_western_digits(self):
        assert _norm_article_num("95") == "95"

    def test_arabic_indic_digits(self):
        assert _norm_article_num("٩٥") == "95"

    def test_mixed_digits(self):
        assert _norm_article_num("١5") == "15"

    def test_strips_whitespace(self):
        assert _norm_article_num("  42  ") == "42"

    def test_bis_suffix(self):
        assert _norm_article_num("95 bis") == "95 bis"

    def test_full_range(self):
        assert _norm_article_num("٠١٢٣٤٥٦٧٨٩") == "0123456789"

    def test_mixed_text(self):
        assert _norm_article_num("المادة ٩٥ من القانون") == "المادة 95 من القانون"

    def test_empty_string(self):
        assert _norm_article_num("") == ""


class TestOpToDict:
    def test_full_op(self):
        op = {
            "id": "op1",
            "amendment_doc_id": "doc1",
            "loi_id": "l1",
            "operation_type": "REPLACE",
            "target_article_key": "CT-Art-95",
            "target_article_number": "95",
            "new_text": "Nouveau texte",
            "proof_extract": "Article 95 est modifié",
            "legal_reference": "Loi 2023-45",
            "confidence": 0.94,
            "status": "pending",
            "applied_at": None,
            "old_version_id": "v1",
            "new_version_id": None,
            "created_at": "2026-01-01",
        }
        result = _op_to_dict(op)
        assert result["id"] == "op1"
        assert result["operation_type"] == "REPLACE"
        assert result["confidence"] == 0.94
        assert result["target_article_key"] == "CT-Art-95"

    def test_empty_op(self):
        result = _op_to_dict({})
        assert result["id"] is None
        assert result["operation_type"] is None
        assert result["status"] is None

    def test_extra_fields_not_leaked(self):
        result = _op_to_dict({"id": "op1", "internal": "secret"})
        assert "internal" not in result

    def test_all_fields_present(self):
        result = _op_to_dict({})
        expected_keys = {
            "id", "amendment_doc_id", "loi_id", "operation_type",
            "target_article_key", "target_article_number", "new_text",
            "proof_extract", "legal_reference", "confidence", "status",
            "applied_at", "old_version_id", "new_version_id", "created_at",
        }
        assert set(result.keys()) == expected_keys


class TestExtractionPrompt:
    def test_has_required_placeholders(self):
        assert "{loi_name}" in _EXTRACTION_PROMPT
        assert "{loi_code}" in _EXTRACTION_PROMPT
        assert "{text}" in _EXTRACTION_PROMPT

    def test_defines_operation_types(self):
        for op_type in ["ADD", "REPLACE", "MODIFY", "REPEAL"]:
            assert op_type in _EXTRACTION_PROMPT

    def test_format_works(self):
        result = _EXTRACTION_PROMPT.format(
            loi_name="Code du travail",
            loi_code="CT",
            text="Article 95 est modifié...",
        )
        assert "Code du travail" in result
        assert "CT" in result

    def test_mentions_json(self):
        assert "JSON" in _EXTRACTION_PROMPT
