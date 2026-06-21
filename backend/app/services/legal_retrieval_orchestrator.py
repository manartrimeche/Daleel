"""
Legal Retrieval Orchestrator — Sprint 6+ : Domain-Partitioned RAG for Base Laws vs Amendments.

This module orchestrates retrieval from two distinct partitions:

  1. Base Law Retriever  — operates over article_versions of the original text
     (stable, authoritative, pre-amendment state).
  2. Amendment Retriever  — operates over amendment_operations and the latest
     article versions (post-amendment, volatile).

Intent classification drives the mixing ratio:
  - "current_state"    (default) → mostly latest versions (amendments applied)
  - "historical"       → mostly base law versions
  - "compare"          → both, interleaved so the LLM sees before/after
  - "compliance_audit" → latest versions + relevant exigences/actions

The orchestrator is agnostic of the vector backend; it receives a search
callable (e.g. search_service.similarity_search) and wraps it with filtering
and mixing logic.

PFE Thesis — Contribution scientifique
--------------------------------------
Ce module formalise une approche de « retrieval partitionné » pour la veille
juridique tunisienne. En séparant les versions de base des textes originels des
versions amendées, il évite le mélange anarchique de sources contradictoires.
La stratégie de mixing pilotée par l'intention de l'utilisateur (état courant,
historique, comparaison, audit de conformité) permet d'adapter dynamiquement
la composition du corpus retrieved. Cette architecture partitionnée renforce la
fiabilité des reponses dans un contexte législatif où les amendements successifs
peuvent invalider des dispositions antérieures.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol, runtime_checkable

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Question-category keyword classifier (trilingual)
# ─────────────────────────────────────────────────────────────

_LEGAL_INTENT_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "current_rule_query": {
        "fr": [
            "texte en vigueur", "version actuelle", "article actuel",
            "disposition applicable", "loi applicable", "droit en vigueur",
            "réglementation actuelle", "que dit la loi", "que prévoit",
        ],
        "ar": [
            "النص الساري", "النسخة الحالية", "الفصل الحالي",
            "القانون المعمول به", "ماذا ينص القانون",
        ],
        "en": [
            "current law", "active provision", "in force", "current version",
            "applicable rule", "what does the law say", "current article",
        ],
    },
    "change_tracking_query": {
        "fr": [
            "amendement", "modification", "historique", "évolution",
            "changement", "avant après", "abrogé", "remplacé",
            "ancienne version", "nouvelle version", "qu'est-ce qui a changé",
        ],
        "ar": [
            "تعديل", "تنقيح", "تاريخ", "تطور", "تغيير",
            "قبل وبعد", "ملغى", "النسخة القديمة",
        ],
        "en": [
            "amendment", "modification", "history", "evolution",
            "what changed", "repealed", "replaced", "old version",
            "before and after", "change tracking",
        ],
    },
    "impact_query": {
        "fr": [
            "impact", "conséquence", "effet", "incidence",
            "concerne mon entreprise", "applicable à ma société",
            "conformité", "mise en conformité", "risque",
            "profil entreprise", "plan de conformité",
        ],
        "ar": [
            "تأثير", "أثر", "نتيجة", "يخص شركتي",
            "امتثال", "خطة امتثال", "مخاطر",
        ],
        "en": [
            "impact", "consequence", "effect", "affects my company",
            "compliance", "compliance plan", "risk", "company profile",
        ],
    },
}


def classify_legal_intent(question: str, lang: str = "fr") -> str:
    """
    Classify a user question into one of the spec categories:
      - current_rule_query
      - change_tracking_query
      - impact_query

    Falls back to ``current_rule_query`` when no keywords match.
    """
    q = (question or "").lower()
    best_category = "current_rule_query"
    best_score = 0
    for category, lang_map in _LEGAL_INTENT_KEYWORDS.items():
        score = 0
        for kw in lang_map.get(lang, []) + lang_map.get("en", []):
            if kw in q:
                score += 1
        if score > best_score:
            best_score = score
            best_category = category
    return best_category


# ─────────────────────────────────────────────────────────────
# Formal retriever strategy abstractions
# ─────────────────────────────────────────────────────────────

@runtime_checkable
class RetrieverStrategy(Protocol):
    """Protocol for pluggable retriever strategies."""
    async def retrieve(
        self,
        question: str,
        search_fn: Callable[..., Awaitable[list[dict]]],
        db: AsyncIOMotorDatabase,
        top_k: int = 10,
        extra_filter: dict[str, Any] | None = None,
    ) -> list[dict]: ...


@dataclass
class BaseLawRetriever:
    """Retrieves from original / base-version article texts."""
    async def retrieve(
        self,
        question: str,
        search_fn: Callable[..., Awaitable[list[dict]]],
        db: AsyncIOMotorDatabase,
        top_k: int = 10,
        extra_filter: dict[str, Any] | None = None,
    ) -> list[dict]:
        pf: dict[str, Any] = {"is_base_version": True}
        if extra_filter:
            pf.update(extra_filter)
        try:
            chunks = await search_fn(question, top_k=top_k, extra_filter=pf)
        except Exception as e:
            logger.warning("BaseLawRetriever search failed: %s", e)
            chunks = []
        for c in chunks:
            c["_partition_source"] = "base"
        return chunks


@dataclass
class AmendmentRetriever:
    """Retrieves from amended / post-amendment article texts and amendment_operations."""
    async def retrieve(
        self,
        question: str,
        search_fn: Callable[..., Awaitable[list[dict]]],
        db: AsyncIOMotorDatabase,
        top_k: int = 10,
        extra_filter: dict[str, Any] | None = None,
    ) -> list[dict]:
        pf: dict[str, Any] = {"is_base_version": {"$ne": True}}
        if extra_filter:
            pf.update(extra_filter)
        try:
            chunks = await search_fn(question, top_k=top_k, extra_filter=pf)
        except Exception as e:
            logger.warning("AmendmentRetriever search failed: %s", e)
            chunks = []
        for c in chunks:
            c["_partition_source"] = "amendment"
        return chunks


@dataclass
class HybridRetriever:
    """Combines base-law and amendment retrieval with configurable weights."""
    base_weight: float = 0.50
    amendment_weight: float = 0.50

    async def retrieve(
        self,
        question: str,
        search_fn: Callable[..., Awaitable[list[dict]]],
        db: AsyncIOMotorDatabase,
        top_k: int = 10,
        extra_filter: dict[str, Any] | None = None,
    ) -> list[dict]:
        base_k = max(1, int(top_k * self.base_weight / (self.base_weight + self.amendment_weight)))
        amend_k = max(1, top_k - base_k)
        base_ret = BaseLawRetriever()
        amend_ret = AmendmentRetriever()
        base_chunks = await base_ret.retrieve(question, search_fn, db, base_k, extra_filter)
        amend_chunks = await amend_ret.retrieve(question, search_fn, db, amend_k, extra_filter)
        for c in base_chunks:
            c["_partition_weight"] = self.base_weight
        for c in amend_chunks:
            c["_partition_weight"] = self.amendment_weight
        return base_chunks + amend_chunks


@dataclass
class RetrievalMix:
    """Parameters for a single retrieval call."""
    source: str  # "base" | "amendment" | "exigence" | "action"
    weight: float  # 0..1 relative weight in the final merged list
    filter: dict[str, Any] | None = None
    top_k: int = 10


async def intent_to_mix(
    intent: str,
    domain_config: Any | None = None,
) -> list[RetrievalMix]:
    """Map high-level intent to a retrieval mix.

    Supports both internal intents (current_state, historical, compare,
    compliance_audit) and spec-required categories (current_rule_query,
    change_tracking_query, impact_query).
    """
    intent = (intent or "current_state").lower()

    # ── Spec category aliases ──
    if intent == "current_rule_query":
        intent = "current_state"
    elif intent == "change_tracking_query":
        intent = "historical"
    elif intent == "impact_query":
        intent = "compliance_audit"

    if intent == "historical":
        return [
            RetrievalMix(source="base", weight=0.85, top_k=12),
            RetrievalMix(source="amendment", weight=0.15, top_k=4),
        ]
    if intent == "compare":
        return [
            RetrievalMix(source="base", weight=0.50, top_k=8),
            RetrievalMix(source="amendment", weight=0.50, top_k=8),
        ]
    if intent == "compliance_audit":
        return [
            RetrievalMix(source="base", weight=0.40, top_k=8),
            RetrievalMix(source="amendment", weight=0.40, top_k=8),
            RetrievalMix(source="exigence", weight=0.10, top_k=4),
            RetrievalMix(source="action", weight=0.10, top_k=4),
        ]
    # Default = current_state
    return [
        RetrievalMix(source="amendment", weight=0.70, top_k=12),
        RetrievalMix(source="base", weight=0.30, top_k=6),
    ]


async def retrieve_partitioned(
    question: str,
    intent: str,
    search_fn: Callable[..., Awaitable[list[dict]]],
    db: AsyncIOMotorDatabase,
    domain_config: Any | None = None,
    extra_filter: dict[str, Any] | None = None,
) -> list[dict]:
    """
    Retrieve chunks from multiple partitions and merge them into a single ranked list.

    Parameters
    ----------
    question : str
        The user query (passed to search_fn).
    intent : str
        One of current_state, historical, compare, compliance_audit.
    search_fn : Callable
        Async function signature: search_fn(question, top_k, extra_filter) -> list[dict]
    db : AsyncIOMotorDatabase
        MongoDB handle for fallback / enrichment lookups.
    domain_config : Any | None
        Optional domain config (e.g. DomainConfig) for top_k overrides.
    extra_filter : dict | None
        Additional MongoDB filter merged into partition filters.

    Returns
    -------
    list[dict] : merged and deduplicated chunks, preserving relevance order.
    """
    mix = await intent_to_mix(intent, domain_config)
    async def _fetch_partition(m: RetrievalMix) -> list[dict]:
        top_k = m.top_k
        if domain_config and hasattr(domain_config, "top_k"):
            top_k = domain_config.top_k

        # Build partition filter
        pf: dict[str, Any] = {}
        if m.source == "base":
            pf["is_base_version"] = True  # convention in chunk metadata
        elif m.source == "amendment":
            pf["is_base_version"] = {"$ne": True}
        elif m.source == "exigence":
            pf["type"] = "exigence"
        elif m.source == "action":
            pf["type"] = "action"

        merged_filter: dict[str, Any] = {}
        if pf:
            merged_filter.update(pf)
        if extra_filter:
            merged_filter.update(extra_filter)

        try:
            chunks = await search_fn(question, top_k=top_k, extra_filter=merged_filter or None)
        except Exception as e:
            logger.warning("Partition '%s' search failed: %s", m.source, e)
            return []

        for c in chunks:
            c["_partition_source"] = m.source
            c["_partition_weight"] = m.weight
        return chunks

    partition_results = await asyncio.gather(
        *(_fetch_partition(m) for m in mix),
        return_exceptions=True,
    )
    collected: list[dict] = []
    for result in partition_results:
        if isinstance(result, Exception):
            logger.warning("Partitioned retrieval task failed: %s", result)
            continue
        collected.extend(result)

    # Deduplicate by _id or text hash
    seen: set[str] = set()
    deduped: list[dict] = []
    for c in collected:
        key = c.get("_id") or hash(c.get("text", ""))
        key_str = str(key)
        if key_str not in seen:
            seen.add(key_str)
            deduped.append(c)

    # Weighted merge: apply partition weight as a boost to the intra-partition
    # position score, then sort globally by descending weighted score.
    for rank, c in enumerate(deduped):
        base_score = float(c.get("score", c.get("hybrid_score", 0.0)))
        weight = float(c.get("_partition_weight", 0.5))
        # Position decay: earlier items in each partition get a positional boost
        position_bonus = 1.0 / (1 + rank * 0.1)
        c["_merge_score"] = (base_score + position_bonus) * weight

    deduped.sort(key=lambda c: c.get("_merge_score", 0), reverse=True)

    # Trim to a sensible total (configurable)
    total_limit = getattr(domain_config, "top_k", 14) if domain_config else 14
    return deduped[:total_limit]


async def get_current_article_text(
    db: AsyncIOMotorDatabase,
    article_id: str,
) -> str | None:
    """
    Return the current (post-amendment) text of an article by fetching the
    latest article_version.
    """
    try:
        ver = await db["article_versions"].find_one(
            {"article_id": article_id},
            sort=[("version", -1)],
        )
        return ver.get("text") if ver else None
    except Exception as e:
        logger.error("Failed to fetch current article text for %s: %s", article_id, e)
        return None


async def get_base_article_text(
    db: AsyncIOMotorDatabase,
    article_id: str,
) -> str | None:
    """
    Return the base (original) text of an article (version = 1 or is_base_version=True).
    """
    try:
        ver = await db["article_versions"].find_one(
            {"article_id": article_id, "$or": [{"version": 1}, {"is_base_version": True}]},
            sort=[("version", 1)],
        )
        return ver.get("text") if ver else None
    except Exception as e:
        logger.error("Failed to fetch base article text for %s: %s", article_id, e)
        return None
