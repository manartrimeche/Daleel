"""Tests for audit_service — serialiser helper."""

from app.services.audit_service import _log_to_dict


class TestLogToDict:
    def test_full_record(self):
        log = {
            "id": "log1",
            "actor": "system",
            "event_type": "amendment_applied",
            "loi_id": "l1",
            "article_id": "a1",
            "old_version_id": "v1",
            "new_version_id": "v2",
            "amendment_op_id": "op1",
            "proof_extract": "Article 95 modifié",
            "legal_reference": "Loi 2023-45",
            "confidence": 0.94,
            "details": {"key": "val"},
            "created_at": "2026-01-01",
        }
        result = _log_to_dict(log)
        assert result["id"] == "log1"
        assert result["event_type"] == "amendment_applied"
        assert result["confidence"] == 0.94
        assert result["details"]["key"] == "val"

    def test_empty_record(self):
        result = _log_to_dict({})
        assert result["id"] is None
        assert result["details"] == {}
        assert result["event_type"] is None

    def test_null_details_returns_empty_dict(self):
        result = _log_to_dict({"details": None})
        assert result["details"] == {}

    def test_extra_fields_not_leaked(self):
        result = _log_to_dict({"id": "log1", "internal_flag": True})
        assert "internal_flag" not in result

    def test_all_expected_keys(self):
        result = _log_to_dict({})
        expected = {
            "id", "actor", "event_type", "loi_id", "article_id",
            "old_version_id", "new_version_id", "amendment_op_id",
            "proof_extract", "legal_reference", "confidence",
            "details", "created_at",
        }
        assert set(result.keys()) == expected
