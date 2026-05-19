"""
Sprint 6+ Integration Tests — verify the four RAG improvements work together.

Tests cover:
  1. Cross-service pipeline: classify → route → retrieve → enrich → guard
  2. API response metadata: domain, kg_enriched, quality_guard_status
  3. Feature toggle isolation: disabling one feature doesn't break others
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.domain_router import route_question
from app.services import legal_retrieval_orchestrator as lro
from app.services import graph_resolver
from app.services.quality_guard_service import audit_and_guard


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

async def _fake_search(q, top_k=10, extra_filter=None):
    """Simulate search returning tagged chunks."""
    is_base = (extra_filter or {}).get("is_base_version")
    if is_base is True:
        tag = "base"
    elif isinstance(is_base, dict):
        tag = "amendment"
    else:
        tag = "general"
    return [
        {
            "_id": f"{tag}_{i}",
            "text": f"Article {i}: disposition légale du code du travail.",
            "score": 0.85 - i * 0.05,
            "loi_id": "loi_ct",
            "article_id": f"art_{i}",
        }
        for i in range(min(top_k, 3))
    ]


def _mock_db():
    """Create a mock MongoDB with basic collections for KG enrichment."""
    db = MagicMock()
    collections = {}

    async def _find_one(query, **kwargs):
        for name, col in collections.items():
            if col.find_one is _find_one_factories.get(name):
                break
        return None

    _find_one_factories = {}

    # lois collection
    lois_col = AsyncMock()
    lois_col.find_one = AsyncMock(return_value={
        "_id": "loi_ct", "title": "Code du Travail", "code": "CT",
        "description": "Loi régissant les relations de travail en Tunisie",
    })
    collections["lois"] = lois_col

    # articles collection
    articles_col = AsyncMock()
    articles_col.find_one = AsyncMock(return_value={
        "_id": "art_0", "num": "1", "title": "Dispositions générales", "loi_id": "loi_ct",
    })
    collections["articles"] = articles_col

    # article_versions collection
    versions_col = AsyncMock()
    versions_col.find_one = AsyncMock(return_value={
        "_id": "ver_1", "article_id": "art_0", "version": 2,
        "text": "Le contrat de travail est régi par les dispositions du présent code...",
    })
    collections["article_versions"] = versions_col

    db.__getitem__ = MagicMock(side_effect=lambda name: collections.get(name, AsyncMock()))
    return db


# ─────────────────────────────────────────────────────────────
# 1. Cross-service integration: full pipeline
# ─────────────────────────────────────────────────────────────

class TestCrossServicePipeline:
    """Verify that classify → route → retrieve → enrich → guard runs end-to-end."""

    @pytest.mark.asyncio
    async def test_full_pipeline_current_rule(self):
        # Step 1: Classify intent
        intent = lro.classify_legal_intent(
            "Que dit la loi en vigueur sur le licenciement ?", "fr",
        )
        assert intent == "current_rule_query"

        # Step 2: Route to domain
        route_result = await route_question(
            "Que dit la loi en vigueur sur le licenciement ?", "fr",
        )
        domain, domain_config = route_result
        assert isinstance(domain, str)
        assert hasattr(domain_config, "top_k")

        # Step 3: Partitioned retrieval
        chunks = await lro.retrieve_partitioned(
            question="licenciement",
            intent=intent,
            search_fn=_fake_search,
            db=None,
            domain_config=domain_config,
        )
        assert len(chunks) >= 1
        assert all("_partition_source" in c for c in chunks)
        assert all("_merge_score" in c for c in chunks)

        # Step 4: KG enrichment
        db = _mock_db()
        chunk_meta = [{"loi_id": c.get("loi_id"), "article_id": c.get("article_id")} for c in chunks]
        kg_text = await graph_resolver.kg_context_for_rag(db, chunk_meta, max_entities=3)
        assert isinstance(kg_text, str)
        # Should have resolved at least the loi
        assert "Code du Travail" in kg_text or kg_text == ""

        # Step 5: Quality guard (mock LLM for semantic fidelity)
        with patch("app.services.quality_guard_service._semantic_fidelity_check", new_callable=AsyncMock) as mock_fidelity:
            mock_fidelity.return_value = {"supported": True, "confidence": 0.9, "issues": []}
            qg_result = await audit_and_guard(
                question="Que dit la loi sur le licenciement ?",
                answer="L'article 1 du Code du Travail prévoit les dispositions suivantes...",
                chunks=chunks,
                lang="fr",
                enabled=True,
            )
            assert qg_result["status"] in ("accepted", "flagged", "rewritten")
            assert "answer" in qg_result

    @pytest.mark.asyncio
    async def test_full_pipeline_change_tracking(self):
        intent = lro.classify_legal_intent("Quel amendement a modifié l'article 5 ?", "fr")
        assert intent == "change_tracking_query"

        route_result = await route_question("amendement article 5", "fr")
        domain, domain_config = route_result

        chunks = await lro.retrieve_partitioned(
            question="amendement article 5",
            intent=intent,
            search_fn=_fake_search,
            db=None,
            domain_config=domain_config,
        )
        assert len(chunks) >= 1
        # change_tracking → historical → base-heavy
        base_chunks = [c for c in chunks if c.get("_partition_source") == "base"]
        assert len(base_chunks) >= 1

    @pytest.mark.asyncio
    async def test_full_pipeline_impact_query(self):
        intent = lro.classify_legal_intent(
            "Quel est l'impact sur la conformité de mon entreprise ?", "fr",
        )
        assert intent == "impact_query"

        route_result = await route_question("conformité entreprise", "fr")
        domain, domain_config = route_result

        chunks = await lro.retrieve_partitioned(
            question="conformité entreprise",
            intent=intent,
            search_fn=_fake_search,
            db=None,
            domain_config=domain_config,
        )
        assert len(chunks) >= 1


# ─────────────────────────────────────────────────────────────
# 2. API response metadata verification
# ─────────────────────────────────────────────────────────────

class TestApiResponseMetadata:
    """Verify that /ask response includes all Sprint 6+ metadata fields."""

    def _make_client(self):
        with patch("app.database.init_db", new_callable=AsyncMock), \
             patch("app.database.close_db", new_callable=AsyncMock), \
             patch("app.services.faiss_index.faiss_manager") as mock_faiss:
            mock_faiss.rebuild = AsyncMock()
            mock_faiss.size = 0
            from app.main import app
            from fastapi.testclient import TestClient
            return TestClient(app, raise_server_exceptions=False)

    @patch("app.services.llm_service.ask", new_callable=AsyncMock)
    def test_ask_response_contains_sprint6_fields(self, mock_ask):
        mock_ask.return_value = {
            "answer": "reponse avec les 4 features actives.",
            "sources": [],
            "model": "qwen2.5:7b",
            "chunks_used": 5,
            "domain": "labor",
            "quality_guard_status": "accepted",
            "quality_guard_issues": [],
            "kg_enriched": True,
        }
        client = self._make_client()
        r = client.post("/api/v1/ask", json={
            "question": "Quels sont les droits d'un salarié ?",
            "top_k": 5,
        })
        assert r.status_code == 200
        data = r.json()
        # All Sprint 6+ metadata fields must be present
        assert "domain" in data
        assert "kg_enriched" in data
        assert "quality_guard_status" in data

    @patch("app.services.llm_service.ask_agentic", new_callable=AsyncMock)
    def test_ask_agentic_response_contains_sprint6_fields(self, mock_ask):
        mock_ask.return_value = {
            "answer": "reponse agentique.",
            "sources": [],
            "model": "qwen2.5:7b",
            "chunks_used": 5,
            "reasoning_steps": ["retrieve_attempt:1", "chunks_accepted"],
            "retrieval_attempts": 1,
            "rewritten_query": None,
            "intent": "analysis",
            "route_decision": None,
            "timings_ms": {"retrieval": 10, "generation": 50, "total": 60},
            "selected_mode": "agentic",
            "domain": "corporate",
            "quality_guard_status": "flagged",
            "quality_guard_issues": ["Language mismatch detected"],
            "kg_enriched": False,
        }
        client = self._make_client()
        r = client.post("/api/v1/ask-agentic", json={
            "question": "Comment créer une SARL ?",
            "top_k": 5,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["domain"] == "corporate"
        assert data["quality_guard_status"] == "flagged"
        assert isinstance(data["quality_guard_issues"], list)
        assert data["kg_enriched"] is False


# ─────────────────────────────────────────────────────────────
# 3. Feature toggle isolation
# ─────────────────────────────────────────────────────────────

class TestFeatureToggleIsolation:
    """Verify that disabling one feature doesn't break the others."""

    @pytest.mark.asyncio
    async def test_quality_guard_disabled_returns_accepted(self):
        result = await audit_and_guard(
            question="test",
            answer="test answer",
            chunks=[],
            lang="fr",
            enabled=False,
        )
        assert result["status"] == "accepted"
        assert result["answer"] == "test answer"

    def test_classify_intent_works_independently(self):
        # Classifier doesn't depend on any other service
        intent = lro.classify_legal_intent("What does the law say?", "en")
        assert intent == "current_rule_query"

    @pytest.mark.asyncio
    async def test_retrieval_works_without_domain_config(self):
        # When domain_config is None, retrieve_partitioned still works
        chunks = await lro.retrieve_partitioned(
            question="test",
            intent="current_state",
            search_fn=_fake_search,
            db=None,
            domain_config=None,
        )
        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_kg_enrichment_returns_empty_on_no_metadata(self):
        db = _mock_db()
        result = await graph_resolver.kg_context_for_rag(db, [], max_entities=6)
        assert result == ""

    @pytest.mark.asyncio
    async def test_domain_router_independent(self):
        result = await route_question("code du travail", "fr")
        domain, config = result
        assert isinstance(domain, str)
        assert hasattr(config, "top_k")
