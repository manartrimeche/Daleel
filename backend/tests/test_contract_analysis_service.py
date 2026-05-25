"""
Unit tests for contract_analysis_service — score computation, helpers, CRUD.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.contract_analysis_service import (
    _pass4_compute_score,
    _safe_json_parse,
    _strip_code_fences,
    _analysis_to_dict,
    _scoped_query,
    CONTRACT_TYPES,
    CLAUSE_LABELS,
)


# ─────────────────────────────────────────────────────────────
# _strip_code_fences
# ─────────────────────────────────────────────────────────────


class TestStripCodeFences:
    def test_no_fences(self):
        assert _strip_code_fences('{"key": "value"}') == '{"key": "value"}'

    def test_json_fences(self):
        text = '```json\n{"key": "value"}\n```'
        assert _strip_code_fences(text) == '{"key": "value"}'

    def test_plain_fences(self):
        text = '```\n[1, 2, 3]\n```'
        assert _strip_code_fences(text) == '[1, 2, 3]'

    def test_no_closing_fence(self):
        text = '```json\n{"key": "value"}'
        result = _strip_code_fences(text)
        assert '"key"' in result


# ─────────────────────────────────────────────────────────────
# _safe_json_parse
# ─────────────────────────────────────────────────────────────


class TestSafeJsonParse:
    def test_valid_json_object(self):
        assert _safe_json_parse('{"a": 1}') == {"a": 1}

    def test_valid_json_array(self):
        assert _safe_json_parse('[1, 2, 3]') == [1, 2, 3]

    def test_json_with_fences(self):
        assert _safe_json_parse('```json\n{"a": 1}\n```') == {"a": 1}

    def test_invalid_json_returns_fallback(self):
        assert _safe_json_parse("not json at all", fallback=[]) == []

    def test_json_embedded_in_text(self):
        text = 'Voici le résultat : [{"risk": "high"}] fin.'
        result = _safe_json_parse(text)
        assert isinstance(result, list)
        assert result[0]["risk"] == "high"

    def test_empty_string(self):
        assert _safe_json_parse("", fallback={}) == {}


# ─────────────────────────────────────────────────────────────
# _pass4_compute_score
# ─────────────────────────────────────────────────────────────


class TestScoreComputation:
    def test_perfect_score_no_issues(self):
        result = _pass4_compute_score([], [])
        assert result["score"] == 100
        assert result["category"] == "excellent"

    def test_critical_findings_reduce_score(self):
        findings = [
            {"severity": "critical", "category": "risk"},
            {"severity": "critical", "category": "risk"},
        ]
        result = _pass4_compute_score(findings, [])
        assert result["score"] == 100 - 30  # 2 * 15
        assert result["category"] == "bon"

    def test_critical_cap_at_45(self):
        findings = [{"severity": "critical"} for _ in range(5)]
        result = _pass4_compute_score(findings, [])
        # 5 * 15 = 75 but capped at 45
        assert result["score"] == 100 - 45
        assert result["breakdown"]["critical_risks"] == -45

    def test_major_findings(self):
        findings = [{"severity": "major"} for _ in range(3)]
        result = _pass4_compute_score(findings, [])
        assert result["score"] == 100 - 24  # 3 * 8
        assert result["breakdown"]["major_risks"] == -24

    def test_minor_findings(self):
        findings = [{"severity": "minor"} for _ in range(4)]
        result = _pass4_compute_score(findings, [])
        assert result["score"] == 100 - 12  # 4 * 3
        assert result["breakdown"]["minor_risks"] == -12

    def test_mandatory_missing_clauses(self):
        missing = [{"importance": "mandatory"} for _ in range(3)]
        result = _pass4_compute_score([], missing)
        assert result["score"] == 100 - 30  # 3 * 10
        assert result["breakdown"]["missing_mandatory"] == -30

    def test_recommended_missing_clauses(self):
        missing = [{"importance": "recommended"} for _ in range(3)]
        result = _pass4_compute_score([], missing)
        assert result["score"] == 100 - 9  # 3 * 3
        assert result["breakdown"]["missing_recommended"] == -9

    def test_combined_score_critique(self):
        findings = [
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "major"},
            {"severity": "major"},
            {"severity": "major"},
            {"severity": "major"},
        ]
        missing = [
            {"importance": "mandatory"},
            {"importance": "mandatory"},
        ]
        result = _pass4_compute_score(findings, missing)
        # critical: 3*15=45, major: 4*8=32, mandatory: 2*10=20
        # total = 45 + 32 + 20 = 97 → score = max(0, 3) = 3
        assert result["score"] == 3
        assert result["category"] == "critique"

    def test_score_never_below_zero(self):
        findings = [{"severity": "critical"} for _ in range(10)]
        missing = [{"importance": "mandatory"} for _ in range(10)]
        result = _pass4_compute_score(findings, missing)
        assert result["score"] >= 0

    def test_attention_category(self):
        findings = [
            {"severity": "critical"},
            {"severity": "major"},
            {"severity": "major"},
            {"severity": "major"},
        ]
        result = _pass4_compute_score(findings, [])
        # critical: 15, major: 3*8=24 → total 39 → score 61
        assert result["score"] == 61
        assert result["category"] == "attention"


# ─────────────────────────────────────────────────────────────
# _scoped_query
# ─────────────────────────────────────────────────────────────


class TestScopedQuery:
    def test_without_org(self):
        q = _scoped_query({"document_id": "doc1"})
        assert q == {"document_id": "doc1"}
        assert "organization_id" not in q

    def test_with_org(self):
        q = _scoped_query({"document_id": "doc1"}, "org-x")
        assert q == {"document_id": "doc1", "organization_id": "org-x"}


# ─────────────────────────────────────────────────────────────
# _analysis_to_dict
# ─────────────────────────────────────────────────────────────


class TestAnalysisToDict:
    def test_serialization(self):
        now = datetime.now(timezone.utc)
        doc = {
            "id": "a1",
            "document_id": "d1",
            "organization_id": "org1",
            "status": "completed",
            "contract_type": "travail",
            "contract_type_label": "Contrat de travail",
            "language": "fr",
            "parties": ["Société X", "M. Y"],
            "summary": "Un contrat de travail.",
            "score": 75,
            "score_category": "bon",
            "score_breakdown": {"critical_risks": -15},
            "findings": [{"id": "f1", "severity": "critical"}],
            "findings_summary": {"critical": 1, "total": 1},
            "missing_clauses": [],
            "recommendations": ["Ajouter clause X"],
            "legal_sources": [],
            "total_chunks_analyzed": 10,
            "analysis_duration_ms": 30000,
            "llm_model": "qwen2.5:7b",
            "created_at": now,
            "updated_at": now,
            "error_message": None,
        }
        result = _analysis_to_dict(doc)

        assert result["id"] == "a1"
        assert result["score"] == 75
        assert result["score_category"] == "bon"
        assert len(result["parties"]) == 2
        assert result["findings"][0]["severity"] == "critical"
        assert "_id" not in result

    def test_handles_missing_fields(self):
        doc = {"id": "a2", "status": "analyzing"}
        result = _analysis_to_dict(doc)
        assert result["id"] == "a2"
        assert result["parties"] == []
        assert result["findings"] == []
        assert result["score"] is None


# ─────────────────────────────────────────────────────────────
# CONTRACT_TYPES structure
# ─────────────────────────────────────────────────────────────


class TestContractTypes:
    def test_all_types_have_required_fields(self):
        for type_key, config in CONTRACT_TYPES.items():
            assert "label_fr" in config, f"{type_key} missing label_fr"
            assert "label_ar" in config, f"{type_key} missing label_ar"
            assert "mandatory_clauses" in config, f"{type_key} missing mandatory_clauses"
            assert "recommended_clauses" in config, f"{type_key} missing recommended_clauses"
            assert "search_queries" in config, f"{type_key} missing search_queries"

    def test_travail_has_key_clauses(self):
        cfg = CONTRACT_TYPES["travail"]
        assert "remuneration" in cfg["mandatory_clauses"]
        assert "confidentialite" in cfg["recommended_clauses"]

    def test_autre_is_generic(self):
        cfg = CONTRACT_TYPES["autre"]
        assert "identite_parties" in cfg["mandatory_clauses"]
        assert "objet" in cfg["mandatory_clauses"]

    def test_clause_labels_coverage(self):
        """Chaque clause référencée a un label."""
        all_clauses = set()
        for config in CONTRACT_TYPES.values():
            all_clauses.update(config["mandatory_clauses"])
            all_clauses.update(config["recommended_clauses"])

        for clause in all_clauses:
            assert clause in CLAUSE_LABELS, f"Clause '{clause}' missing from CLAUSE_LABELS"


# ─────────────────────────────────────────────────────────────
# CRUD (with mocked MongoDB)
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_analysis_not_found(monkeypatch):
    mock_coll = MagicMock()
    mock_coll.find_one = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "app.services.contract_analysis_service._collection",
        lambda name: mock_coll,
    )

    from app.services.contract_analysis_service import get_analysis
    result = await get_analysis("nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_delete_analysis_returns_false_when_not_found(monkeypatch):
    mock_result = MagicMock()
    mock_result.deleted_count = 0
    mock_coll = MagicMock()
    mock_coll.delete_one = AsyncMock(return_value=mock_result)
    monkeypatch.setattr(
        "app.services.contract_analysis_service._collection",
        lambda name: mock_coll,
    )

    from app.services.contract_analysis_service import delete_analysis
    result = await delete_analysis("nonexistent-id")
    assert result is False


@pytest.mark.asyncio
async def test_delete_analysis_returns_true_when_found(monkeypatch):
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_coll = MagicMock()
    mock_coll.delete_one = AsyncMock(return_value=mock_result)
    monkeypatch.setattr(
        "app.services.contract_analysis_service._collection",
        lambda name: mock_coll,
    )

    from app.services.contract_analysis_service import delete_analysis
    result = await delete_analysis("existing-id")
    assert result is True
