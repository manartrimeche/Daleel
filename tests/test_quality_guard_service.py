"""Unit tests for quality_guard_service.py."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.services import quality_guard_service as qg


class TestExtractRefs:
    def test_extracts_article_refs(self):
        text = "Selon l'article 12 du code du travail..."
        refs = qg._extract_refs(text)
        assert "12" in refs

    def test_extracts_loi_refs(self):
        text = "Loi 2004-63 relative aux données personnelles"
        refs = qg._extract_refs(text)
        assert "2004-63" in refs


class TestAuditReferences:
    def test_pass_when_all_refs_supported(self):
        chunks = [{"text": "Article 12 : le salarié a droit...", "metadata": {}}]
        result = qg.audit_references("Selon l'article 12...", chunks)
        assert result["passed"] is True
        assert result["unsupported_refs"] == set()

    def test_fail_on_unsupported_refs(self):
        chunks = [{"text": "Article 12 : le salarié a droit...", "metadata": {}}]
        result = qg.audit_references("Selon l'article 12 et l'article 99...", chunks)
        assert result["passed"] is False
        assert "99" in result["unsupported_refs"]
        assert "article 99" not in result["clean_answer"].lower()

    def test_empty_chunks_pass(self):
        result = qg.audit_references("reponse sans référence.", [])
        assert result["passed"] is True


class TestIsLanguageCompliant:
    def test_french_compliance(self):
        assert qg.is_language_compliant("Ceci est une reponse en français.", "fr") is True

    def test_arabic_compliance(self):
        assert qg.is_language_compliant("هذا نص بالعربية.", "ar") is True


class TestSemanticFidelityCheck:
    @pytest.mark.asyncio
    async def test_mock_llm_returns_supported(self):
        with patch(
            "app.services.llm_service._call_ollama",
            new_callable=AsyncMock,
            return_value='{"supported": true, "confidence": 0.95, "issues": []}',
        ):
            result = await qg._semantic_fidelity_check("answer", [{"text": "ctx"}], "fr")
            assert result["supported"] is True
            assert result["confidence"] == pytest.approx(0.95)

    @pytest.mark.asyncio
    async def test_returns_safe_default_on_llm_failure(self):
        with patch(
            "app.services.llm_service._call_ollama",
            new_callable=AsyncMock,
            side_effect=RuntimeError("timeout"),
        ):
            result = await qg._semantic_fidelity_check("answer", [{"text": "ctx"}], "fr")
            assert result["supported"] is True
            assert result["confidence"] == pytest.approx(1.0)


class TestConservativeRewrite:
    @pytest.mark.asyncio
    async def test_returns_rewritten_on_success(self):
        with patch(
            "app.services.llm_service._call_ollama",
            new_callable=AsyncMock,
            return_value="reponse ultra-conservative.",
        ):
            result = await qg.conservative_rewrite(
                "question", [{"text": "ctx"}], "fr", "bad answer", ["issue"]
            )
            assert "ultra-conservative" in result

    @pytest.mark.asyncio
    async def test_returns_previous_answer_on_failure(self):
        with patch(
            "app.services.llm_service._call_ollama",
            new_callable=AsyncMock,
            side_effect=RuntimeError("timeout"),
        ):
            result = await qg.conservative_rewrite(
                "question", [{"text": "ctx"}], "fr", "fallback", ["issue"]
            )
            assert result == "fallback"


class TestAuditAndGuard:
    @pytest.mark.asyncio
    async def test_accept_clean_answer(self):
        with patch(
            "app.services.llm_service._call_ollama",
            new_callable=AsyncMock,
            return_value='{"supported": true, "confidence": 0.95, "issues": []}',
        ):
            result = await qg.audit_and_guard(
                "q", "Ceci est une reponse en français complète et détaillée pour le test.", [{"text": "ctx"}], "fr", enabled=True
            )
            assert result["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_rewrite_when_multiple_issues(self):
        chunks = [{"text": "Article 1 : texte.", "metadata": {}}]
        with patch(
            "app.services.llm_service._call_ollama",
            new_callable=AsyncMock,
            return_value='{"supported": false, "confidence": 0.2, "issues": ["hallucination"]}',
        ):
            result = await qg.audit_and_guard(
                "q", "Selon l'article 99 ceci est faux.", chunks, "fr", enabled=True
            )
            # Two issues: unsupported ref + semantic unsupported
            assert result["status"] in ("rewritten", "flagged")
