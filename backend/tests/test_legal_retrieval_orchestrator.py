"""Unit tests for legal_retrieval_orchestrator.py."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services import legal_retrieval_orchestrator as lro


# ─────────────────────────────────────────────────────────────
# Helper: fake search function that tags chunks by partition filter
# ─────────────────────────────────────────────────────────────

async def _fake_search(q, top_k=10, extra_filter=None):
    """Return chunks that encode the filter so tests can inspect partition source."""
    is_base = (extra_filter or {}).get("is_base_version")
    if is_base is True:
        tag = "base"
    elif isinstance(is_base, dict) and is_base.get("$ne") is True:
        tag = "amendment"
    elif (extra_filter or {}).get("type") == "exigence":
        tag = "exigence"
    elif (extra_filter or {}).get("type") == "action":
        tag = "action"
    else:
        tag = "unfiltered"
    return [{"_id": f"{tag}_{i}", "text": f"{tag} chunk {i}", "score": 0.9 - i * 0.1}
            for i in range(min(top_k, 3))]


# ─────────────────────────────────────────────────────────────
# Keyword classifier
# ─────────────────────────────────────────────────────────────

class TestClassifyLegalIntent:
    def test_current_rule_fr(self):
        assert lro.classify_legal_intent("Que dit la loi sur le travail ?", "fr") == "current_rule_query"

    def test_current_rule_en(self):
        assert lro.classify_legal_intent("What does the law say about overtime?", "en") == "current_rule_query"

    def test_change_tracking_fr(self):
        assert lro.classify_legal_intent("Quel est l'historique des amendements ?", "fr") == "change_tracking_query"

    def test_change_tracking_en(self):
        assert lro.classify_legal_intent("What changed in the amendment?", "en") == "change_tracking_query"

    def test_impact_fr(self):
        assert lro.classify_legal_intent("Quel est l'impact sur la conformité de mon entreprise ?", "fr") == "impact_query"

    def test_impact_en(self):
        assert lro.classify_legal_intent("What is the compliance impact on my company profile?", "en") == "impact_query"

    def test_fallback_to_current_rule(self):
        assert lro.classify_legal_intent("Bonjour", "fr") == "current_rule_query"

    def test_arabic_change_tracking(self):
        assert lro.classify_legal_intent("ما هو تاريخ تعديل هذا الفصل؟", "ar") == "change_tracking_query"


# ─────────────────────────────────────────────────────────────
# Intent-to-mix mapping (original + spec aliases)
# ─────────────────────────────────────────────────────────────

class TestIntentToMix:
    @pytest.mark.asyncio
    async def test_compliance_base_weighted(self):
        mix = await lro.intent_to_mix("compliance_audit")
        weights = {m.source: m.weight for m in mix}
        assert weights["base"] == pytest.approx(0.40)
        assert weights["amendment"] == pytest.approx(0.40)

    @pytest.mark.asyncio
    async def test_amendment_heavy(self):
        mix = await lro.intent_to_mix("amendment")
        weights = {m.source: m.weight for m in mix}
        assert weights["amendment"] == pytest.approx(0.70)
        assert weights["base"] == pytest.approx(0.30)

    @pytest.mark.asyncio
    async def test_default_balanced(self):
        mix = await lro.intent_to_mix("unknown")
        weights = {m.source: m.weight for m in mix}
        assert weights["amendment"] == pytest.approx(0.70)
        assert weights["base"] == pytest.approx(0.30)

    @pytest.mark.asyncio
    async def test_current_rule_query_alias(self):
        mix = await lro.intent_to_mix("current_rule_query")
        weights = {m.source: m.weight for m in mix}
        # current_rule_query → current_state → amendment 0.70, base 0.30
        assert weights["amendment"] == pytest.approx(0.70)
        assert weights["base"] == pytest.approx(0.30)

    @pytest.mark.asyncio
    async def test_change_tracking_query_alias(self):
        mix = await lro.intent_to_mix("change_tracking_query")
        weights = {m.source: m.weight for m in mix}
        # change_tracking_query → historical → base 0.85, amendment 0.15
        assert weights["base"] == pytest.approx(0.85)
        assert weights["amendment"] == pytest.approx(0.15)

    @pytest.mark.asyncio
    async def test_impact_query_alias(self):
        mix = await lro.intent_to_mix("impact_query")
        sources = {m.source for m in mix}
        # impact_query → compliance_audit → base, amendment, exigence, action
        assert sources == {"base", "amendment", "exigence", "action"}


# ─────────────────────────────────────────────────────────────
# Formal retriever strategy classes
# ─────────────────────────────────────────────────────────────

class TestRetrieverStrategies:
    def test_protocol_conformance(self):
        assert isinstance(lro.BaseLawRetriever(), lro.RetrieverStrategy)
        assert isinstance(lro.AmendmentRetriever(), lro.RetrieverStrategy)
        assert isinstance(lro.HybridRetriever(), lro.RetrieverStrategy)

    @pytest.mark.asyncio
    async def test_base_law_retriever(self):
        ret = lro.BaseLawRetriever()
        chunks = await ret.retrieve("question", _fake_search, db=None, top_k=3)
        assert len(chunks) == 3
        assert all(c["_partition_source"] == "base" for c in chunks)

    @pytest.mark.asyncio
    async def test_amendment_retriever(self):
        ret = lro.AmendmentRetriever()
        chunks = await ret.retrieve("question", _fake_search, db=None, top_k=3)
        assert len(chunks) == 3
        assert all(c["_partition_source"] == "amendment" for c in chunks)

    @pytest.mark.asyncio
    async def test_hybrid_retriever_mixes_both(self):
        ret = lro.HybridRetriever(base_weight=0.60, amendment_weight=0.40)
        chunks = await ret.retrieve("question", _fake_search, db=None, top_k=6)
        sources = {c["_partition_source"] for c in chunks}
        assert "base" in sources
        assert "amendment" in sources
        # Weight values should be stamped
        base_chunks = [c for c in chunks if c["_partition_source"] == "base"]
        amend_chunks = [c for c in chunks if c["_partition_source"] == "amendment"]
        assert all(c["_partition_weight"] == 0.60 for c in base_chunks)
        assert all(c["_partition_weight"] == 0.40 for c in amend_chunks)

    @pytest.mark.asyncio
    async def test_base_law_retriever_handles_search_failure(self):
        async def failing_search(q, top_k=10, extra_filter=None):
            raise ConnectionError("DB down")
        ret = lro.BaseLawRetriever()
        chunks = await ret.retrieve("q", failing_search, db=None)
        assert chunks == []


# ─────────────────────────────────────────────────────────────
# Retrieve partitioned — merge & weighted rerank
# ─────────────────────────────────────────────────────────────

class TestRetrievePartitioned:
    @pytest.mark.asyncio
    async def test_merges_both_partitions(self):
        result = await lro.retrieve_partitioned(
            question="q", intent="compliance_audit",
            search_fn=_fake_search, db=None, domain_config=None,
        )
        assert len(result) >= 1
        sources = {c.get("_partition_source") for c in result}
        assert "base" in sources or "amendment" in sources

    @pytest.mark.asyncio
    async def test_weighted_merge_scores_present(self):
        result = await lro.retrieve_partitioned(
            question="q", intent="compare",
            search_fn=_fake_search, db=None, domain_config=None,
        )
        assert all("_merge_score" in c for c in result)
        # Results should be sorted descending by _merge_score
        scores = [c["_merge_score"] for c in result]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_deduplication(self):
        call_count = 0
        async def dedup_search(q, top_k=10, extra_filter=None):
            nonlocal call_count
            call_count += 1
            # Return same _id from both partitions
            return [{"_id": "shared_1", "text": "same", "score": 0.8}]
        result = await lro.retrieve_partitioned(
            question="q", intent="compare",
            search_fn=dedup_search, db=None, domain_config=None,
        )
        ids = [c["_id"] for c in result]
        assert ids.count("shared_1") == 1  # deduplicated


# ─────────────────────────────────────────────────────────────
# Spec scenario tests
# ─────────────────────────────────────────────────────────────

class TestCurrentRuleQuestion:
    """Scenario: user asks about the current applicable law."""
    @pytest.mark.asyncio
    async def test_current_rule_retrieval(self):
        intent = lro.classify_legal_intent("Que dit la loi applicable en vigueur ?", "fr")
        assert intent == "current_rule_query"
        mix = await lro.intent_to_mix(intent)
        weights = {m.source: m.weight for m in mix}
        # current_state: amendment-heavy (latest consolidated text)
        assert weights["amendment"] > weights["base"]

    @pytest.mark.asyncio
    async def test_current_rule_end_to_end(self):
        intent = lro.classify_legal_intent("What does the law say about dismissal?", "en")
        result = await lro.retrieve_partitioned(
            question="dismissal", intent=intent,
            search_fn=_fake_search, db=None, domain_config=None,
        )
        assert len(result) >= 1


class TestChangeTrackingQuestion:
    """Scenario: user asks about amendment history or what changed."""
    @pytest.mark.asyncio
    async def test_change_tracking_retrieval(self):
        intent = lro.classify_legal_intent("Quel amendement a modifié cet article ?", "fr")
        assert intent == "change_tracking_query"
        mix = await lro.intent_to_mix(intent)
        weights = {m.source: m.weight for m in mix}
        # historical: base-heavy (original text for comparison)
        assert weights["base"] > weights["amendment"]
        assert weights["base"] == pytest.approx(0.85)

    @pytest.mark.asyncio
    async def test_change_tracking_end_to_end(self):
        intent = lro.classify_legal_intent("What changed in the last amendment?", "en")
        result = await lro.retrieve_partitioned(
            question="amendment changes", intent=intent,
            search_fn=_fake_search, db=None, domain_config=None,
        )
        sources = {c.get("_partition_source") for c in result}
        assert "base" in sources


class TestImpactQuestionCompanyProfile:
    """Scenario: user asks about impact/compliance for their company."""
    @pytest.mark.asyncio
    async def test_impact_classification(self):
        intent = lro.classify_legal_intent(
            "Quel est l'impact de cette loi sur la conformité de mon entreprise ?", "fr",
        )
        assert intent == "impact_query"

    @pytest.mark.asyncio
    async def test_impact_retrieval_includes_exigences_actions(self):
        intent = lro.classify_legal_intent(
            "What is the compliance impact on my company profile?", "en",
        )
        assert intent == "impact_query"
        mix = await lro.intent_to_mix(intent)
        sources = {m.source for m in mix}
        # impact_query → compliance_audit → includes exigence + action partitions
        assert "exigence" in sources
        assert "action" in sources
        assert "base" in sources
        assert "amendment" in sources

    @pytest.mark.asyncio
    async def test_impact_end_to_end(self):
        intent = lro.classify_legal_intent(
            "Quel risque de conformité pour ma société ?", "fr",
        )
        assert intent == "impact_query"
        result = await lro.retrieve_partitioned(
            question="conformité société", intent=intent,
            search_fn=_fake_search, db=None, domain_config=None,
        )
        sources = {c.get("_partition_source") for c in result}
        assert len(sources) >= 2  # at least base + amendment (exigence/action too if chunks returned)


# ─────────────────────────────────────────────────────────────
# Article text helpers
# ─────────────────────────────────────────────────────────────

class TestArticleHelpers:
    @pytest.mark.asyncio
    async def test_get_current_article_text(self):
        coll = AsyncMock()
        coll.find_one = AsyncMock(return_value={"_id": "v1", "text": "version active"})
        db = MagicMock()
        db.__getitem__ = MagicMock(return_value=coll)
        txt = await lro.get_current_article_text(db, "a1")
        assert txt == "version active"

    @pytest.mark.asyncio
    async def test_get_base_article_text(self):
        coll = AsyncMock()
        coll.find_one = AsyncMock(return_value={"text": "Base version text"})
        db = MagicMock()
        db.__getitem__ = MagicMock(return_value=coll)
        txt = await lro.get_base_article_text(db, "a1")
        assert "Base" in txt

    @pytest.mark.asyncio
    async def test_get_current_article_text_not_found(self):
        coll = AsyncMock()
        coll.find_one = AsyncMock(return_value=None)
        db = MagicMock()
        db.__getitem__ = MagicMock(return_value=coll)
        txt = await lro.get_current_article_text(db, "missing")
        assert txt is None
