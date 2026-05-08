"""
Graph Resolver (KG Light) — Sprint 6+ : Lightweight Knowledge Graph over MongoDB.

This module reconstructs a small legal knowledge graph from existing MongoDB
collections without introducing a dedicated graph database.  It traverses links
between laws, articles, versions, exigences, actions, criticalities, dependencies,
and amendments, then returns a structured subgraph that can be injected into
RAG context for richer grounding.

Entities:
  - loi          (from lois)
  - article      (from articles)
  - version      (from article_versions)
  - exigence     (from exigences)
  - action       (from actions)
  - criticality  (from action_criticalities)
  - dependency   (from action_dependencies)
  - amendment    (from amendment_operations)

The resolver is extendable: add new entity traversers without breaking existing
RAG pipelines.

PFE Thesis — Contribution scientifique
--------------------------------------
Plutôt que d'adopter une base de données graphe lourde (Neo4j, RDF), ce module
propose une approche « KG light » nativement intégrée au schéma documentaire
MongoDB existant. En exploitant les relations implicites entre lois, articles,
versions, exigences et actions, il enrichit le contexte RAG avec un sous-graphe
structuré sans duplication de données. Cette solution minimise l'overhead
opérationnel tout en apportant une dimension relationnelle au retrieval,
permettant à l'LLM de raisonner sur les dépendances inter-articles et les
impacts d'amendements dans les reponses juridiques générées.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Typed DTOs — Pydantic models for graph nodes and context
# ─────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    """Generic graph node representing any entity."""
    entity_type: str
    entity_id: str
    label: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Directed edge between two graph nodes."""
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relation: str


class CriticalityNode(BaseModel):
    action_id: str
    score: float = 0.0
    level: str = "unknown"
    data: dict[str, Any] = Field(default_factory=dict)


class DependencyEdge(BaseModel):
    source_action_id: str
    target_action_id: str
    dependency_type: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class AmendmentNode(BaseModel):
    amendment_id: str
    operation: str = ""
    loi_id: str = ""
    article_id: Optional[str] = None
    version_id: Optional[str] = None
    data: dict[str, Any] = Field(default_factory=dict)


class ArticleSubgraph(BaseModel):
    """Structured subgraph centered on an article."""
    article: GraphNode
    loi: Optional[GraphNode] = None
    versions: list[GraphNode] = Field(default_factory=list)
    exigences: list[GraphNode] = Field(default_factory=list)
    actions: list[GraphNode] = Field(default_factory=list)
    criticalities: list[CriticalityNode] = Field(default_factory=list)
    dependencies: list[DependencyEdge] = Field(default_factory=list)
    amendments: list[AmendmentNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class VersionSubgraph(BaseModel):
    """Structured subgraph centered on an article version."""
    version: GraphNode
    article: Optional[GraphNode] = None
    loi: Optional[GraphNode] = None
    exigences: list[GraphNode] = Field(default_factory=list)
    amendments: list[AmendmentNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class CompanyGraphContext(BaseModel):
    """Subgraph for a company profile's applicable exigences/actions."""
    profile: GraphNode
    applicable_exigences: list[GraphNode] = Field(default_factory=list)
    applicable_actions: list[GraphNode] = Field(default_factory=list)
    criticalities: list[CriticalityNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class GraphContext(BaseModel):
    """Full graph context payload for RAG injection."""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    amendments: list[AmendmentNode] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)
    text_summary: str = ""


def _safe_id(value: Any) -> Any:
    """Normalise MongoDB _id fields."""
    if isinstance(value, dict) and "$oid" in value:
        return value["$oid"]
    return value


async def resolve_loi_context(
    db: AsyncIOMotorDatabase,
    loi_id: str | None = None,
    loi_code: str | None = None,
    article_num: str | None = None,
    max_depth: int = 2,
) -> dict[str, Any]:
    """
    Build a subgraph centered on a Loi (by ID or code) optionally anchored on
    a specific article number.

    Returns
    -------
    {
        "loi": { ... },
        "articles": [ { ..., "versions": [ ... ], "exigences": [ ... ], "actions": [ ... ] } ],
        "amendments": [ { ... } ],
        "stats": { entity_counts ... }
    }
    """
    result: dict[str, Any] = {"loi": None, "articles": [], "amendments": [], "stats": {}}

    # 1. Resolve Loi
    loi_query: dict[str, Any] = {}
    if loi_id:
        loi_query["_id"] = loi_id
    elif loi_code:
        loi_query["code"] = loi_code
    else:
        return result

    loi_doc = await db["lois"].find_one(loi_query)
    if not loi_doc:
        return result
    result["loi"] = {k: v for k, v in loi_doc.items() if k not in ("embedding",)}
    loi_oid = _safe_id(loi_doc["_id"])

    # 2. Articles
    article_cursor = db["articles"].find({"loi_id": loi_oid})
    articles = []
    async for a in article_cursor:
        a["_id"] = _safe_id(a["_id"])
        articles.append(a)
    if article_num:
        articles = [a for a in articles if str(a.get("num")) == str(article_num)]
    result["articles"] = articles

    # 3. Versions + exigences + actions (depth 1)
    for art in articles:
        art_id = art["_id"]
        versions = []
        async for v in db["article_versions"].find({"article_id": art_id}).sort("version", -1).limit(3):
            v["_id"] = _safe_id(v["_id"])
            versions.append(v)
        art["versions"] = versions

        exigences = []
        async for e in db["exigences"].find({"article_id": art_id}):
            e["_id"] = _safe_id(e["_id"])
            exigences.append(e)
        art["exigences"] = exigences

        actions = []
        exigence_ids = [e["_id"] for e in exigences]
        if exigence_ids:
            async for ac in db["actions"].find({"exigence_id": {"$in": exigence_ids}}):
                ac["_id"] = _safe_id(ac["_id"])
                actions.append(ac)
        art["actions"] = actions

        # Depth 2: criticalities + dependencies
        if max_depth >= 2:
            action_ids = [ac["_id"] for ac in actions]
            for ac in actions:
                crit = await db["action_criticalities"].find_one({"action_id": ac["_id"]})
                if crit:
                    crit["_id"] = _safe_id(crit["_id"])
                ac["criticality"] = crit

            if action_ids:
                deps = []
                async for d in db["action_dependencies"].find({"$or": [
                    {"source_action_id": {"$in": action_ids}},
                    {"target_action_id": {"$in": action_ids}},
                ]}):
                    d["_id"] = _safe_id(d["_id"])
                    deps.append(d)
                art["dependencies"] = deps
            else:
                art["dependencies"] = []

    # 4. Amendments touching this Loi
    async for am in db["amendment_operations"].find({"loi_id": loi_oid}).sort("created_at", -1).limit(10):
        am["_id"] = _safe_id(am["_id"])
        result["amendments"].append(am)

    # 5. Stats
    result["stats"] = {
        "article_count": len(result["articles"]),
        "version_count": sum(len(a.get("versions", [])) for a in result["articles"]),
        "exigence_count": sum(len(a.get("exigences", [])) for a in result["articles"]),
        "action_count": sum(len(a.get("actions", [])) for a in result["articles"]),
        "amendment_count": len(result["amendments"]),
    }
    return result


async def resolve_entity_neighbors(
    db: AsyncIOMotorDatabase,
    entity_type: str,
    entity_id: str,
    max_depth: int = 1,
) -> dict[str, Any]:
    """
    Generic neighbor resolution for any entity type.

    Supported entity_type values: 'loi', 'article', 'action', 'exigence'.
    Returns a dict keyed by relation name containing related documents.
    """
    neighbors: dict[str, Any] = {"center": None, "relations": {}}
    collection_map = {
        "loi": "lois",
        "article": "articles",
        "action": "actions",
        "exigence": "exigences",
    }
    col = collection_map.get(entity_type)
    if not col:
        return neighbors

    doc = await db[col].find_one({"_id": entity_id})
    if not doc:
        return neighbors
    doc["_id"] = _safe_id(doc["_id"])
    neighbors["center"] = doc

    if entity_type == "article":
        versions = []
        async for v in db["article_versions"].find({"article_id": entity_id}).sort("version", -1).limit(3):
            v["_id"] = _safe_id(v["_id"])
            versions.append(v)
        neighbors["relations"]["versions"] = versions

        exigences = []
        async for e in db["exigences"].find({"article_id": entity_id}):
            e["_id"] = _safe_id(e["_id"])
            exigences.append(e)
        neighbors["relations"]["exigences"] = exigences

        # Parent loi
        loi_id = doc.get("loi_id")
        if loi_id and max_depth >= 1:
            loi = await db["lois"].find_one({"_id": loi_id})
            if loi:
                loi["_id"] = _safe_id(loi["_id"])
                neighbors["relations"]["loi"] = loi

    elif entity_type == "action":
        crit = await db["action_criticalities"].find_one({"action_id": entity_id})
        if crit:
            crit["_id"] = _safe_id(crit["_id"])
        neighbors["relations"]["criticality"] = crit

        deps = []
        async for d in db["action_dependencies"].find({
            "$or": [{"source_action_id": entity_id}, {"target_action_id": entity_id}]
        }):
            d["_id"] = _safe_id(d["_id"])
            deps.append(d)
        neighbors["relations"]["dependencies"] = deps

    return neighbors


async def kg_context_for_rag(
    db: AsyncIOMotorDatabase,
    chunk_metadata: list[dict],
    max_entities: int = 6,
) -> str:
    """
    Build a text snippet from the KG that can be prepended to RAG context.

    Parameters
    ----------
    chunk_metadata : list[dict]
        Metadata from the retrieved chunks (usually contains loi_id, article_id, etc.).
    max_entities : int
        Maximum distinct entities to resolve (to keep latency low).

    Returns
    -------
    str: A compact textual summary of the subgraph for injection.
    """
    seen_lois: set[str] = set()
    seen_articles: set[str] = set()
    lines: list[str] = []

    for meta in chunk_metadata[:max_entities]:
        loi_id = meta.get("loi_id") or meta.get("loi")
        art_id = meta.get("article_id") or meta.get("article")
        if loi_id and loi_id not in seen_lois:
            seen_lois.add(loi_id)
            loi = await db["lois"].find_one({"_id": loi_id})
            if loi:
                lines.append(f"Loi: {loi.get('title', '')} (Code: {loi.get('code','')}) — {loi.get('description','')}")
        if art_id and art_id not in seen_articles:
            seen_articles.add(art_id)
            art = await db["articles"].find_one({"_id": art_id})
            if art:
                lines.append(f"Article {art.get('num','')}: {art.get('title','')}")
                # Last version summary
                ver = await db["article_versions"].find_one({"article_id": art_id}, sort=[("version", -1)])
                if ver:
                    lines.append(f"  Dernière version ({ver.get('version','')}): {str(ver.get('text',''))[:200]}...")

    return "\n".join(lines) if lines else ""


# ─────────────────────────────────────────────────────────────
# Spec-required resolvers — filling identified gaps
# ─────────────────────────────────────────────────────────────

async def resolve_article_graph(
    db: AsyncIOMotorDatabase,
    article_id: str,
) -> ArticleSubgraph:
    """
    First-class article graph: Article → Versions, Exigences, Actions,
    Criticalities, Dependencies, Amendments, and parent Loi.

    Returns a typed ``ArticleSubgraph``.
    """
    art_doc = await db["articles"].find_one({"_id": article_id})
    if not art_doc:
        return ArticleSubgraph(
            article=GraphNode(entity_type="article", entity_id=article_id, label="not found"),
        )
    art_doc["_id"] = _safe_id(art_doc["_id"])
    art_node = GraphNode(entity_type="article", entity_id=str(art_doc["_id"]),
                         label=f"Article {art_doc.get('num', '')}", data=art_doc)
    edges: list[GraphEdge] = []

    # Parent loi
    loi_node: GraphNode | None = None
    loi_id = art_doc.get("loi_id")
    if loi_id:
        loi_doc = await db["lois"].find_one({"_id": loi_id})
        if loi_doc:
            loi_doc["_id"] = _safe_id(loi_doc["_id"])
            loi_node = GraphNode(entity_type="loi", entity_id=str(loi_doc["_id"]),
                                 label=loi_doc.get("title", ""), data=loi_doc)
            edges.append(GraphEdge(source_type="loi", source_id=str(loi_doc["_id"]),
                                   target_type="article", target_id=str(art_doc["_id"]),
                                   relation="contains_article"))

    # Versions
    version_nodes: list[GraphNode] = []
    async for v in db["article_versions"].find({"article_id": article_id}).sort("version", -1).limit(5):
        v["_id"] = _safe_id(v["_id"])
        vn = GraphNode(entity_type="version", entity_id=str(v["_id"]),
                       label=f"v{v.get('version', '')}", data=v)
        version_nodes.append(vn)
        edges.append(GraphEdge(source_type="article", source_id=str(art_doc["_id"]),
                               target_type="version", target_id=str(v["_id"]),
                               relation="has_version"))

    # Exigences
    exigence_nodes: list[GraphNode] = []
    async for e in db["exigences"].find({"article_id": article_id}):
        e["_id"] = _safe_id(e["_id"])
        en = GraphNode(entity_type="exigence", entity_id=str(e["_id"]),
                       label=e.get("title", e.get("description", "")[:80]), data=e)
        exigence_nodes.append(en)
        edges.append(GraphEdge(source_type="article", source_id=str(art_doc["_id"]),
                               target_type="exigence", target_id=str(e["_id"]),
                               relation="defines_exigence"))

    # Actions (from exigences)
    action_nodes: list[GraphNode] = []
    criticality_nodes: list[CriticalityNode] = []
    dependency_edges: list[DependencyEdge] = []
    exigence_ids = [en.entity_id for en in exigence_nodes]
    if exigence_ids:
        async for ac in db["actions"].find({"exigence_id": {"$in": exigence_ids}}):
            ac["_id"] = _safe_id(ac["_id"])
            an = GraphNode(entity_type="action", entity_id=str(ac["_id"]),
                           label=ac.get("title", ac.get("description", "")[:80]), data=ac)
            action_nodes.append(an)
            edges.append(GraphEdge(source_type="exigence", source_id=str(ac.get("exigence_id", "")),
                                   target_type="action", target_id=str(ac["_id"]),
                                   relation="requires_action"))

            # Criticality
            crit = await db["action_criticalities"].find_one({"action_id": str(ac["_id"])})
            if crit:
                crit["_id"] = _safe_id(crit["_id"])
                criticality_nodes.append(CriticalityNode(
                    action_id=str(ac["_id"]),
                    score=float(crit.get("score", 0)),
                    level=str(crit.get("level", "unknown")),
                    data=crit,
                ))

        # Dependencies
        action_ids = [an.entity_id for an in action_nodes]
        if action_ids:
            async for d in db["action_dependencies"].find({"$or": [
                {"source_action_id": {"$in": action_ids}},
                {"target_action_id": {"$in": action_ids}},
            ]}):
                d["_id"] = _safe_id(d["_id"])
                dependency_edges.append(DependencyEdge(
                    source_action_id=str(d.get("source_action_id", "")),
                    target_action_id=str(d.get("target_action_id", "")),
                    dependency_type=str(d.get("type", d.get("dependency_type", ""))),
                    data=d,
                ))

    # Amendments affecting this article
    amendment_nodes: list[AmendmentNode] = []
    async for am in db["amendment_operations"].find({"article_id": article_id}).sort("created_at", -1).limit(10):
        am["_id"] = _safe_id(am["_id"])
        amendment_nodes.append(AmendmentNode(
            amendment_id=str(am["_id"]),
            operation=str(am.get("operation", "")),
            loi_id=str(am.get("loi_id", "")),
            article_id=str(am.get("article_id", "")),
            version_id=str(am.get("version_id", "")) if am.get("version_id") else None,
            data=am,
        ))

    return ArticleSubgraph(
        article=art_node,
        loi=loi_node,
        versions=version_nodes,
        exigences=exigence_nodes,
        actions=action_nodes,
        criticalities=criticality_nodes,
        dependencies=dependency_edges,
        amendments=amendment_nodes,
        edges=edges,
    )


async def resolve_article_version_graph(
    db: AsyncIOMotorDatabase,
    version_id: str,
) -> VersionSubgraph:
    """
    First-class version graph: ArticleVersion → parent Article → parent Loi,
    linked Exigences (via article_id), and Amendments targeting this version.

    Returns a typed ``VersionSubgraph``.
    """
    ver_doc = await db["article_versions"].find_one({"_id": version_id})
    if not ver_doc:
        return VersionSubgraph(
            version=GraphNode(entity_type="version", entity_id=version_id, label="not found"),
        )
    ver_doc["_id"] = _safe_id(ver_doc["_id"])
    ver_node = GraphNode(entity_type="version", entity_id=str(ver_doc["_id"]),
                         label=f"v{ver_doc.get('version', '')}", data=ver_doc)
    edges: list[GraphEdge] = []

    # Parent article
    art_node: GraphNode | None = None
    loi_node: GraphNode | None = None
    art_id = ver_doc.get("article_id")
    if art_id:
        art_doc = await db["articles"].find_one({"_id": art_id})
        if art_doc:
            art_doc["_id"] = _safe_id(art_doc["_id"])
            art_node = GraphNode(entity_type="article", entity_id=str(art_doc["_id"]),
                                 label=f"Article {art_doc.get('num', '')}", data=art_doc)
            edges.append(GraphEdge(source_type="article", source_id=str(art_doc["_id"]),
                                   target_type="version", target_id=str(ver_doc["_id"]),
                                   relation="has_version"))
            # Grandparent loi
            loi_id = art_doc.get("loi_id")
            if loi_id:
                loi_doc = await db["lois"].find_one({"_id": loi_id})
                if loi_doc:
                    loi_doc["_id"] = _safe_id(loi_doc["_id"])
                    loi_node = GraphNode(entity_type="loi", entity_id=str(loi_doc["_id"]),
                                         label=loi_doc.get("title", ""), data=loi_doc)
                    edges.append(GraphEdge(source_type="loi", source_id=str(loi_doc["_id"]),
                                           target_type="article", target_id=str(art_doc["_id"]),
                                           relation="contains_article"))

    # Exigences via article_id
    exigence_nodes: list[GraphNode] = []
    if art_id:
        async for e in db["exigences"].find({"article_id": art_id}):
            e["_id"] = _safe_id(e["_id"])
            en = GraphNode(entity_type="exigence", entity_id=str(e["_id"]),
                           label=e.get("title", e.get("description", "")[:80]), data=e)
            exigence_nodes.append(en)
            edges.append(GraphEdge(source_type="version", source_id=str(ver_doc["_id"]),
                                   target_type="exigence", target_id=str(e["_id"]),
                                   relation="version_defines_exigence"))

    # Amendments targeting this specific version
    amendment_nodes: list[AmendmentNode] = []
    async for am in db["amendment_operations"].find({"version_id": version_id}).sort("created_at", -1).limit(10):
        am["_id"] = _safe_id(am["_id"])
        amendment_nodes.append(AmendmentNode(
            amendment_id=str(am["_id"]),
            operation=str(am.get("operation", "")),
            loi_id=str(am.get("loi_id", "")),
            article_id=str(am.get("article_id", "")) if am.get("article_id") else None,
            version_id=str(am.get("version_id", "")),
            data=am,
        ))
    # Also fetch amendments by article_id that have no version_id (legacy)
    if art_id:
        async for am in db["amendment_operations"].find({
            "article_id": art_id, "version_id": {"$exists": False}
        }).sort("created_at", -1).limit(5):
            am["_id"] = _safe_id(am["_id"])
            amendment_nodes.append(AmendmentNode(
                amendment_id=str(am["_id"]),
                operation=str(am.get("operation", "")),
                loi_id=str(am.get("loi_id", "")),
                article_id=str(am.get("article_id", "")),
                version_id=None,
                data=am,
            ))

    return VersionSubgraph(
        version=ver_node,
        article=art_node,
        loi=loi_node,
        exigences=exigence_nodes,
        amendments=amendment_nodes,
        edges=edges,
    )


async def resolve_company_graph(
    db: AsyncIOMotorDatabase,
    profile_id: str,
) -> CompanyGraphContext:
    """
    CompanyProfile → applicable Exigences → Actions → Criticalities.

    Uses the ``exigence_applicabilities`` collection to find which exigences
    are applicable to this company, then follows exigence → action → criticality.

    Returns a typed ``CompanyGraphContext``.
    """
    profile_doc = await db["company_profiles"].find_one({"id": profile_id})
    if not profile_doc:
        return CompanyGraphContext(
            profile=GraphNode(entity_type="company_profile", entity_id=profile_id, label="not found"),
        )
    profile_doc["_id"] = _safe_id(profile_doc.get("_id", ""))
    profile_node = GraphNode(
        entity_type="company_profile",
        entity_id=str(profile_doc.get("id", profile_doc["_id"])),
        label=profile_doc.get("name", ""),
        data={k: v for k, v in profile_doc.items() if k != "_id"},
    )
    edges: list[GraphEdge] = []

    # Applicable exigences via exigence_applicabilities
    applicable_exigence_ids: list[str] = []
    async for app in db["exigence_applicabilities"].find({
        "profile_id": profile_id, "is_applicable": True,
    }):
        eid = app.get("exigence_id")
        if eid:
            applicable_exigence_ids.append(str(eid))

    exigence_nodes: list[GraphNode] = []
    if applicable_exigence_ids:
        async for e in db["exigences"].find({"id": {"$in": applicable_exigence_ids}}):
            e["_id"] = _safe_id(e["_id"])
            en = GraphNode(entity_type="exigence", entity_id=str(e.get("id", e["_id"])),
                           label=e.get("title", e.get("description", "")[:80]), data=e)
            exigence_nodes.append(en)
            edges.append(GraphEdge(
                source_type="company_profile", source_id=profile_node.entity_id,
                target_type="exigence", target_id=en.entity_id,
                relation="applicable_exigence",
            ))

    # Actions from applicable exigences
    action_nodes: list[GraphNode] = []
    criticality_nodes: list[CriticalityNode] = []
    ex_ids_for_actions = [en.entity_id for en in exigence_nodes]
    if ex_ids_for_actions:
        async for ac in db["actions"].find({"exigence_id": {"$in": ex_ids_for_actions}}):
            ac["_id"] = _safe_id(ac["_id"])
            an = GraphNode(entity_type="action", entity_id=str(ac.get("id", ac["_id"])),
                           label=ac.get("title", ac.get("description", "")[:80]), data=ac)
            action_nodes.append(an)
            edges.append(GraphEdge(
                source_type="exigence", source_id=str(ac.get("exigence_id", "")),
                target_type="action", target_id=an.entity_id,
                relation="requires_action",
            ))

            # Criticality for each action
            crit = await db["action_criticalities"].find_one({"action_id": str(ac.get("id", ac["_id"]))})
            if crit:
                crit["_id"] = _safe_id(crit["_id"])
                criticality_nodes.append(CriticalityNode(
                    action_id=an.entity_id,
                    score=float(crit.get("score", 0)),
                    level=str(crit.get("level", "unknown")),
                    data=crit,
                ))

    return CompanyGraphContext(
        profile=profile_node,
        applicable_exigences=exigence_nodes,
        applicable_actions=action_nodes,
        criticalities=criticality_nodes,
        edges=edges,
    )


async def build_structured_context_for_rag(
    db: AsyncIOMotorDatabase,
    chunk_metadata: list[dict],
    company_profile_id: str | None = None,
    max_entities: int = 6,
) -> GraphContext:
    """
    High-level entry point that assembles a full ``GraphContext`` from chunk
    metadata and optional company profile, ready for RAG prompt injection.

    Combines article subgraphs, company graph, and a text summary.
    """
    all_nodes: list[GraphNode] = []
    all_edges: list[GraphEdge] = []
    all_amendments: list[AmendmentNode] = []
    seen_articles: set[str] = set()

    # Resolve article subgraphs from chunk metadata
    for meta in chunk_metadata[:max_entities]:
        art_id = meta.get("article_id") or meta.get("article")
        if art_id and art_id not in seen_articles:
            seen_articles.add(art_id)
            subgraph = await resolve_article_graph(db, art_id)
            all_nodes.append(subgraph.article)
            if subgraph.loi:
                all_nodes.append(subgraph.loi)
            all_nodes.extend(subgraph.versions)
            all_nodes.extend(subgraph.exigences)
            all_nodes.extend(subgraph.actions)
            all_edges.extend(subgraph.edges)
            all_amendments.extend(subgraph.amendments)

    # Company profile enrichment
    if company_profile_id:
        cpg = await resolve_company_graph(db, company_profile_id)
        if cpg.profile.label != "not found":
            all_nodes.append(cpg.profile)
            all_nodes.extend(cpg.applicable_exigences)
            all_nodes.extend(cpg.applicable_actions)
            all_edges.extend(cpg.edges)

    # Build text summary (reuse kg_context_for_rag for the textual part)
    text_summary = await kg_context_for_rag(db, chunk_metadata, max_entities=max_entities)

    stats = {
        "total_nodes": len(all_nodes),
        "total_edges": len(all_edges),
        "total_amendments": len(all_amendments),
        "articles_resolved": len(seen_articles),
    }

    return GraphContext(
        nodes=all_nodes,
        edges=all_edges,
        amendments=all_amendments,
        stats=stats,
        text_summary=text_summary,
    )
