"""
Domain Router — Sprint 6+ : Domain-Aware RAG for Tunisian Legal Compliance.

Routes a user question to the most appropriate legal domain pipeline.
Domains: data_protection, labor, corporate, investment, credit_info, cross_domain, unknown.

Strategy:
  1. Lexical scoring (fast, deterministic) using domain keyword maps.
  2. Optional LLM-based routing fallback when lexical scores are ambiguous.

Each domain carries its own retrieval parameters and system prompt suffix.

PFE Thesis — Contribution scientifique
--------------------------------------
Ce module résout le verrou de la spécialisation sémantique en droit tunisien.
En partitionnant l'espace documentaire en domaines juridiques (travail,
sociétés, protection des données, investissement), le routeur lexical + LLM
permet d'ajuster dynamiquement la configuration de recherche (top_k, poids
lexical, suffixe système) sans intervention humaine. Cela constitue une
approche de « domain-adaptive RAG » où la phase de retrieval est guidée par
la prédiction du domaine cible, réduisant le bruit inter-domaine et améliorant
la précision des citations juridiques.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Iterator

from app.config import get_settings

logger = logging.getLogger(__name__)

_DOMAIN_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "data_protection": {
        "fr": [
            "données personnelles", "INPDP", "protection des données",
            "vie privée", "RGPD", "collecte", "traitement",
            "suppression", "déclaration", "consentement",
            "hébergé", "transfert", "données à caractère personnel",
            "droit à l'effacement", "loi 2004-63",
        ],
        "ar": [
            "البيانات الشخصية", "حماية البيانات", "الخصوصية",
            "معطيات شخصية", "حذف", "تصريح", "الموافقة",
        ],
        "en": ["personal data", "data protection", "privacy", "GDPR"],
    },
    "labor": {
        "fr": [
            "employeur", "salarié", "contrat de travail",
            "licenciement", "code du travail", "syndicat",
            "heures supplémentaires", "salaire", "ouvrier",
            "inspection du travail", "accident du travail",
            "congé", "droit du travail",
            "travailleur", "employé", "préavis",
            "cdi", "cdd", "période d'essai", "periode d'essai",
            "période d’essai", "periode d’essai", "confirmation",
            "indemnité de licenciement", "durée du travail",
            "repos hebdomadaire", "CNSS", "SMIG",
            "convention collective", "contrat à durée déterminée",
            "contrat à durée indéterminée",
        ],
        "ar": [
            "عمل", "عقد العمل", "إقالة", "مدونة الشغل", "نقابة",
            "عامل", "عمال", "أجور", "أجر", "عقود",
            "مشغل", "ساعات إضافية", "العمل الإضافي",
            "مجلة الشغل", "تسريح", "حادث شغل", "عقد شغل",
            "حقوق العامل", "رخصة", "ساعات العمل",
        ],
        "en": [
            "labor law", "employment", "work contract", "dismissal",
            "trade union", "employee", "overtime", "wages", "worker",
        ],
    },
    "corporate": {
        "fr": [
            "société", "SARL", "SA", "SUARL", "constitution", "gérant",
            "code des sociétés", "registre de commerce",
            "associé", "actionnaire", "parts sociales",
            "assemblée générale", "statuts", "dissolution", "capital social",
        ],
        "ar": [
            "شركة", "مسير", "مجلة الشركات", "السجل التجاري", "تأسيس",
            "شريك", "مساهم", "رأس المال",
        ],
        "en": ["company", "corporation", "incorporation", "manager", "company law"],
    },
    "investment": {
        "fr": ["investissement", "APII", "investisseur", "incitation fiscale", "code de l'investissement"],
        "ar": ["استثمار", "مستثمر", "إعفاء ضريبي"],
        "en": ["investment", "investor", "tax incentive", "startup"],
    },
    "credit_info": {
        "fr": [
            "société de renseignement de crédit", "renseignement de crédit",
            "bureau de crédit", "historique de crédit", "solvabilité",
            "notation de crédit", "risque de crédit", "scoring",
            "données de crédit", "centrale des risques",
            "Banque Centrale de Tunisie", "BCT",
            "fichier des crédits", "endettement",
            "information crédit", "crédit scoring",
        ],
        "ar": [
            "شركة استعلام ائتماني", "استعلام ائتماني",
            "مخاطر الائتمان", "البنك المركزي",
            "تصنيف ائتماني", "ملاءة مالية",
            "مركزية المخاطر", "ديون",
        ],
        "en": [
            "credit information", "credit bureau", "credit score",
            "credit risk", "creditworthiness", "credit rating",
        ],
    },
}


@dataclass
class DomainConfig:
    domain: str
    top_k: int = 10
    similarity_threshold: float = 0.55
    vector_weight: float = 0.56
    lexical_weight: float = 0.20
    keyword_weight: float = 0.14
    anchor_weight: float = 0.10
    lexical_boosts: list[tuple[re.Pattern, float]] = field(default_factory=list)
    system_prompt_suffix: str = ""


@dataclass
class RouteResult:
    """Result of domain routing with confidence and explanation.

    Supports tuple unpacking ``domain, config = route_question(...)`` for
    backward-compatible call sites, while exposing *confidence* and
    *explanation* for callers that need richer diagnostics.
    """

    domain: str
    config: DomainConfig
    confidence: float = 0.0
    explanation: str = ""

    # Allow  domain, config = route_result
    def __iter__(self) -> Iterator:
        return iter((self.domain, self.config))


_DEFAULT_CONFIGS: dict[str, DomainConfig] = {
    "data_protection": DomainConfig(
        domain="data_protection",
        top_k=12,
        similarity_threshold=0.60,
        system_prompt_suffix="Dans cette consultation, concentrez-vous sur la protection des données personnelles en Tunisie. Appuyez-vous sur la loi n°2004-63 et les textes INPDP. Restez strictement ancré dans les sources.",
    ),
    "labor": DomainConfig(
        domain="labor",
        top_k=12,
        similarity_threshold=0.55,
        system_prompt_suffix="Dans cette consultation, concentrez-vous sur le droit du travail tunisien. Citez le Code du Travail (مجلة الشغل). Précisez les conditions d'applicabilité.",
    ),
    "corporate": DomainConfig(
        domain="corporate",
        top_k=10,
        similarity_threshold=0.55,
        lexical_boosts=[
            (re.compile(r"\bSARL\b|\bSA\b|\bSUARL\b", re.IGNORECASE), 0.06),
            (re.compile(r"\bCode des Sociétés\b", re.IGNORECASE), 0.08),
        ],
        system_prompt_suffix="Dans cette consultation, concentrez-vous sur le droit des sociétés tunisien. Citez le Code des sociétés commerciales (مجلة الشركات التجارية). Distinguez SARL, SA et SUARL.",
    ),
    "investment": DomainConfig(
        domain="investment",
        top_k=10,
        similarity_threshold=0.55,
        system_prompt_suffix="Dans cette consultation, concentrez-vous sur le droit de l'investissement en Tunisie. Citez le Code de l'Investissement et les dispositions APII.",
    ),
    "credit_info": DomainConfig(
        domain="credit_info",
        top_k=10,
        similarity_threshold=0.58,
        system_prompt_suffix="Dans cette consultation, concentrez-vous sur la réglementation des sociétés de renseignement de crédit en Tunisie. Citez les circulaires de la Banque Centrale de Tunisie (BCT). Restez strictement ancré dans les sources.",
    ),
    "cross_domain": DomainConfig(
        domain="cross_domain",
        top_k=14,
        similarity_threshold=0.50,
        vector_weight=0.50,
        lexical_weight=0.24,
        system_prompt_suffix="Cette question touche plusieurs domaines juridiques. Structurez votre analyse par domaine et signalez les interactions entre les textes.",
    ),
    "unknown": DomainConfig(
        domain="unknown",
        top_k=10,
        similarity_threshold=0.50,
        system_prompt_suffix="Restez prudent et ancrez chaque affirmation dans les sources disponibles.",
    ),
}


def _load_keyword_overrides() -> None:
    raw = os.getenv("DALEEL_DOMAIN_KEYWORD_OVERRIDES_JSON", "")
    if not raw:
        return
    try:
        parsed: dict = json.loads(raw)
        for domain, lang_map in parsed.items():
            for lang, kws in lang_map.items():
                if isinstance(kws, list):
                    _DOMAIN_KEYWORDS.setdefault(domain, {}).setdefault(lang, []).extend(kws)
    except Exception as e:
        logger.warning("Failed to parse DALEEL_DOMAIN_KEYWORD_OVERRIDES_JSON: %s", e)


_load_keyword_overrides()


_SHORT_KW_BOUNDARY_RE_CACHE: dict[str, re.Pattern] = {}


def _keyword_in_text(kw_lower: str, text_lower: str) -> bool:
    """Match keyword in text; uses word boundaries for short keywords (<=3 chars)
    to prevent false positives like 'SA' matching inside 'savons'."""
    if len(kw_lower) <= 3:
        pat = _SHORT_KW_BOUNDARY_RE_CACHE.get(kw_lower)
        if pat is None:
            pat = re.compile(rf"\b{re.escape(kw_lower)}\b")
            _SHORT_KW_BOUNDARY_RE_CACHE[kw_lower] = pat
        return bool(pat.search(text_lower))
    return kw_lower in text_lower


def _lexical_scores(question: str, lang: str) -> dict[str, float]:
    q = (question or "").lower()
    scores: dict[str, float] = {}
    for domain, lang_map in _DOMAIN_KEYWORDS.items():
        keywords = lang_map.get(lang, []) + lang_map.get("en", [])
        if not keywords:
            continue
        hits = sum(1 for kw in keywords if _keyword_in_text(kw.lower(), q))
        scores[domain] = hits / max(1, len(keywords)) ** 0.5
    return scores


async def _llm_fallback(question: str, lang: str) -> str | None:
    from app.services import llm_service  # lazy import to avoid circular dependency
    settings = get_settings()
    if not getattr(settings, "domain_router_llm_fallback_enabled", True):
        return None
    _valid_domains = "data_protection, labor, corporate, investment, credit_info, cross_domain, unknown"
    prompt = f"Classify this Tunisian legal question into exactly one domain: {_valid_domains}.\nQuestion: {question}\nAnswer with the domain name only."
    if lang == "fr":
        prompt = f"Classez cette question juridique tunisienne dans un seul domaine : {_valid_domains}.\nQuestion : {question}\nRépondez uniquement avec le nom du domaine."
    elif lang == "ar":
        prompt = f"صنف هذا السؤال القانوني التونسي في مجال واحد: {_valid_domains}.\nالسؤال: {question}\nأجب باسم المجال فقط."
    try:
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You only output one word: the domain name."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            base_url=settings.llm_base_url,
        )
        cleaned = (response or "").strip().lower()
        allowed = set(_DEFAULT_CONFIGS.keys())
        for token in cleaned.split():
            if token in allowed:
                return token
        return None
    except Exception as e:
        logger.warning("LLM domain fallback failed: %s", e)
        return None


async def route_question(
    question: str,
    lang: str,
    company_profile: dict | None = None,
    targeted_loi_code: str | None = None,
) -> RouteResult:
    """Route a legal question to the best domain pipeline.

    Returns a :class:`RouteResult` that supports tuple unpacking::

        domain, config = await route_question(question, lang)

    or richer access::

        result = await route_question(question, lang)
        print(result.confidence, result.explanation)
    """
    loi_to_domain: dict[str, str] = {"CS": "corporate", "CT": "labor", "INPDP": "data_protection", "INV": "investment", "BCT": "credit_info"}
    if targeted_loi_code:
        domain = loi_to_domain.get(targeted_loi_code.upper(), "unknown")
        config = _DEFAULT_CONFIGS.get(domain, _DEFAULT_CONFIGS["unknown"])
        return RouteResult(
            domain=domain,
            config=config,
            confidence=1.0,
            explanation=f"Explicit loi code override: {targeted_loi_code.upper()} -> {domain}",
        )

    # 1. Try the fine-tuned reasoning model first
    from app.services import reasoning_model_service
    pred_domain, conf = reasoning_model_service.classify_domain(question)
    if pred_domain and reasoning_model_service.is_confident(conf):
        config = _DEFAULT_CONFIGS.get(pred_domain, _DEFAULT_CONFIGS["unknown"])
        return RouteResult(
            domain=pred_domain,
            config=config,
            confidence=conf,
            explanation=f"Fine-tuned reasoning model prediction ({conf:.2f})",
        )

    scores = _lexical_scores(question, lang)
    if company_profile:
        profile_text = " ".join(filter(None, [
            str(company_profile.get("sector") or ""),
            str(company_profile.get("activities") or ""),
        ])).lower()
        profile_scores = _lexical_scores(profile_text, lang)
        for k, v in profile_scores.items():
            scores[k] = scores.get(k, 0.0) + v * 0.3

    if not scores:
        return RouteResult(
            domain="unknown",
            config=_DEFAULT_CONFIGS["unknown"],
            confidence=0.0,
            explanation="No lexical signals detected",
        )

    best_domain = max(scores, key=lambda k: scores[k])
    best_score = scores[best_domain]
    explanation_parts: list[str] = [f"Lexical top={best_domain} (score={best_score:.3f})"]

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_scores) >= 2:
        second_score = sorted_scores[1][1]
        if best_score > 0.0 and (best_score - second_score) / best_score < 0.25:
            explanation_parts.append(
                f"Cross-domain triggered: gap between {sorted_scores[0][0]} ({best_score:.3f}) "
                f"and {sorted_scores[1][0]} ({second_score:.3f}) < 25%"
            )
            best_domain = "cross_domain"

    threshold = float(os.getenv("DALEEL_DOMAIN_ROUTER_LEXICAL_THRESHOLD", "0.15"))
    if best_score < threshold:
        llm_domain = await _llm_fallback(question, lang)
        if llm_domain:
            explanation_parts.append(f"LLM fallback overrode to {llm_domain} (lexical score {best_score:.3f} < threshold {threshold})")
            best_domain = llm_domain
        else:
            explanation_parts.append(f"Lexical score {best_score:.3f} below threshold {threshold}; LLM fallback returned nothing")

    confidence = min(best_score / max(threshold, 0.01), 1.0)
    config = _DEFAULT_CONFIGS.get(best_domain, _DEFAULT_CONFIGS["unknown"])
    explanation = "; ".join(explanation_parts)
    logger.info("Domain routed: %s (score=%.3f, confidence=%.2f, lang=%s)", best_domain, best_score, confidence, lang)
    return RouteResult(
        domain=best_domain,
        config=config,
        confidence=round(confidence, 4),
        explanation=explanation,
    )


def get_domain_config(domain: str) -> DomainConfig:
    return _DEFAULT_CONFIGS.get(domain, _DEFAULT_CONFIGS["unknown"])
