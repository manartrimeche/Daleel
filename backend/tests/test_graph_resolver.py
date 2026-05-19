"""Unit tests for graph_resolver.py."""
import pytest
from unittest.mock import AsyncMock
from app.services import graph_resolver as gr


class _MockCursor:
    def __init__(self, data):
        self._data = data or []
        self._idx = 0

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n):
        return self

    def __aiter__(self):
        self._idx = 0
        return self

    async def __anext__(self):
        if self._idx >= len(self._data):
            raise StopAsyncIteration
        item = self._data[self._idx]
        self._idx += 1
        return item


def _make_find(data):
    def _find(*args, **kwargs):
        return _MockCursor(data)
    return _find


def _mock_db(loi=None, articles=None, versions=None, exigences=None,
             actions=None, criticalities=None, dependencies=None, amendments=None,
             company_profiles=None, applicabilities=None):
    db = {}
    for name, data in [
        ("lois", loi), ("articles", articles), ("article_versions", versions),
        ("exigences", exigences), ("actions", actions),
        ("action_criticalities", criticalities), ("action_dependencies", dependencies),
        ("amendment_operations", amendments),
        ("company_profiles", company_profiles),
        ("exigence_applicabilities", applicabilities),
    ]:
        coll = AsyncMock()
        coll.find = _make_find(data)
        coll.find_one = AsyncMock(return_value=(data[0] if data else None))
        db[name] = coll
    return db


# ─────────────────────────────────────────────────────────────
# Existing tests (kept as-is)
# ─────────────────────────────────────────────────────────────

class TestResolveLoiContext:
    @pytest.mark.asyncio
    async def test_empty_when_no_code(self):
        db = _mock_db()
        result = await gr.resolve_loi_context(db, loi_id=None, loi_code=None)
        assert result["loi"] is None

    @pytest.mark.asyncio
    async def test_resolves_loi(self):
        db = _mock_db(loi=[{"_id": "l1", "code": "CT", "title": "Travail"}],
                      articles=[{"_id": "a1", "loi_id": "l1", "num": "1"}])
        db["lois"].find_one = AsyncMock(return_value={"_id": "l1", "code": "CT"})
        result = await gr.resolve_loi_context(db, loi_code="CT")
        assert result["loi"]["code"] == "CT"
        assert result["stats"]["article_count"] == 1


class TestResolveEntityNeighbors:
    @pytest.mark.asyncio
    async def test_unsupported_entity(self):
        db = _mock_db()
        result = await gr.resolve_entity_neighbors(db, "bad", "x")
        assert result["center"] is None


class TestKgContextForRag:
    @pytest.mark.asyncio
    async def test_empty_when_no_meta(self):
        db = _mock_db()
        text = await gr.kg_context_for_rag(db, [])
        assert text == ""


# ─────────────────────────────────────────────────────────────
# Deep-traversal tests — article → exigences → actions
# ─────────────────────────────────────────────────────────────

class TestArticleToExigences:
    @pytest.mark.asyncio
    async def test_article_graph_includes_exigences(self):
        db = _mock_db(
            articles=[{"_id": "a1", "loi_id": "l1", "num": "12"}],
            loi=[{"_id": "l1", "code": "CT", "title": "Travail"}],
            exigences=[{"_id": "ex1", "article_id": "a1", "title": "Déclaration obligatoire"}],
        )
        db["articles"].find_one = AsyncMock(return_value={"_id": "a1", "loi_id": "l1", "num": "12"})
        db["lois"].find_one = AsyncMock(return_value={"_id": "l1", "code": "CT", "title": "Travail"})

        result = await gr.resolve_article_graph(db, "a1")
        assert isinstance(result, gr.ArticleSubgraph)
        assert result.article.entity_id == "a1"
        assert len(result.exigences) == 1
        assert result.exigences[0].entity_id == "ex1"
        assert result.loi is not None
        assert result.loi.entity_id == "l1"

    @pytest.mark.asyncio
    async def test_article_graph_not_found(self):
        db = _mock_db()
        db["articles"].find_one = AsyncMock(return_value=None)
        result = await gr.resolve_article_graph(db, "missing")
        assert result.article.label == "not found"
        assert result.exigences == []


class TestExigenceToActions:
    @pytest.mark.asyncio
    async def test_actions_resolved_from_exigences(self):
        db = _mock_db(
            articles=[{"_id": "a1", "loi_id": "l1", "num": "5"}],
            loi=[{"_id": "l1", "code": "CS", "title": "Sociétés"}],
            exigences=[{"_id": "ex1", "article_id": "a1", "title": "Obligation de conformité"}],
            actions=[{"_id": "act1", "exigence_id": "ex1", "title": "Obtenir agrément"}],
        )
        db["articles"].find_one = AsyncMock(return_value={"_id": "a1", "loi_id": "l1", "num": "5"})
        db["lois"].find_one = AsyncMock(return_value={"_id": "l1", "code": "CS", "title": "Sociétés"})

        result = await gr.resolve_article_graph(db, "a1")
        assert len(result.actions) == 1
        assert result.actions[0].entity_id == "act1"
        # Edge exigence → action must exist
        action_edges = [e for e in result.edges if e.relation == "requires_action"]
        assert len(action_edges) == 1
        assert action_edges[0].source_id == "ex1"
        assert action_edges[0].target_id == "act1"


# ─────────────────────────────────────────────────────────────
# Deep-traversal tests — action → criticality / dependencies
# ─────────────────────────────────────────────────────────────

class TestActionCriticalityAndDependencies:
    @pytest.mark.asyncio
    async def test_criticality_attached_to_action(self):
        db = _mock_db(
            articles=[{"_id": "a1", "loi_id": "l1", "num": "10"}],
            loi=[{"_id": "l1", "code": "CT", "title": "Travail"}],
            exigences=[{"_id": "ex1", "article_id": "a1", "title": "Sécurité"}],
            actions=[{"_id": "act1", "exigence_id": "ex1", "title": "Former personnel"}],
            criticalities=[{"_id": "c1", "action_id": "act1", "score": 8.5, "level": "high"}],
        )
        db["articles"].find_one = AsyncMock(return_value={"_id": "a1", "loi_id": "l1", "num": "10"})
        db["lois"].find_one = AsyncMock(return_value={"_id": "l1", "code": "CT", "title": "Travail"})
        db["action_criticalities"].find_one = AsyncMock(
            return_value={"_id": "c1", "action_id": "act1", "score": 8.5, "level": "high"},
        )

        result = await gr.resolve_article_graph(db, "a1")
        assert len(result.criticalities) == 1
        assert result.criticalities[0].action_id == "act1"
        assert result.criticalities[0].score == 8.5
        assert result.criticalities[0].level == "high"

    @pytest.mark.asyncio
    async def test_dependencies_between_actions(self):
        db = _mock_db(
            articles=[{"_id": "a1", "loi_id": "l1", "num": "10"}],
            loi=[{"_id": "l1", "code": "CT", "title": "Travail"}],
            exigences=[{"_id": "ex1", "article_id": "a1", "title": "Sécurité"}],
            actions=[
                {"_id": "act1", "exigence_id": "ex1", "title": "Former personnel"},
                {"_id": "act2", "exigence_id": "ex1", "title": "Acheter EPI"},
            ],
            dependencies=[{
                "_id": "d1", "source_action_id": "act1",
                "target_action_id": "act2", "type": "prerequisite",
            }],
        )
        db["articles"].find_one = AsyncMock(return_value={"_id": "a1", "loi_id": "l1", "num": "10"})
        db["lois"].find_one = AsyncMock(return_value={"_id": "l1", "code": "CT", "title": "Travail"})
        db["action_criticalities"].find_one = AsyncMock(return_value=None)

        result = await gr.resolve_article_graph(db, "a1")
        assert len(result.dependencies) == 1
        assert result.dependencies[0].source_action_id == "act1"
        assert result.dependencies[0].target_action_id == "act2"
        assert result.dependencies[0].dependency_type == "prerequisite"


# ─────────────────────────────────────────────────────────────
# Amendment history — with version link
# ─────────────────────────────────────────────────────────────

class TestAmendmentHistory:
    @pytest.mark.asyncio
    async def test_amendments_on_article_graph(self):
        db = _mock_db(
            articles=[{"_id": "a1", "loi_id": "l1", "num": "3"}],
            loi=[{"_id": "l1", "code": "CS", "title": "Sociétés"}],
            amendments=[{
                "_id": "am1", "operation": "MODIFY", "loi_id": "l1",
                "article_id": "a1", "version_id": "v2", "created_at": "2025-01-01",
            }],
        )
        db["articles"].find_one = AsyncMock(return_value={"_id": "a1", "loi_id": "l1", "num": "3"})
        db["lois"].find_one = AsyncMock(return_value={"_id": "l1", "code": "CS", "title": "Sociétés"})
        db["action_criticalities"].find_one = AsyncMock(return_value=None)

        result = await gr.resolve_article_graph(db, "a1")
        assert len(result.amendments) == 1
        assert result.amendments[0].operation == "MODIFY"
        assert result.amendments[0].version_id == "v2"
        assert result.amendments[0].article_id == "a1"

    @pytest.mark.asyncio
    async def test_version_graph_fetches_amendments(self):
        db = _mock_db(
            versions=[{"_id": "v1", "article_id": "a1", "version": 2, "text": "Texte modifié"}],
            articles=[{"_id": "a1", "loi_id": "l1", "num": "7"}],
            loi=[{"_id": "l1", "code": "CT", "title": "Travail"}],
            amendments=[{
                "_id": "am1", "operation": "REPLACE", "loi_id": "l1",
                "article_id": "a1", "version_id": "v1", "created_at": "2024-06-01",
            }],
        )
        db["article_versions"].find_one = AsyncMock(
            return_value={"_id": "v1", "article_id": "a1", "version": 2, "text": "Texte modifié"},
        )
        db["articles"].find_one = AsyncMock(return_value={"_id": "a1", "loi_id": "l1", "num": "7"})
        db["lois"].find_one = AsyncMock(return_value={"_id": "l1", "code": "CT", "title": "Travail"})

        result = await gr.resolve_article_version_graph(db, "v1")
        assert isinstance(result, gr.VersionSubgraph)
        assert result.version.entity_id == "v1"
        assert result.article is not None
        assert result.article.entity_id == "a1"
        assert result.loi is not None
        assert len(result.amendments) >= 1
        assert result.amendments[0].operation == "REPLACE"

    @pytest.mark.asyncio
    async def test_version_graph_not_found(self):
        db = _mock_db()
        db["article_versions"].find_one = AsyncMock(return_value=None)
        result = await gr.resolve_article_version_graph(db, "missing")
        assert result.version.label == "not found"


# ─────────────────────────────────────────────────────────────
# CompanyProfile → applicable Exigence / Action
# ─────────────────────────────────────────────────────────────

class TestCompanyProfileGraph:
    @pytest.mark.asyncio
    async def test_company_graph_with_applicable_exigences(self):
        db = _mock_db(
            company_profiles=[{"_id": "cp1", "id": "cp1", "name": "Acme SARL", "sector": "industrie"}],
            applicabilities=[
                {"_id": "ap1", "profile_id": "cp1", "exigence_id": "ex1", "is_applicable": True},
                {"_id": "ap2", "profile_id": "cp1", "exigence_id": "ex2", "is_applicable": False},
            ],
            exigences=[{"_id": "e1", "id": "ex1", "title": "Déclaration CNSS"}],
            actions=[{"_id": "act1", "id": "act1", "exigence_id": "ex1", "title": "Déposer formulaire"}],
            criticalities=[{"_id": "c1", "action_id": "act1", "score": 7.0, "level": "medium"}],
        )
        db["company_profiles"].find_one = AsyncMock(
            return_value={"_id": "cp1", "id": "cp1", "name": "Acme SARL", "sector": "industrie"},
        )
        db["action_criticalities"].find_one = AsyncMock(
            return_value={"_id": "c1", "action_id": "act1", "score": 7.0, "level": "medium"},
        )

        result = await gr.resolve_company_graph(db, "cp1")
        assert isinstance(result, gr.CompanyGraphContext)
        assert result.profile.label == "Acme SARL"
        assert len(result.applicable_exigences) == 1
        assert result.applicable_exigences[0].entity_id == "ex1"
        assert len(result.applicable_actions) == 1
        assert result.applicable_actions[0].entity_id == "act1"
        assert len(result.criticalities) == 1
        assert result.criticalities[0].level == "medium"
        # Edges: profile→exigence + exigence→action
        assert len(result.edges) == 2

    @pytest.mark.asyncio
    async def test_company_graph_not_found(self):
        db = _mock_db()
        db["company_profiles"].find_one = AsyncMock(return_value=None)
        result = await gr.resolve_company_graph(db, "missing")
        assert result.profile.label == "not found"
        assert result.applicable_exigences == []

    @pytest.mark.asyncio
    async def test_company_graph_no_applicable_exigences(self):
        db = _mock_db(
            company_profiles=[{"_id": "cp1", "id": "cp1", "name": "Empty Corp"}],
        )
        db["company_profiles"].find_one = AsyncMock(
            return_value={"_id": "cp1", "id": "cp1", "name": "Empty Corp"},
        )
        result = await gr.resolve_company_graph(db, "cp1")
        assert result.profile.label == "Empty Corp"
        assert result.applicable_exigences == []
        assert result.applicable_actions == []


# ─────────────────────────────────────────────────────────────
# build_structured_context_for_rag
# ─────────────────────────────────────────────────────────────

class TestBuildStructuredContextForRag:
    @pytest.mark.asyncio
    async def test_returns_graph_context(self):
        db = _mock_db(
            articles=[{"_id": "a1", "loi_id": "l1", "num": "1"}],
            loi=[{"_id": "l1", "code": "CT", "title": "Travail"}],
        )
        db["articles"].find_one = AsyncMock(return_value={"_id": "a1", "loi_id": "l1", "num": "1"})
        db["lois"].find_one = AsyncMock(return_value={"_id": "l1", "code": "CT", "title": "Travail"})
        db["action_criticalities"].find_one = AsyncMock(return_value=None)

        result = await gr.build_structured_context_for_rag(
            db, [{"article_id": "a1"}], max_entities=2,
        )
        assert isinstance(result, gr.GraphContext)
        assert result.stats["articles_resolved"] == 1
        assert result.stats["total_nodes"] >= 1

    @pytest.mark.asyncio
    async def test_empty_metadata_returns_empty_context(self):
        db = _mock_db()
        result = await gr.build_structured_context_for_rag(db, [])
        assert isinstance(result, gr.GraphContext)
        assert result.stats["total_nodes"] == 0
        assert result.text_summary == ""


# ─────────────────────────────────────────────────────────────
# DTO validation
# ─────────────────────────────────────────────────────────────

class TestDTOs:
    def test_graph_node_creation(self):
        node = gr.GraphNode(entity_type="article", entity_id="a1", label="Article 12")
        assert node.entity_type == "article"
        assert node.data == {}

    def test_graph_edge_creation(self):
        edge = gr.GraphEdge(
            source_type="loi", source_id="l1",
            target_type="article", target_id="a1",
            relation="contains_article",
        )
        assert edge.relation == "contains_article"

    def test_criticality_node(self):
        cn = gr.CriticalityNode(action_id="act1", score=9.0, level="critical")
        assert cn.score == 9.0

    def test_dependency_edge(self):
        de = gr.DependencyEdge(
            source_action_id="act1", target_action_id="act2",
            dependency_type="prerequisite",
        )
        assert de.dependency_type == "prerequisite"

    def test_amendment_node(self):
        am = gr.AmendmentNode(
            amendment_id="am1", operation="MODIFY", loi_id="l1",
            article_id="a1", version_id="v2",
        )
        assert am.version_id == "v2"
