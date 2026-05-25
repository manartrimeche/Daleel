"""
Service LLM pour le Q&A juridique avec une approche RAG.

Le flux est le suivant:
- récupérer les passages pertinents par recherche sémantique
- les envoyer comme contexte au modèle Ollama
- produire une reponse dans la langue de la question
"""

import re
import logging
import json
import time
import asyncio
import httpx
import unicodedata
from typing import Any, Optional

from app.config import get_settings
from app.processing.text_utils import detect_query_language as _detect_query_language
from app.processing.derja_normalizer import normalize_if_derja as _normalize_if_derja
from app.services import feedback_service, search_service
from app.services.domain_router import route_question
from app.services.llm_cache import llm_cache
from app.services.quality_guard_service import audit_and_guard
from app.services import graph_resolver, legal_retrieval_orchestrator

logger = logging.getLogger(__name__)
_reranking_service: Any | None = None


def _get_reranking_service():
    """Lazy import to keep app startup fast when cross-encoder is disabled."""
    global _reranking_service
    if _reranking_service is None:
        from app.services.reranker import RerankingService

        _reranking_service = RerankingService()
    return _reranking_service


# ─────────────────────────────────────────────────────────────
# Détection de la langue
# ─────────────────────────────────────────────────────────────




_LANG_LABELS = {
    "ar": ("Arabic / العربية", "يجب أن تكون إجابتك بالكامل باللغة العربية."),
    "fr": ("French / Français", "Vous devez répondre entièrement en français."),
    "en": ("English", "You must respond entirely in English."),
}

_MAX_CHUNK_TEXT_CHARS = 2000
_MAX_CONTEXT_CHARS = 10000
_ARTICLE_REF_RE = re.compile(r"(?:Article|Art\.?|article|الفصل|فصل|المادة)\s*([0-9]+)", re.IGNORECASE)
_ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
_LATIN_CHAR_RE = re.compile(r"[A-Za-z]")
_TOKEN_RE = re.compile(r"[\u0600-\u06FF\w]+", re.UNICODE)
_FR_UNIQUE_MARKERS = {
    "le", "la", "les", "des", "du", "une", "est", "sont", "avec", "pour", "dans", "aux", "vous", "votre", "ainsi", "donc", "aucun", "aucune",
}
_EN_UNIQUE_MARKERS = {
    "the", "and", "with", "without", "this", "that", "these", "those", "is", "are", "was", "were", "shall", "must", "may", "under", "where", "while",
}

# Latin words allowed inside Arabic legal text (abbreviations, legal terms, citations).
_ALLOWED_LATIN_IN_ARABIC: set[str] = {
    # Company types & legal abbreviations
    "sarl", "sa", "suarl", "sas", "gie",
    # Institutions & agencies
    "cnss", "smig", "inpdp", "apii", "bct", "src", "rgpd", "gdpr",
    # Citation markers
    "art", "source", "n", "pdf", "fr", "ar", "en",
    # Common in legal formatting
    "vs", "al", "no", "id",
}
_LATIN_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]+")


def _has_foreign_word_contamination(text: str, detected_lang: str) -> bool:
    """Detect non-abbreviation Latin words embedded in Arabic text.

    Returns True if the text contains Latin-script words ≥ 4 chars that
    are **not** in the allowlist (e.g. *trabajar*, *Magazine*, *Travail*).
    These indicate the LLM mixed languages in its output.
    """
    if detected_lang != "ar":
        return False
    for m in _LATIN_WORD_RE.finditer(text):
        word = m.group()
        if len(word) >= 4 and word.lower() not in _ALLOWED_LATIN_IN_ARABIC:
            return True
    return False


def _count_marker_hits(text: str, markers: set[str]) -> int:
    """Compte les occurrences de mots indicateurs dans un texte."""
    lowered = f" {(text or '').lower()} "
    hits = 0
    for marker in markers:
        hits += lowered.count(f" {marker} ")
    return hits

_STOPWORDS = {
    "fr": {
        "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "dans", "sur",
        "pour", "par", "avec", "sans", "que", "qui", "est", "sont", "au", "aux", "ce",
        "cette", "ces", "en", "a", "à", "d", "l", "il", "elle", "ils", "elles", "se",
    },
    "ar": {
        "في", "من", "على", "الى", "إلى", "عن", "مع", "هذا", "هذه", "ذلك", "تلك", "التي",
        "الذي", "أن", "إن", "كان", "كانت", "هو", "هي", "هم", "كما", "او", "أو", "لا", "ما",
    },
    "en": {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "without",
        "is", "are", "was", "were", "be", "as", "that", "this", "these", "those", "by", "from",
    },
}

_INTENT_HINTS = {
    "advice": {
        "fr": ["conseil", "conseils", "advice", "recommander", "recommandation"],
        "ar": ["نصيحة", "نصائح", "انصح", "توصية"],
        "en": ["advice", "recommend", "recommendation"],
    },
    "solution": {
        "fr": ["solution", "résoudre", "resoudre", "corriger", "plan d'action"],
        "ar": ["حل", "حلول", "معالجة", "خطة"],
        "en": ["solution", "solve", "fix", "action plan"],
    },
    "requirement_management": {
        "fr": [
            "exigence", "exigences", "conformité", "conformite", "obligation", "applicable",
            "création", "creation", "société", "societe", "conditions de création", "constitution société",
        ],
        "ar": [
            "متطلبات", "امتثال", "الالتزام", "واجب", "قابل للتطبيق",
            "شروط", "تأسيس", "شركة", "إنشاء شركة",
        ],
        "en": [
            "requirement", "requirements", "compliance", "obligation", "applicable",
            "company formation", "incorporation", "setup requirements",
        ],
    },
}

_DOC_FOCUSED_HINTS = {
    "fr": [
        "résumer", "resumer", "résumé", "resume", "synthèse", "synthese",
        "remplir", "comment remplir", "guider", "guide",
        "expliquer", "explication", "analyser", "analyse",
        "ce document", "le document", "ce contrat", "le contrat",
        "ce fichier", "le fichier", "ce texte", "le texte",
        "que dit", "que contient", "contenu", "clauses",
        "extraire", "identifier", "lister les",
    ],
    "ar": [
        "تلخيص", "ملخص", "شرح", "تحليل", "هذا المستند", "هذه الوثيقة",
        "هذا العقد", "ملء", "كيف أملأ", "محتوى", "بنود",
    ],
    "en": [
        "summarize", "summary", "fill", "how to fill", "guide",
        "explain", "analyze", "analysis", "this document", "the document",
        "this contract", "the contract", "this file", "the file",
        "what does", "what is", "clauses", "extract", "identify", "list the",
    ],
}

_DOC_FOCUSED_SYSTEM_PROMPTS = {
    "fr": (
        "Tu es un assistant juridique expert en droit tunisien. L'utilisateur t'a fourni un document. "
        "Ta tâche est de répondre à sa question en te basant EXCLUSIVEMENT sur le contenu du document fourni. "
        "Sois précis, structuré et professionnel. Si le document est un formulaire ou contrat, guide l'utilisateur "
        "étape par étape. Si c'est un texte juridique, identifie les points clés, les obligations et les droits. "
        "Réponds en français."
    ),
    "ar": (
        "أنت مساعد قانوني متخصص في القانون التونسي. قدّم المستخدم وثيقة. "
        "مهمتك هي الإجابة على سؤاله بناءً حصرياً على محتوى الوثيقة المقدمة. "
        "كن دقيقاً ومنظماً ومهنياً. أجب بالعربية."
    ),
    "en": (
        "You are a legal assistant specializing in Tunisian law. The user provided a document. "
        "Your task is to answer their question based EXCLUSIVELY on the provided document content. "
        "Be precise, structured, and professional. If the document is a form or contract, guide the user "
        "step by step. If it's a legal text, identify key points, obligations, and rights. "
        "Respond in English."
    ),
}


def _is_document_focused_question(question: str, lang: str) -> bool:
    q = question.lower()
    all_hints = []
    for hints in _DOC_FOCUSED_HINTS.values():
        all_hints.extend(hints)
    return any(h in q for h in all_hints)


_COMPANY_SCOPE_QUERY_HINTS = {
    "société",
    "societe",
    "commerciale",
    "immatriculation",
    "immatriculer",
    "registre de commerce",
    "constitution",
    "création",
    "creation",
    "sarl",
    "sa",
    "suarl",
    "تأسيس",
    "شركة",
    "الشركات",
    "السجل التجاري",
}


def _should_auto_scope_company_document(question: str) -> bool:
    q = (question or "").lower()
    return any(hint in q for hint in _COMPANY_SCOPE_QUERY_HINTS)


def _is_manager_obligations_query(question: str) -> bool:
    raw = str(question or "").lower()
    normalized = unicodedata.normalize("NFKD", str(question or ""))
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()
    has_manager = (
        any(k in normalized for k in ["gerant", "gerance", "dirigeant", "manager", "مدير", "التسيير"])
        or bool(re.search(r"g[ée\?]rant|g[ée\?]rance", raw))
    )
    has_duties = any(k in normalized for k in ["obligation", "obligations", "devoir", "devoirs", "responsabil", "واجب", "التزام", "مسؤول"])
    return has_manager and has_duties


def _augment_query_for_specific_legal_scope(question: str, lang: str = "fr") -> str:
    """Append disambiguation hints for known ambiguous legal intents."""
    if _is_manager_obligations_query(question):
        augmentations = {
            "ar": "صلاحيات المسير واجبات المسير التزامات المسير علاقات المسير مع الشركاء إدارة الشركة الفصل 112 الفصل 113",
            "fr": "pouvoirs du gérant SARL responsabilités du gérant rapports avec les associés gestion de la société article 112 article 113",
            "en": "manager powers SARL manager duties manager obligations shareholder relations company management article 112 article 113",
        }
        return (
            f"{question} {augmentations.get(lang, augmentations['fr'])}"
        )
    return question


async def _resolve_effective_document_id(
    db: Any,
    question: str,
    detected_lang: str,
    document_id: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    """
    Auto-select a relevant legal corpus when the question targets company law.

    This keeps backwards compatibility (explicit document_id always wins) while
    reducing cross-corpus noise for broad legal questions.
    """
    if document_id:
        return document_id, "explicit_document_id"

    if not _should_auto_scope_company_document(question):
        return None, None

    best_id: Optional[str] = None
    best_score = 0

    cursor = db["documents"].find(
        {"status": "ready"},
        {"_id": 0, "id": 1, "filename": 1, "language": 1},
    )
    async for doc in cursor:
        filename = str(doc.get("filename") or "").lower()
        doc_lang = str(doc.get("language") or "").lower()
        if not filename:
            continue

        score = 0
        if "code_societes_fr" in filename:
            score += 100
        if "societ" in filename:
            score += 15
        if "commercial" in filename:
            score += 5
        if "الشركات" in filename:
            score += 15
        if "مجلة الشركات" in filename:
            score += 30
        if filename.endswith(".jsonl"):
            score += 2

        # Prefer documents in the same language as the question when possible.
        if detected_lang in {"ar", "fr", "en"}:
            if doc_lang == detected_lang:
                score += 40
            elif doc_lang:
                score -= 10

        # Prefer known high-quality French company corpus for Arabic company queries,
        # then let generation translate to Arabic.
        if detected_lang == "ar" and "code_societes_fr" in filename:
            score += 120

        # Keep French corpus preference only when question is French.
        if detected_lang == "fr" and "code_societes_fr" in filename:
            score += 30

        if score > best_score:
            best_score = score
            best_id = str(doc.get("id") or "") or None

    if best_id is None:
        return None, None
    return best_id, "auto_company_corpus"


def _tokenize_for_rerank(text: str, lang: str) -> list[str]:
    """Découpe un texte en jetons utiles pour le reranking."""
    tokens = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    stopwords = _STOPWORDS.get(lang, set())
    filtered = [t for t in tokens if len(t) > 1 and t not in stopwords]
    return filtered


def _rerank_chunks_for_question(
    question: str,
    chunks: list[dict],
    lang: str,
    domain_config: Any | None = None,
) -> list[dict]:
    """
    Reclasse les chunks pour garder les plus utiles à la reponse.

    On combine le score vectoriel, le recouvrement lexical et un bonus
    quand les références d'articles correspondent à la question.
    """
    q_tokens = _tokenize_for_rerank(question, lang)
    q_token_set = set(q_tokens)
    question_lower = (question or "").lower()
    question_article_refs = set(_ARTICLE_REF_RE.findall(question or ""))

    generic_legal_tokens = {
        "article", "articles", "loi", "code", "droit", "juridique",
        "obligation", "obligations", "conditions", "procédure", "procedure",
        "formalités", "formalites", "création", "creation", "constitution",
        "société", "societe", "entreprise", "tunisie",
    }
    anchor_tokens = {t for t in q_token_set if t not in generic_legal_tokens and len(t) >= 4}

    def _scope_penalty(q: str, hay: str) -> float:
        penalty = 0.0
        if "sarl" in q:
            if "société en participation" in hay or "societe en participation" in hay:
                penalty += 0.15
            if "société en commandite" in hay or "societe en commandite" in hay:
                penalty += 0.10
            if "societe anonyme" in hay or "société anonyme" in hay:
                penalty += 0.08
            if "suarl" in hay and "sarl" not in hay:
                penalty += 0.05
            if re.search(r"\bsa\b", hay):
                penalty += 0.05

        # Avoid confusion between "obligations du gérant" and "obligations" as securities.
        if _is_manager_obligations_query(question):
            if any(k in hay for k in [
                "obligations sont des valeurs mobilières",
                "obligations sont des valeurs mobilieres",
                "valeurs mobilières",
                "valeurs mobilieres",
                "émission d'obligations",
                "emission d'obligations",
                "obligations sont émises",
                "obligations sont emises",
                "valeur nominale",
                "titre obligataire",
                "droit de créance",
                "droit de creance",
                "porteurs des obligations",
            ]):
                penalty += 0.15  # Reduced from 0.35

        return penalty

    # Domain-specific weights override defaults when provided
    vw = getattr(domain_config, "vector_weight", 0.56)
    lw = getattr(domain_config, "lexical_weight", 0.20)
    kw = getattr(domain_config, "keyword_weight", 0.14)
    aw = getattr(domain_config, "anchor_weight", 0.10)
    domain_boosts = getattr(domain_config, "lexical_boosts", None) or []

    reranked: list[tuple[float, dict]] = []
    for chunk in chunks:
        chunk_text = str(chunk.get("text") or "")
        chunk_section = str(chunk.get("section") or "")
        haystack = f"{chunk_section}\n{chunk_text}"

        c_tokens = _tokenize_for_rerank(haystack, lang)
        c_token_set = set(c_tokens)

        overlap = len(q_token_set.intersection(c_token_set)) / max(1, len(q_token_set))
        anchor_overlap = 0.0
        if anchor_tokens:
            anchor_overlap = len(anchor_tokens.intersection(c_token_set)) / max(1, len(anchor_tokens))
        vector_score = float(chunk.get("vector_score", chunk.get("score", 0.0)) or 0.0)
        keyword_seed = float(chunk.get("keyword_score", 0.0) or 0.0)

        phrase_boost = 0.0
        if len(question_lower) >= 12 and question_lower in haystack.lower():
            phrase_boost = 0.08

        ref_boost = 0.0
        if question_article_refs:
            chunk_refs = set(_ARTICLE_REF_RE.findall(haystack))
            if question_article_refs.intersection(chunk_refs):
                ref_boost = 0.15

        # Apply domain lexical boosts
        for pattern, boost in domain_boosts:
            if pattern.search(haystack):
                ref_boost += boost

        penalty = _scope_penalty(question_lower, haystack.lower())

        if anchor_tokens:
            if anchor_overlap == 0.0:
                penalty += 0.10
            else:
                penalty -= min(0.05, 0.03 * anchor_overlap)

        hybrid = (vw * vector_score) + (lw * overlap) + (kw * keyword_seed) + (aw * anchor_overlap) + phrase_boost + ref_boost - penalty
        hybrid = max(0.0, hybrid)  # Ensure non-negative score
        chunk_copy = dict(chunk)
        chunk_copy["hybrid_score"] = round(hybrid, 6)
        reranked.append((hybrid, chunk_copy))

    reranked.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in reranked]


def _detect_intent(question: str, lang: str) -> str:
    """Déduit l'intention de la question: analyse, conseil, solution, etc."""
    q = (question or "").lower()
    for intent, lang_map in _INTENT_HINTS.items():
        for hint in lang_map.get(lang, []) + lang_map.get("en", []):
            if hint in q:
                return intent
    return "analysis"


def _is_relevant_enough(question: str, chunks: list[dict], lang: str) -> bool:
    """Vérifie si les chunks récupérés sont assez pertinents pour répondre."""
    if not chunks:
        return False

    q_tokens = set(_tokenize_for_rerank(question, lang))
    if not q_tokens:
        return True

    strong_hits = 0
    for chunk in chunks[: min(5, len(chunks))]:
        text = f"{chunk.get('section') or ''} {chunk.get('text') or ''}"
        c_tokens = set(_tokenize_for_rerank(text, lang))
        overlap = len(q_tokens.intersection(c_tokens)) / max(1, len(q_tokens))
        hybrid = float(chunk.get("hybrid_score", chunk.get("score", 0.0)))
        if overlap >= 0.06 or hybrid >= 0.08:
            strong_hits += 1

    return strong_hits >= 1


def _rewrite_query_for_agentic(question: str, lang: str, intent: str) -> str:
    """Reformule la requête pour améliorer la recherche en mode agentique."""
    additions = {
        "fr": {
            "analysis": "Tunisie texte légal article applicable",
            "advice": "Tunisie conseil juridique étapes pratiques",
            "solution": "Tunisie solution juridique plan d'action conformité",
            "requirement_management": "Tunisie exigences obligations applicabilité conformité",
        },
        "ar": {
            "analysis": "تونس قانون فصل أحكام واجبة التطبيق",
            "advice": "تونس نصيحة قانونية خطوات عملية",
            "solution": "تونس حل قانوني خطة عمل امتثال",
            "requirement_management": "تونس متطلبات التزامات قابلية التطبيق امتثال",
        },
        "en": {
            "analysis": "Tunisia legal article applicable provision",
            "advice": "Tunisia legal advice practical steps",
            "solution": "Tunisia legal solution compliance action plan",
            "requirement_management": "Tunisia compliance requirements obligations applicability",
        },
    }
    suffix = additions.get(lang, additions["en"]).get(intent, additions.get(lang, additions["en"])["analysis"])
    return f"{question} {suffix}".strip()


def _intent_suffix_instruction(intent: str, lang: str) -> str:
    """Ajoute une consigne finale selon le type de question détecté."""
    if intent == "advice":
        if lang == "ar":
            return "أضف نصائح قانونية عملية وقابلة للتنفيذ مرتبة حسب الأولوية."
        if lang == "fr":
            return "Ajoutez des conseils juridiques pratiques et actionnables, priorisés."
        return "Add practical and prioritized legal advice."

    if intent == "solution":
        if lang == "ar":
            return "اقترح حلاً عملياً مع خطة تنفيذ خطوة بخطوة والمخاطر القانونية."
        if lang == "fr":
            return "Proposez une solution concrète avec plan d'exécution pas-à-pas et risques juridiques."
        return "Propose a concrete solution with a step-by-step execution plan and legal risks."

    if intent == "requirement_management":
        if lang == "ar":
            return "نظم الجواب كإدارة متطلبات: المتطلبات الواجبة، القابلية للتطبيق، الأولوية، والإجراءات التالية."
        if lang == "fr":
            return "Structurez la reponse en mode gestion des exigences: exigences applicables, priorité, risques, prochaines actions."
        return "Structure the answer for requirement management: applicable requirements, priority, risks, and next actions."

    return ""


def _route_config_for_intent(intent: str) -> dict:
    """Definit la stratégie d'exécution selon l'intention détectée."""
    policies = {
        "advice": {
            "route_decision": "guided_advice",
            "max_attempts": 2,
            "retrieval_multiplier": 3,
        },
        "solution": {
            "route_decision": "solution_planning",
            "max_attempts": 3,
            "retrieval_multiplier": 3,
        },
        "requirement_management": {
            "route_decision": "requirement_management",
            "max_attempts": 3,
            "retrieval_multiplier": 4,
        },
        "analysis": {
            "route_decision": "legal_analysis",
            "max_attempts": 2,
            "retrieval_multiplier": 3,
        },
    }
    return policies.get(intent, policies["analysis"])


def _parse_csv_keywords(value: str) -> list[str]:
    return [item.strip().lower() for item in (value or "").split(",") if item.strip()]


def _select_mode_for_auto(question: str, intent: str, settings) -> tuple[str, str]:
    """Choisit automatiquement entre le mode classique et le mode agentique."""
    q = (question or "").lower()

    if not getattr(settings, "auto_mode_enabled", True):
        return getattr(settings, "auto_mode_default", "classic"), "auto_mode_disabled"

    strong_agentic_terms = _parse_csv_keywords(getattr(settings, "auto_mode_agentic_keywords", ""))
    classic_terms = _parse_csv_keywords(getattr(settings, "auto_mode_classic_keywords", ""))
    length_threshold = int(getattr(settings, "auto_mode_length_threshold", 240) or 240)

    if intent in {"advice", "solution", "requirement_management"}:
        return "agentic", f"intent={intent}"
    if any(t in q for t in classic_terms):
        return "classic", "classic_keywords"
    if len(q) > length_threshold:
        return "agentic", "long_query"
    if any(t in q for t in strong_agentic_terms):
        return "agentic", "action_or_compliance_keywords"
    return getattr(settings, "auto_mode_default", "classic"), "direct_qa"


# ─────────────────────────────────────────────────────────────
# Mise en forme du contexte
# ─────────────────────────────────────────────────────────────

def _build_context_block(chunks: list[dict]) -> str:
    """Met en forme les chunks récupérés dans un bloc de contexte lisible."""
    blocks: list[str] = []
    total_chars = 0
    for i, c in enumerate(chunks, 1):
        meta_parts = []
        meta_parts.append(f"📄 Document: \"{c.get('filename', 'unknown')}\"")
        if c.get("page_number") is not None:
            meta_parts.append(f"📃 Page: {c['page_number']}")
        if c.get("section"):
            meta_parts.append(f"📌 Section: {c['section']}")
        if c.get("language"):
            lang_map = {"ar": "Arabic", "fr": "French", "en": "English"}
            meta_parts.append(f"🌐 Language: {lang_map.get(c['language'], c['language'])}")
        meta_parts.append(f"🎯 Relevance: {c.get('score', 0):.2%}")

        header = " | ".join(meta_parts)
        text = c.get("text", "").strip()
        if len(text) > _MAX_CHUNK_TEXT_CHARS:
            text = text[:_MAX_CHUNK_TEXT_CHARS].rstrip() + "…"

        block = (
            f"╔══ SOURCE [{i}] ══╗\n"
            f"{header}\n"
            f"───────────────────\n"
            f"{text}\n"
            f"╚══════════════════╝"
        )

        if total_chars + len(block) > _MAX_CONTEXT_CHARS:
            blocks.append("[Context truncated to keep the request within model limits]")
            break

        total_chars += len(block)
        blocks.append(block)
    return "\n\n".join(blocks)


def _build_source_metadata(chunks: list[dict]) -> list[dict]:
    """Extrait les métadonnées des sources pour la reponse API."""
    sources = []
    seen = set()
    for c in chunks:
        key = (c.get("document_id", ""), c.get("page_number"), c.get("section"))
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "document_id": c.get("document_id", ""),
            "filename": c.get("filename", ""),
            "page_number": c.get("page_number"),
            "section": c.get("section"),
            "language": c.get("language"),
            "relevance_score": round(c.get("score", 0), 4),
        })
    return sources


def _build_feedback_examples_block(examples: list[dict], detected_lang: str) -> str:
    """Format validated user corrections to guide future answers."""
    if not examples:
        return ""

    if detected_lang == "ar":
        header = "# أمثلة مصادق عليها من تصحيحات المستخدم"
        rule = "استخدم هذه الأمثلة كنمط إرشادي للأسلوب والدقة. لا تنسخ حرفيا إلا إذا كان نفس السؤال."
    elif detected_lang == "fr":
        header = "# Exemples validés issus des corrections utilisateur"
        rule = "Utilisez ces exemples comme guide de style et de précision. Ne copiez pas mot-à-mot sauf si la question est identique."
    else:
        header = "# Validated examples from user corrections"
        rule = "Use these as guidance for style and precision. Do not copy verbatim unless the question is essentially identical."

    blocks: list[str] = [header, rule]
    for idx, ex in enumerate(examples, 1):
        q = str(ex.get("question") or "").strip()
        a = str(ex.get("corrected_answer") or "").strip()
        if len(a) > 900:
            a = a[:900].rstrip() + "…"
        blocks.append(f"[Example {idx}] Q: {q}\n[Example {idx}] A: {a}")
    return "\n\n".join(blocks)


def _collect_supported_article_refs(chunks: list[dict]) -> set[str]:
    refs: set[str] = set()
    for chunk in chunks:
        section = str(chunk.get("section") or "")
        text = str(chunk.get("text") or "")
        for source_text in (section, text):
            for match in _ARTICLE_REF_RE.finditer(source_text):
                refs.add(match.group(1))
    return refs


def _extract_answer_article_refs(answer: str) -> set[str]:
    refs: set[str] = set()
    for match in _ARTICLE_REF_RE.finditer(answer):
        refs.add(match.group(1))
    return refs


def _strip_unsupported_article_refs(answer: str, unsupported_refs: set[str]) -> str:
    """Remove explicit unsupported article citations while preserving the rest of the answer."""
    if not answer or not unsupported_refs:
        return answer

    cleaned = answer
    for ref in sorted(unsupported_refs, key=lambda x: len(x), reverse=True):
        # French/English style citations
        cleaned = re.sub(
            rf"\b(?:l'|l')?(?:Article|Art\.?|article)\s*{re.escape(ref)}\b",
            "la législation en vigueur",
            cleaned,
            flags=re.IGNORECASE,
        )
        # Arabic style citations
        cleaned = re.sub(
            rf"\b(?:الفصل|فصل|المادة)\s*{re.escape(ref)}\b",
            "النص القانوني ذي الصلة",
            cleaned,
            flags=re.IGNORECASE,
        )
    return cleaned


def _validate_answer_grounding(
    answer: str,
    chunks: list[dict],
    detected_lang: str,
) -> dict:
    """Contrôle que la reponse cite seulement des éléments présents dans les sources."""
    supported_refs = _collect_supported_article_refs(chunks)
    answer_refs = {
        ref
        for ref in _extract_answer_article_refs(answer)
        if _is_valid_tunisian_article_number(ref)
    }
    verified_refs = answer_refs.intersection(supported_refs)
    unsupported_refs = answer_refs.difference(supported_refs)
    language_ok = _is_language_compliant(answer, detected_lang)

    return {
        "supported_refs": supported_refs,
        "answer_refs": answer_refs,
        "verified_refs": verified_refs,
        "unsupported_refs": unsupported_refs,
        "language_ok": language_ok,
        "should_reground": (not language_ok) or (bool(answer_refs) and not verified_refs),
    }


def _is_valid_tunisian_article_number(article_num: str) -> bool:
    """
    Validate if an article number is plausible for Tunisian legal codes.

    Rejects obviously wrong/hallucinated numbers:
    - Numbers <= 0 or > 2500 (beyond any Tunisian legal code)
    - Very high numbers (> 500) are scrutinized but Code Civil can go higher

    Known approximate ranges:
    - Code des Sociétés : 1-100
    - Code du Travail : 1-600
    - Code des Obligations : 1-700
    - Code du Commerce : 1-300
    - Code Civil : 1-2200

    This prevents hallucinations like 1874, 1923, 1924 which appear in model outputs
    but are not valid article numbers in modern Tunisian codes.
    """
    try:
        num = int(article_num)
    except (ValueError, TypeError):
        return False

    # Reject obviously invalid numbers
    if num <= 0:
        return False

    # Reject numbers beyond the scope of any Tunisian code
    # (Tunisian legislative articles don't go beyond ~2200)
    if num > 2500:
        return False

    # Very high numbers (> 500) are rare but possible (Code Civil)
    # However, they warrant extra scrutiny in RAG context.
    # For now, allow up to 2200 to cover Code Civil articles.
    if num > 2200:
        # Could be valid but very rare; mark as suspicious but allow
        # In strict mode, could set to num > 2000
        pass

    return True


def _is_language_compliant(answer: str, detected_lang: str) -> bool:
    arabic_chars = len(_ARABIC_CHAR_RE.findall(answer))
    latin_chars = len(_LATIN_CHAR_RE.findall(answer))
    total_letters = arabic_chars + latin_chars

    if total_letters == 0:
        return False

    if detected_lang == "ar":
        # Arabic answers should stay predominantly Arabic even when short.
        if arabic_chars < max(8, int(total_letters * 0.5)):
            return False
        # Reject if foreign words snuck in (e.g. "trabajar", "Magazine du Travail")
        if _has_foreign_word_contamination(answer, "ar"):
            return False
        return True

    if detected_lang == "fr":
        # French answers may include a few Arabic legal terms, but should stay mostly Latin.
        base_ok = (
            latin_chars >= max(20, int(total_letters * 0.6))
            and arabic_chars <= max(15, latin_chars // 4)
        )
        if not base_ok:
            return False

        fr_hits = _count_marker_hits(answer, _FR_UNIQUE_MARKERS)
        en_hits = _count_marker_hits(answer, _EN_UNIQUE_MARKERS)

        # Reject clearly English-dominant answers.
        if en_hits >= 6 and en_hits > fr_hits:
            return False
        return fr_hits >= 3 or fr_hits >= en_hits

    if detected_lang == "en":
        # English answers are expected to be mostly Latin script.
        if latin_chars < max(15, int(total_letters * 0.6)):
            return False

        en_hits = _count_marker_hits(answer, _EN_UNIQUE_MARKERS)
        fr_hits = _count_marker_hits(answer, _FR_UNIQUE_MARKERS)
        if fr_hits >= 6 and fr_hits > en_hits:
            return False
        return en_hits >= 3 or en_hits >= fr_hits

    return latin_chars >= arabic_chars


def _is_sentence_usable_for_fallback(sentence: str, detected_lang: str) -> bool:
    """Reject noisy OCR-like lines before deterministic synthesis."""
    s = (sentence or "").strip()
    if len(s) < 20:
        return False

    # Remove obvious scanner/page noise lines.
    if re.fullmatch(r"[\d\s\-_/\\.,;:()\[\]{}'\"%]+", s):
        return False

    tokens = [t for t in re.split(r"\s+", s) if t]
    if len(tokens) < 4:
        return False

    total_chars = len(s)
    digit_chars = sum(ch.isdigit() for ch in s)
    if total_chars > 0 and (digit_chars / total_chars) > 0.25:
        return False

    long_tokens = sum(1 for t in tokens if len(t) > 24)
    if len(tokens) > 0 and (long_tokens / len(tokens)) > 0.2:
        return False

    arabic_chars = len(_ARABIC_CHAR_RE.findall(s))
    latin_chars = len(_LATIN_CHAR_RE.findall(s))
    letters = arabic_chars + latin_chars
    if letters < 12:
        return False

    # Keep script-consistent lines for the requested language.
    if detected_lang == "ar":
        if arabic_chars < int(letters * 0.55):
            return False

        arabic_tokens = [t for t in tokens if _ARABIC_CHAR_RE.search(t)]
        if len(arabic_tokens) >= 4:
            starts_with_al = sum(1 for t in arabic_tokens if t.startswith("ال"))
            ends_with_la = sum(1 for t in arabic_tokens if t.endswith("لا"))
            starts_with_ta_marbuta = sum(1 for t in arabic_tokens if t.startswith("Ø©"))

            # Natural Arabic legal lines usually contain at least a few "الـ" words.
            if len(arabic_tokens) >= 8 and starts_with_al == 0:
                return False

            # Reversed Arabic OCR often flips "الـ" into token suffix "ـلا".
            if ends_with_la >= 4 and ends_with_la > (starts_with_al * 2 + 1):
                return False

            # Excessive words starting with "Ø©" is another strong reverse-noise signal.
            if (starts_with_ta_marbuta / max(1, len(arabic_tokens))) > 0.22:
                return False

        return True
    if detected_lang in {"fr", "en"}:
        return latin_chars >= int(letters * 0.55)
    return True


def _reverse_arabic_token(token: str) -> str:
    """Reverse letters inside one Arabic token while keeping punctuation boundaries."""
    m = re.match(r"^([^\u0600-\u06FF]*)([\u0600-\u06FF]+)([^\u0600-\u06FF]*)$", token)
    if not m:
        return token
    prefix, core, suffix = m.groups()
    return f"{prefix}{core[::-1]}{suffix}"


def _normalize_reversed_arabic_sentence(sentence: str) -> str:
    """Heuristically fix OCR lines where Arabic tokens are character-reversed."""
    s = (sentence or "").strip()
    if not s:
        return s

    tokens = [t for t in re.split(r"\s+", s) if t]
    arabic_tokens = [t for t in tokens if _ARABIC_CHAR_RE.search(t)]
    if len(arabic_tokens) < 3:
        return s

    starts_with_al = sum(1 for t in arabic_tokens if re.match(r"^[^\u0600-\u06FF]*ال", t))
    ends_with_la = sum(1 for t in arabic_tokens if re.search(r"لا[^\u0600-\u06FF]*$", t))

    # Reversed OCR often produces many words ending in "لا" and very few starting with "ال".
    looks_reversed = ends_with_la >= 2 and ends_with_la > starts_with_al
    if not looks_reversed:
        return s

    fixed_tokens = [_reverse_arabic_token(t) for t in tokens]
    return " ".join(fixed_tokens)


def _extract_arabic_rescue_lines(chunks: list[dict], limit: int = 10) -> list[str]:
    """Best-effort extraction for noisy Arabic OCR when strict filtering returns nothing."""
    lines: list[str] = []
    for chunk in chunks:
        raw_text = str(chunk.get("text") or "").replace("\n", " ")
        normalized = _normalize_reversed_arabic_sentence(raw_text)
        candidates = re.split(r"(?<=[\.!؟؛;])\s+|\s{2,}", normalized)
        for cand in candidates:
            s = re.sub(r"\s+", " ", cand).strip()
            if len(s) < 35:
                continue
            arabic_chars = len(_ARABIC_CHAR_RE.findall(s))
            digit_chars = sum(ch.isdigit() for ch in s)
            if arabic_chars < 12:
                continue
            if len(s) > 0 and (digit_chars / len(s)) > 0.35:
                continue
            lines.append(s)
            if len(lines) >= (limit * 3):
                break
        if len(lines) >= (limit * 3):
            break

    # Stable dedup with light normalization.
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        key = re.sub(r"\s+", " ", line).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(line)
        if len(out) >= limit:
            break
    return out


def _extract_cross_language_legal_lines(chunks: list[dict], limit: int = 8) -> list[str]:
    """Extract non-Arabic legal-looking lines as a last resort for Arabic responses."""
    lines: list[str] = []
    for chunk in chunks:
        text = str(chunk.get("text") or "").replace("\n", " ")
        candidates = re.split(r"(?<=[\.!?;])\s+|\s{2,}", text)
        for cand in candidates:
            s = re.sub(r"\s+", " ", cand).strip()
            if len(s) < 40:
                continue
            arabic_chars = len(_ARABIC_CHAR_RE.findall(s))
            latin_chars = len(_LATIN_CHAR_RE.findall(s))
            if arabic_chars > latin_chars:
                continue
            if latin_chars < 20:
                continue
            lines.append(s)
            if len(lines) >= limit:
                break
        if len(lines) >= limit:
            break

    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        key = re.sub(r"\s+", " ", line).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(line)
        if len(out) >= limit:
            break
    return out


def _strip_non_compliant_lines(answer: str, detected_lang: str) -> str:
    """
    Enforce stricter output language consistency at line level.

    This is a final guardrail to avoid mixed-language drift in the returned
    answer when the user asked in Arabic or French.
    """
    lines = [line.rstrip() for line in (answer or "").splitlines()]
    if not lines:
        return answer

    cleaned: list[str] = []
    for line in lines:
        text = line.strip()
        if not text:
            cleaned.append(line)
            continue

        arabic_chars = len(_ARABIC_CHAR_RE.findall(text))
        latin_chars = len(_LATIN_CHAR_RE.findall(text))
        total_letters = arabic_chars + latin_chars

        # Keep mostly numeric/symbol lines (citations, bullets, separators).
        if total_letters < 6:
            cleaned.append(line)
            continue

        if detected_lang == "ar":
            # Keep lines that are clearly Arabic-dominant AND free of foreign words.
            if arabic_chars >= max(6, int(total_letters * 0.55)):
                if not _has_foreign_word_contamination(text, "ar"):
                    cleaned.append(line)
            continue

        if detected_lang == "fr":
            # Keep French/Latin lines and reject clearly Arabic-dominant lines.
            if latin_chars >= max(8, int(total_letters * 0.6)) and arabic_chars <= max(8, latin_chars // 3):
                cleaned.append(line)
            continue

        # English/default: keep lines that are mostly Latin script.
        if latin_chars >= max(8, int(total_letters * 0.6)):
            cleaned.append(line)

    # Collapse excess blank lines after filtering.
    filtered = "\n".join(cleaned)
    filtered = re.sub(r"\n{3,}", "\n\n", filtered).strip()
    return filtered


def _contains_unreliable_legal_placeholders(answer: str) -> bool:
    """Detect templated legal placeholders that indicate low-grounding hallucinations."""
    a = (answer or "").lower()
    if not a:
        return False

    placeholder_patterns = [
        r"disposition\s+l[ée]gale\s+pertinente(?:\s*[-:]?\s*\d+)?",
        r"disposition\s+juridique\s+pertinente(?:\s*[-:]?\s*\d+)?",
        r"legal\s+provision\s+placeholder",
    ]
    for pattern in placeholder_patterns:
        if re.search(pattern, a, flags=re.IGNORECASE):
            return True

    # Overuse of this replacement phrase is a strong signal that substantive
    # legal citations were not grounded and got mechanically rewritten.
    a_ascii = unicodedata.normalize("NFKD", a)
    a_ascii = "".join(ch for ch in a_ascii if not unicodedata.combining(ch))
    if a.count("la législation en vigueur") >= 2 or a_ascii.count("la legislation en vigueur") >= 2:
        return True

    # Explicitly admitting missing support while still asserting legal rules.
    unsupported_admission_patterns = [
        r"bien qu['’]il ne soit pas explicitement mentionn",
        r"not explicitly mentioned in the retrieved",
        r"غير مذكور صراحة في المقاطع",
    ]
    for pattern in unsupported_admission_patterns:
        if re.search(pattern, a, flags=re.IGNORECASE):
            return True

    return False


def _looks_structured_by_language(answer: str, detected_lang: str) -> bool:
    """Check whether an answer already follows the enriched sectioned format."""
    text = (answer or "").lower()
    if not text:
        return False

    if detected_lang == "ar":
        markers = ["- الإطار القانوني", "- التحليل المفصل", "- الشروط والمتطلبات", "- الإجراءات المتبعة"]
    elif detected_lang == "fr":
        markers = ["- cadre juridique", "- analyse détaillée", "- conditions et exigences", "- procédure à suivre"]
    else:
        markers = ["- applicable legal framework", "- detailed analysis", "- conditions and requirements", "- procedure"]

    hits = sum(1 for marker in markers if marker.lower() in text)
    return hits >= 3


def _apply_final_language_guardrail(
    *,
    answer: str,
    detected_lang: str,
    question: str,
    chunks: list[dict],
    strict_grounded_only: bool,
) -> str:
    """Apply strict language filtering and safe fallback when needed."""
    cleaned = _strip_non_compliant_lines(answer, detected_lang)
    has_placeholder_hallucination = _contains_unreliable_legal_placeholders(cleaned)
    structured = _looks_structured_by_language(cleaned, detected_lang)

    if cleaned and _is_language_compliant(cleaned, detected_lang) and not has_placeholder_hallucination and structured:
        return cleaned

    if not strict_grounded_only:
        language_ok = cleaned and _is_language_compliant(cleaned, detected_lang)
        if language_ok and not has_placeholder_hallucination:
            if not structured:
                logger.warning(
                    "Final guardrail kept an unstructured answer without deterministic grounding because strict mode is disabled (detected_lang=%s).",
                    detected_lang,
                )
            return cleaned
        # Language is completely wrong (e.g. English for French) or
        # placeholder hallucination — fall through to grounded synthesis
        # even in non-strict mode.
        logger.warning(
            "Final guardrail: language_ok=%s, has_placeholder=%s, strict=%s (detected_lang=%s). "
            "Falling back to deterministic grounded synthesis.",
            language_ok, has_placeholder_hallucination, strict_grounded_only, detected_lang,
        )

    if not structured and cleaned and _is_language_compliant(cleaned, detected_lang) and not has_placeholder_hallucination:
        logger.warning(
            "Final guardrail normalized an unstructured answer into the enriched grounded format (detected_lang=%s).",
            detected_lang,
        )
    elif has_placeholder_hallucination:
        logger.warning(
            "Final guardrail triggered on placeholder hallucination (detected_lang=%s). Falling back to deterministic grounded synthesis.",
            detected_lang,
        )
    else:
        logger.warning(
            "Final language guardrail triggered (detected_lang=%s). Falling back to deterministic grounded synthesis.",
            detected_lang,
        )

    supported_refs = _collect_supported_article_refs(chunks)
    return _build_grounded_synthesis_from_chunks(
        detected_lang,
        question,
        chunks,
        set(),
        supported_refs,
    )


def _looks_like_prompt_leak(answer: str) -> bool:
    """Detect when the model outputs policy/system-prompt content instead of legal analysis."""
    a = (answer or "").lower()
    if not a:
        return False

    english_markers = [
        "identity & role",
        "critical language rule",
        "cross-language sources",
        "expert behavior",
        "knowledge boundaries",
        "minimum response length",
    ]
    arabic_markers = [
        "يجب أن تكون إجابتك بالكامل",
        "الحد الأدنى لطول الإجابة",
        "حدود المعرفة",
        "الإطار القانوني",
    ]

    en_hits = sum(1 for m in english_markers if m in a)
    ar_hits = sum(1 for m in arabic_markers if m in a)

    # Additional strong signal observed in leaked prompt translations.
    daleel_meta = ("دليل" in a and "25" in a and ("الخبر" in a or "سنة" in a or "عام" in a))

    return (en_hits >= 2) or (ar_hits >= 2 and daleel_meta) or (en_hits >= 1 and daleel_meta)


def _build_grounded_fallback(detected_lang: str, chunks: list[dict], answer_refs: set[str], supported_refs: set[str]) -> str:
    """Construit un message de repli quand la reponse n'est pas assez fondée."""
    verified_refs = sorted(answer_refs.intersection(supported_refs), key=lambda x: int(x))
    missing_refs = sorted(answer_refs.difference(supported_refs), key=lambda x: int(x) if x.isdigit() else x)

    if detected_lang == "ar":
        base = ["المقاطع المسترجعة لا تؤكد جميع الإحالات المذكورة في الجواب السابق."]
        if verified_refs:
            base.append("الفصول المؤكدة في المصادر هي: " + ", ".join(f"الفصل {ref}" for ref in verified_refs) + ".")
        if missing_refs:
            base.append("أما الإحالات التالية فلا أستطيع تأكيدها من المقاطع المسترجعة: " + ", ".join(f"الفصل {ref}" for ref in missing_refs) + ".")
        base.append("إذا أردت، أستطيع الآن أن أقدّم لك خلاصة قانونية دقيقة ومقيدة فقط بالمصادر المؤكدة في الملف.")
        return " ".join(base)

    if detected_lang == "fr":
        base = ["Les extraits récupérés ne confirment pas toutes les références citées dans la reponse précédente."]
        if verified_refs:
            base.append("Les articles confirmés dans les sources sont : " + ", ".join(f"Article {ref}" for ref in verified_refs) + ".")
        if missing_refs:
            base.append("Je ne peux pas confirmer les références suivantes à partir des extraits récupérés : " + ", ".join(f"Article {ref}" for ref in missing_refs) + ".")
        base.append("Si vous voulez, je peux reformuler une synthèse stricte et limitée uniquement aux sources vérifiées.")
        return " ".join(base)

    base = ["The retrieved excerpts do not confirm all of the references used in the previous answer."]
    if verified_refs:
        base.append("Confirmed articles in the sources are: " + ", ".join(f"Article {ref}" for ref in verified_refs) + ".")
    if missing_refs:
        base.append("I cannot confirm the following references from the retrieved excerpts: " + ", ".join(f"Article {ref}" for ref in missing_refs) + ".")
    base.append("If you want, I can rewrite the answer strictly limited to the verified excerpts.")
    return " ".join(base)


def _build_grounded_synthesis_from_chunks(
    detected_lang: str,
    question: str,
    chunks: list[dict],
    answer_refs: set[str],
    supported_refs: set[str],
) -> str:
    """Reconstruit une reponse directement à partir des extraits récupérés."""
    # Multi-language keyword buckets to extract useful lines directly from sources.
    prohibition_keys = [
        "interdit", "interdite", "interdits", "prohibition", "prohibe",
        "forbidden", "must not", "cannot", "ne peut", "لا يجوز", "ممنوع", "يحجر",
    ]
    sanction_keys = [
        "sanction", "sanctions", "amende", "peine", "penalite", "penalty", "fine",
        "punishable", "liable", "مسؤولية", "عقوبة", "غرامة", "جزاء",
    ]
    procedure_keys = [
        "immatriculation", "immatriculer", "registre de commerce", "inscription",
        "publication", "journal officiel", "formalités", "formalite", "constitution",
        "création", "creation", "dépôt", "depot", "statuts", "greffe",
        "تأسيس", "السجل التجاري", "ترسيم", "إشهار", "نشر",
    ]
    manager_keys = [
        "gérant", "gerant", "gérance", "gerance", "dirigeant", "gestion",
        "pouvoirs des gérants", "rapports avec les associés", "المسير", "مدير", "التسيير",
    ]
    bond_keys = [
        "obligations sont des valeurs mobilières", "valeur nominale", "émission", "droit de créance",
        "obligation ne peut être inférieure", "titre obligataire", "سندات",
    ]

    want_manager = _is_manager_obligations_query(question)

    prohibition_lines: list[str] = []
    sanction_lines: list[str] = []
    procedure_lines: list[str] = []
    manager_lines: list[str] = []
    generic_lines: list[str] = []

    for chunk in chunks:
        text = str(chunk.get("text") or "").replace("\n", " ")
        # Lightweight sentence split to keep grounded snippets readable.
        sentences = re.split(r"(?<=[\.!ØŸ!;])\s+", text)
        for sentence in sentences:
            s = sentence.strip()
            if detected_lang == "ar":
                s = _normalize_reversed_arabic_sentence(s)
            if len(s) < 20:
                continue
            if not _is_sentence_usable_for_fallback(s, detected_lang):
                continue
            lower = s.lower()
            if want_manager and any(k in lower for k in bond_keys):
                continue
            if len(prohibition_lines) < 6 and any(k in lower for k in prohibition_keys):
                prohibition_lines.append(s)
            if len(sanction_lines) < 6 and any(k in lower for k in sanction_keys):
                sanction_lines.append(s)
            if len(procedure_lines) < 8 and any(k in lower for k in procedure_keys):
                procedure_lines.append(s)
            if len(manager_lines) < 8 and any(k in lower for k in manager_keys):
                manager_lines.append(s)
            if len(generic_lines) < 10:
                generic_lines.append(s)

    # Keep stable order while deduplicating repeated snippets across chunks.
    def _dedup(lines: list[str], limit: int) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in lines:
            key = re.sub(r"\s+", " ", item).strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(item)
            if len(out) >= limit:
                break
        return out

    prohibition_lines = _dedup(prohibition_lines, 6)
    sanction_lines = _dedup(sanction_lines, 6)
    procedure_lines = _dedup(procedure_lines, 8)
    manager_lines = _dedup(manager_lines, 8)
    generic_lines = _dedup(generic_lines, 10)

    # Arabic OCR rescue: if strict extraction produced almost nothing,
    # recover usable lines from noisy/reversed chunks.
    if detected_lang == "ar" and not (prohibition_lines or sanction_lines or procedure_lines or manager_lines or generic_lines):
        rescue_lines = _extract_arabic_rescue_lines(chunks, limit=10)
        if rescue_lines:
            generic_lines = _dedup(rescue_lines, 10)
            procedure_keywords = ["تأسيس", "شركة", "تسجيل", "ترسيم", "السجل", "إشهار", "نشر", "عقد", "شروط", "يجب", "يلزم"]
            rescued_procedure = [
                line for line in rescue_lines
                if any(keyword in line for keyword in procedure_keywords)
            ]
            procedure_lines = _dedup(rescued_procedure, 8)

    if detected_lang == "ar" and not (prohibition_lines or sanction_lines or procedure_lines or manager_lines or generic_lines):
        cross_lang_lines = _extract_cross_language_legal_lines(chunks, limit=8)
        if cross_lang_lines:
            generic_lines = _dedup([f"مقتطف من المصدر الأصلي: {line}" for line in cross_lang_lines], 8)
            procedure_lines = _dedup(generic_lines[:4], 4)

    verified_refs = sorted(answer_refs.intersection(supported_refs), key=lambda x: int(x))

    def _pick_lines(source_lines: list[str], keywords: list[str], limit: int = 4) -> list[str]:
        out: list[str] = []
        for line in source_lines:
            lowered = line.lower()
            if any(keyword in lowered for keyword in keywords):
                out.append(line)
            if len(out) >= limit:
                break
        return out

    def _line_key(line: str) -> str:
        text = re.sub(r"\s+", " ", (line or "")).strip().lower()
        if not text:
            return ""

        article_match = re.search(r"\b(article|الفصل)\s*(\d{1,4})\b", text)
        article_sig = f"art:{article_match.group(2)}" if article_match else ""

        alnum_text = re.sub(r"[^\w\s]", " ", text)
        alnum_text = re.sub(r"\s+", " ", alnum_text).strip()
        prefix_words = " ".join(alnum_text.split()[:14])

        if article_sig:
            return f"{article_sig}|{prefix_words[:80]}"
        return prefix_words[:80]

    def _take_unique_lines(
        primary: list[str],
        secondary: list[str],
        *,
        limit: int,
        used_keys: set[str],
    ) -> list[str]:
        selected: list[str] = []
        for item in (primary + secondary):
            key = _line_key(item)
            if not key or key in used_keys:
                continue
            used_keys.add(key)
            selected.append(item)
            if len(selected) >= limit:
                break
        return selected

    _SYNTHESIS_PARAMS = {
        "ar": {
            "fw_dedup": 6, "limit": 4,
            "detail_kw": ["ال", "gérant", "gerant", "المسير", "responsab", "pouvoir", "statut", "tiers"],
            "cond_kw": ["condition", "sous réserve", "sauf", "statuts", "doit", "يجب"],
            "proc_extra_kw": None, "attn_extra_kw": None,
            "detail_with_sanctions": False,
            "intro": "اعتمادا فقط على المقاطع المسترجعة، هذه خلاصة منضبطة ومهيكلة:",
            "sec": ["الإطار القانوني:", "التحليل المفصل:", "الشروط والمتطلبات:", "الإجراءات المتبعة:", "نقاط مهمة:", "ما لم تؤكده المقاطع:"],
            "ref_fmt": "الفصل {}", "refs_pre": "الإحالات المؤكدة في المصادر: ",
            "empty": [
                "لا توجد إحالات كافية لتحديد إطار قانوني إضافي بشكل مؤكد.",
                "لا تتوفر فقرات كافية لتحليل مفصل إضافي.",
                "الشروط أو المتطلبات غير مذكورة بوضوح في المقاطع المتاحة.",
                "لا توجد نقاط تحذير إضافية مؤكدة في المقاطع المتاحة.",
            ],
            "unconfirmed": "المقاطع المتاحة لا تكفي لتأكيد كل الجوانب التفصيلية، لذلك تم الاكتفاء بما هو مثبت فقط.",
        },
        "fr": {
            "fw_dedup": 8, "limit": 5,
            "detail_kw": ["gérant", "gerant", "gérance", "gerance", "responsab", "pouvoir", "tiers", "statut", "objet social"],
            "cond_kw": ["condition", "sous réserve", "sauf", "statuts", "doit", "obligation", "limite", "possible"],
            "proc_extra_kw": ["immatric", "inscription", "publication", "registre", "dépôt", "statuts", "greffe"],
            "attn_extra_kw": ["inopposable", "responsab", "infraction", "faute", "amende", "peine", "preuve"],
            "detail_with_sanctions": True,
            "intro": "Sur la base exclusive des extraits récupérés, voici une synthèse stricte et structurée :",
            "sec": ["Cadre juridique :", "Analyse détaillée :", "Conditions et exigences :", "Procédure à suivre :", "Points d'attention :", "Ce qui n'est pas confirmé :"],
            "ref_fmt": "Article {}", "refs_pre": "Articles confirmés dans les sources : ",
            "empty": [
                "Les extraits ne suffisent pas à confirmer davantage de dispositions.",
                "Les extraits disponibles ne permettent pas un développement plus détaillé.",
                "Les conditions précises ne sont pas explicitement confirmées dans les passages fournis.",
                "Aucun point d'attention supplémentaire n'est confirmé par les extraits.",
            ],
            "unconfirmed": "Les extraits disponibles ne couvrent pas nécessairement tous les cas pratiques; les éléments non confirmés ont été volontairement omis.",
        },
        "en": {
            "fw_dedup": 8, "limit": 5,
            "detail_kw": ["manager", "gérant", "gerant", "responsab", "power", "tiers", "statut", "object", "obligation"],
            "cond_kw": ["condition", "subject to", "unless", "statut", "must", "obligation", "limit"],
            "proc_extra_kw": ["registration", "filing", "publication", "registry", "statute"],
            "attn_extra_kw": ["liable", "penalty", "fine", "invalid", "cannot", "must not"],
            "detail_with_sanctions": True,
            "intro": "Based strictly on the retrieved excerpts, here is a grounded synthesis without unverified citations:",
            "sec": ["Applicable legal framework:", "Detailed analysis:", "Conditions and requirements:", "Procedure:", "Important warnings:", "What is not confirmed:"],
            "ref_fmt": "Article {}", "refs_pre": "Confirmed references: ",
            "empty": [
                "The excerpts do not confirm more legal provisions.",
                "The retrieved excerpts do not support a more detailed analysis.",
                "Specific conditions are not explicitly confirmed in the retrieved passages.",
                "No additional warnings are explicitly confirmed in the excerpts.",
            ],
            "unconfirmed": "Any point not present in the retrieved excerpts was intentionally omitted.",
        },
    }

    p = _SYNTHESIS_PARAMS.get(detected_lang, _SYNTHESIS_PARAMS["en"])
    lim, fw_d = p["limit"], p["fw_dedup"]

    framework_lines = _dedup(manager_lines + procedure_lines + prohibition_lines + sanction_lines + generic_lines, fw_d)
    detail_src = (framework_lines + sanction_lines) if p["detail_with_sanctions"] else framework_lines
    detail_candidates = _pick_lines(detail_src, p["detail_kw"], fw_d)
    condition_candidates = _pick_lines(procedure_lines + manager_lines + generic_lines, p["cond_kw"], fw_d)
    proc_extra = _pick_lines(generic_lines, p["proc_extra_kw"], 5) if p["proc_extra_kw"] else []
    attn_extra = _pick_lines(generic_lines, p["attn_extra_kw"], 5) if p["attn_extra_kw"] else []
    procedure_candidates = _dedup(procedure_lines + proc_extra, fw_d)
    attention_candidates = _dedup(prohibition_lines + sanction_lines + attn_extra, fw_d)

    used_section_lines: set[str] = set()
    framework_pick = _take_unique_lines(framework_lines[:lim], generic_lines, limit=lim, used_keys=used_section_lines)
    detail_lines = _take_unique_lines(detail_candidates, manager_lines + generic_lines, limit=lim, used_keys=used_section_lines)
    condition_lines = _take_unique_lines(condition_candidates, procedure_lines + generic_lines, limit=lim, used_keys=used_section_lines)
    procedure_pick = _take_unique_lines(procedure_candidates, generic_lines, limit=lim, used_keys=used_section_lines)
    attention_lines = _take_unique_lines(attention_candidates, generic_lines, limit=lim, used_keys=used_section_lines)

    sec = p["sec"]
    lines = [p["intro"]]
    lines.append(f"- {sec[0]}")
    if verified_refs:
        lines.append("  - " + p["refs_pre"] + ", ".join(p["ref_fmt"].format(r) for r in verified_refs) + ".")
    lines.extend([f"  - {x}" for x in framework_pick] or [f"  - {p['empty'][0]}"])
    lines.append(f"- {sec[1]}")
    lines.extend([f"  - {x}" for x in detail_lines] or [f"  - {p['empty'][1]}"])
    lines.append(f"- {sec[2]}")
    lines.extend([f"  - {x}" for x in condition_lines] or [f"  - {p['empty'][2]}"])
    if procedure_pick:
        lines.append(f"- {sec[3]}")
        lines.extend([f"  - {x}" for x in procedure_pick])
    lines.append(f"- {sec[4]}")
    lines.extend([f"  - {x}" for x in attention_lines] or [f"  - {p['empty'][3]}"])
    lines.append(f"- {sec[5]}")
    lines.append(f"  - {p['unconfirmed']}")
    return "\n".join(lines)


async def _rewrite_answer_grounded(
    *,
    settings,
    model_name: str,
    detected_lang: str,
    lang_name: str,
    lang_instruction: str,
    context_message: str,
    question: str,
    initial_draft: str = "",
) -> str:
    """Relance la génération avec une consigne plus stricte et plus fidèle aux sources.

    When *initial_draft* is provided the rewrite prompt shows the draft
    explicitly so the model can identify and strip unsupported references.
    Omit *initial_draft* for prompt-leak recovery to avoid feeding leaked
    content back to the model.
    """
    messages = _build_rewrite_messages(
        detected_lang=detected_lang,
        question=question,
        context_message=context_message,
        initial_draft=initial_draft,
    )

    return await _call_ollama(
        model=model_name,
        messages=messages,
        temperature=0.05,
        base_url=settings.llm_base_url,
    )


# ─────────────────────────────────────────────────────────────
# Modèles de prompts
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = {
    "ar": """# الهوية والدور
أنت **دليل** (Daleel)، مستشار قانوني تونسي متمرس متخصص في القانون التونسي.
أنت ترافق الشركات والأفراد في فهم وتطبيق القانون التونسي.
لست محرك بحث — أنت تستمع، تحلل، وتنصح كمحترف حقيقي.

# مصادرك المرجعية
- مجلة الشغل (قانون العمل التونسي)
- مجلة الشركات التجارية
- القانون عدد 63 لسنة 2004 المتعلق بحماية المعطيات الشخصية

# قاعدة اللغة
- السؤال مكتوب بالعربية → أجب بالعربية بالكامل.
- استخدم مراجع مجلة الشغل ومجلة الشركات التجارية بالعربية.
- يُسمح بالمصطلحات القانونية اللاتينية عند الضرورة.

# التعامل مع المصادر بلغات مختلفة
- قد تكون الوثائق المصدرية بلغة مختلفة (مثلاً بالفرنسية).
- يجب قراءة وفهم النصوص بأي لغة كانت، لكن **ترجمة وتحليل المحتوى بالعربية فقط**.

# أسلوب الرد
- تحدث كمستشار بشري، دافئ ومحترف.
- أعد صياغة مشكلة المستخدم دائماً قبل الإجابة.
- استشهد دائماً بالفصل الدقيق والقانون الذي تستند إليه.
- قدم نصائح عملية وقابلة للتنفيذ، وليس فقط نظرية.
- إذا كان الوضع غامضاً، اطرح **سؤال توضيح واحد فقط**.
- إذا لم تكن متأكداً من فصل ما، قل ذلك بوضوح.

# قواعد الاستشهاد بالنصوص القانونية
كل فصل يُذكر يجب أن يتبع هذا التنسيق بالضبط:
📌 **الفصل X من [اسم المجلة]** — «النص الحرفي من المصدر» [Source N]

مثال:
📌 **الفصل 14 من مجلة الشغل** — «يمكن إبرام عقد الشغل لمدة محددة أو غير محددة» [Source 1]

القواعد:
- اذكر رقم الفصل الدقيق الظاهر في المصدر.
- ضع النص المقتبس بين علامتي تنصيص «».
- اذكر دائماً [Source N] في نهاية كل استشهاد.
- رتّب الفصول حسب الموضوع لا حسب المصدر.

# هيكل الإجابة
للأسئلة البسيطة:
→ إجابة مباشرة + 📌 فصل قانوني + نصيحة عملية

للحالات المعقدة:
→ "## ⚖️ ما فهمته من وضعيتكم" — إعادة صياغة مختصرة
→ "## 📜 ما يقوله القانون" — الفصول مع تنسيق 📌 أعلاه، مرتبة حسب الموضوع
→ "## 💡 ما أنصحكم به عملياً" — نصائح مرقمة وقابلة للتنفيذ
→ "## ⚠️ نقاط انتباه" — مخاطر، استثناءات، مواعيد مهمة

اختم بـ **خلاصة** في 2-3 جمل.

# حدود المعرفة - الالتزام الصارم
- **مصدر معلوماتك الوحيد هو المقتطفات المسترجعة أعلاه فقط.**
- **ممنوع منعاً باتاً** اقتباس أو ذكر أي فصل غير موجود حرفياً في المقتطفات.
- يجب أن تستند كل واقعة لمصدر مع تنسيق 📌 المحدد أعلاه.

# الحدود
- تقدم معلومات قانونية وليس آراء قانونية رسمية.
- للنزاعات الخطيرة أو الإجراءات القضائية، أوصِ دائماً باستشارة محامٍ معتمد في تونس.
- لا تصدر عقوداً أو وثائق رسمية دون التنبيه بأنها تحتاج مصادقة مهنية.""",

    "fr": """# IDENTITÉ ET RÔLE
Vous êtes **Daleel** (دليل), un conseiller juridique expert spécialisé en droit tunisien.
Vous accompagnez des entreprises et des particuliers dans la compréhension et l'application du droit tunisien.
Vous ne vous comportez pas comme un moteur de recherche — vous écoutez, vous analysez, vous conseillez comme un vrai professionnel.

# VOS SOURCES DE RÉFÉRENCE
- مجلة الشغل (Code du travail tunisien — version arabe)
- مجلة الشركات التجارية (Code des sociétés commerciales — version arabe)
- Code du travail tunisien (version française)
- Code des sociétés commerciales (version française)
- Loi 63-2004 sur la protection des données personnelles

# RÈGLE LINGUISTIQUE
- La question est en français → répondez entièrement en français.
- NE PAS mélanger les langues.

# SOURCES MULTILINGUES
- Les sources récupérées peuvent être dans une autre langue (ex: arabe).
- Vous DEVEZ comprendre les sources dans n'importe quelle langue, mais **traduire et analyser explicitement le tout en français exclusif**.

# STYLE DE RÉPONSE
- Parlez comme un conseiller humain, chaleureux et professionnel.
- Reformulez toujours le problème de l'utilisateur avant de répondre.
- Citez toujours l'article précis et la loi sur laquelle vous vous appuyez.
- Donnez des conseils concrets et actionnables, pas uniquement de la théorie.
- Si la situation est ambiguë, posez **UNE seule question de clarification**.
- Si vous n'êtes pas certain d'un article, dites-le clairement.

# RÈGLES DE CITATION JURIDIQUE
Chaque article cité doit suivre ce format exact :
📌 **Article X du [Nom du Code]** — « extrait exact du texte de l'article » [Source N]

Exemple :
📌 **Article 14 du Code du travail** — « Le contrat de travail est conclu pour une durée déterminée ou indéterminée » [Source 1]

Règles :
- Citez le numéro d'article exact visible dans la source.
- Mettez l'extrait pertinent entre guillemets français « ».
- Indiquez toujours [Source N] à la fin de chaque citation.
- Regroupez les articles par thème, pas par source.

# STRUCTURE DE VOS RÉPONSES
Pour les questions simples :
→ Réponse directe + 📌 article de loi + conseil pratique

Pour les situations complexes :
→ "## ⚖️ Ce que je comprends de votre situation" — reformulation concise
→ "## 📜 Ce que dit la loi" — articles cités avec le format 📌 ci-dessus, regroupés par thème
→ "## 💡 Ce que je vous conseille concrètement" — conseils numérotés et actionnables
→ "## ⚠️ Points d'attention" — risques, exceptions, délais importants

Terminez par une **synthèse récapitulative** en 2-3 phrases.

# LIMITES DE CONNAISSANCES - RESPECT STRICT
- **Votre SEULE source de connaissances sont les extraits récupérés ci-dessus.**
- Vous avez **INTERDICTION FORMELLE** de citer ou inventer des lois ou articles qui ne sont pas explicitement présents dans les textes extraits ci-dessus.
- Chaque disposition abordée DOIT citer sa source avec le format 📌 défini ci-dessus.

# LIMITES PROFESSIONNELLES
- Vous fournissez des informations juridiques, pas des avis juridiques formels.
- Pour les litiges graves ou procédures judiciaires, recommandez toujours de consulter un avocat agréé en Tunisie.
- Ne générez jamais de contrats ou documents officiels sans préciser qu'ils nécessitent validation professionnelle.""",

    "en": """# IDENTITY & ROLE
You are **Daleel** (دليل), an expert legal advisor specializing in Tunisian law.
You assist businesses and individuals in understanding and applying Tunisian law.
You are not a search engine — you listen, analyze, and advise like a real professional.

# YOUR REFERENCE SOURCES
- مجلة الشغل (Tunisian Labor Code — Arabic version)
- مجلة الشركات التجارية (Commercial Companies Code — Arabic version)
- Tunisian Labor Code (French version)
- Commercial Companies Code (French version)
- Law 63-2004 on personal data protection

# LANGUAGE RULE
- Your ENTIRE response MUST be in **English**. Do NOT mix languages.

# CROSS-LANGUAGE SOURCES
- You MUST analyze the sources in their original language, then respond and explain entirely in English.

# RESPONSE STYLE
- Speak like a warm, professional human advisor.
- Always reformulate the user's problem before answering.
- Always cite the precise article and law you rely on.
- Give concrete, actionable advice — not just theory.
- If the situation is ambiguous, ask **ONE single clarification question**.
- If you are unsure about an article, say so clearly.

# CITATION RULES
Every cited article must follow this exact format:
📌 **Article X of [Code Name]** — "exact excerpt from the source text" [Source N]

Example:
📌 **Article 14 of the Labor Code** — "The employment contract may be concluded for a fixed or indefinite period" [Source 1]

Rules:
- Cite the exact article number visible in the source.
- Put the relevant excerpt in quotation marks.
- Always indicate [Source N] at the end of each citation.
- Group articles by theme, not by source.

# RESPONSE STRUCTURE
For simple questions:
→ Direct answer + 📌 law article + practical advice

For complex situations:
→ "## ⚖️ What I understand from your situation" — concise reformulation
→ "## 📜 What the law says" — articles cited with the 📌 format above, grouped by theme
→ "## 💡 My concrete advice" — numbered, actionable advice
→ "## ⚠️ Points of attention" — risks, exceptions, important deadlines

End with a **summary** in 2-3 sentences.

# KNOWLEDGE BOUNDARIES - STRICT COMPLIANCE
- Your ONLY knowledge source is the retrieved excerpts above.
- You are FORBIDDEN from citing any article NOT explicitly visible in the excerpts.
- Every disposition must cite its source using the 📌 format defined above.

# PROFESSIONAL LIMITS
- You provide legal information, not formal legal opinions.
- For serious disputes or court proceedings, always recommend consulting a licensed lawyer in Tunisia.
- Never generate contracts or official documents without noting they require professional validation."""
}

CONTEXT_INJECTION_TEMPLATE = {
    "ar": """# الوثائق القانونية المسترجعة
تم استرجاع المقتطفات الـ {num_sources} التالية من قاعدة البيانات القانونية التونسية. هذه هي مصادرك الأساسية.

⚠️ ملاحظة: اقرأ النصوص بلُغتها الأصلية، ثم صغ إجابتك باللغة العربية فقط.

{context}

─────────────────────────────────
الوثائق المرجعية: {doc_list}
─────────────────────────────────

هام: استخرج كل رقم فصل أو شرط موجود حرفياً في المصادر واستخدمه، وتجنب إضافة قوانين من خارجها.""",

    "fr": """# DOCUMENTS JURIDIQUES RÉCUPÉRÉS
Les {num_sources} extraits suivants ont été récupérés dans la base documentaire juridique tunisienne. Ils constituent vos sources principales.

⚠️ NOTE : Les sources peuvent être en arabe ou en français. Lisez-les attentivement, puis formulez toute votre reponse en français.

{context}

─────────────────────────────────
Documents référencés : {doc_list}
─────────────────────────────────

IMPORTANT : Extrayez chaque article et condition explicitement présents. N'inventez aucun article.""",

    "en": """# RETRIEVED LEGAL DOCUMENTS
The following {num_sources} excerpts were retrieved. These are your primary sources.

⚠️ NOTE: Read them in their original language, then respond in English.

{context}

─────────────────────────────────
Documents referenced: {doc_list}
─────────────────────────────────

IMPORTANT: Extract every relevant article explicitly present. Do not invent any outside references."""
}

GROUNDING_REMINDER = {
    "ar": """# قيود الإجابة المحكمة
- اقتصر فقط على الحقائق والفصول المذكورة حصرياً في المقتطفات.
- يمنع ذكر فصول غير موجودة صراحة في المستندات.
- استخدم العبارات الدقيقة من المصادر.""",

    "fr": """# CONTRAINTES DE RÉDACTION STRICTES
- Utilisez uniquement les faits et articles clairement visibles dans les extraits récupérés.
- N'inventez aucun numéro d'article.
- Préférez la formulation exacte de la source quand possible.""",

    "en": """# ANSWERING CONSTRAINTS
- Use only facts and articles visible in the excerpts.
- Do not invent article numbers."""
}

# ─────────────────────────────────────────────────────────────
# Prompt de réécriture strictement ancrée dans le contexte
# ─────────────────────────────────────────────────────────────

CONTEXT_REWRITE_PROMPT = {
    "fr": """# MODE : RÉÉCRITURE STRICTEMENT ANCRÉE DANS LES SOURCES

## MISSION
Réécrivez une reponse juridique complète en utilisant **uniquement** les
extraits que vous venez de recevoir ci-dessus. Vous ne disposez d'aucune
autre source de connaissances.

## QUESTION D'ORIGINE
{question}
{draft_section}
## RÈGLES IMPÉRATIVES

1. **INTERDICTION ABSOLUE** d'introduire toute loi, article, numéro de texte,
   autorité ou institution qui n'apparaît pas **mot pour mot** dans les extraits
   reçus précédemment.
2. **Ignorez totalement** vos connaissances juridiques préalables. Seuls les
   extraits ci-dessus existent pour vous.
3. Chaque affirmation juridique DOIT citer sa source : **[Source N]**.
4. Si le brouillon contenait des références non présentes dans les extraits,
   **supprimez-les** sans les remplacer par d'autres inventions.
5. Ne reformulez pas les articles de loi — utilisez la formulation exacte des
   extraits autant que possible.

## SI LE CONTEXTE EST INSUFFISANT

Si les extraits ne contiennent pas assez d'informations pour répondre
pleinement à la question :
- Indiquez clairement : « ⚠️ **Contexte insuffisant** — Les sources
  disponibles ne couvrent pas entièrement cette question. »
- Précisez **quels aspects précis** ne sont pas couverts par les extraits.
- Suggérez **quels documents ou textes de loi** supplémentaires seraient
  nécessaires pour compléter l'analyse.
- **N'inventez JAMAIS** de règles, conditions ou sanctions pour combler
  les lacunes.

## FORMAT DE RÉPONSE
Répondez en français. Adoptez un ton chaleureux et professionnel.
Pour les situations complexes, structurez avec :
→ **Ce que je comprends de votre situation**
→ **Ce que dit la loi** (avec articles précis et [Source N])
→ **Ce que je vous conseille concrètement**
→ **Points d'attention**""",

    "ar": """# الوضع: إعادة كتابة مرتبطة حصرياً بالمصادر

## المهمة
أعد كتابة إجابة قانونية كاملة باستخدام **فقط** المقتطفات التي تلقيتها أعلاه.
لا تملك أي مصدر معرفة آخر.

## السؤال الأصلي
{question}
{draft_section}
## قواعد إلزامية

1. **يُمنع منعاً باتاً** إدخال أي قانون أو فصل أو رقم نص أو هيئة أو مؤسسة
   غير موجودة **حرفياً** في المقتطفات أعلاه.
2. **تجاهل تماماً** معارفك القانونية المسبقة. المقتطفات أعلاه فقط هي مصدرك.
3. كل تأكيد قانوني يجب أن يُنسب إلى مصدره: **[Source N]**.
4. إذا كانت المسودة تحتوي على مراجع غير موجودة في المقتطفات، **احذفها** دون
   استبدالها باختراعات أخرى.
5. لا تعد صياغة نصوص القانون — استخدم الصياغة الأصلية من المقتطفات قدر الإمكان.

## إذا كان السياق غير كافٍ

إذا لم تحتوِ المقتطفات على معلومات كافية للإجابة الكاملة:
- اذكر بوضوح: «⚠️ **سياق غير كافٍ** — المصادر المتاحة لا تغطي هذا السؤال
  بالكامل.»
- حدد **أي جوانب بالضبط** غير مغطاة بالمقتطفات.
- اقترح **أي وثائق أو نصوص قانونية** إضافية ستكون ضرورية.
- **لا تخترع أبداً** قواعد أو شروطاً أو عقوبات لسد الثغرات.

## شكل الإجابة
أجب باللغة العربية. اعتمد أسلوباً دافئاً ومهنياً.
للحالات المعقدة، نظّم بالأقسام:
→ **ما فهمته من وضعيتكم**
→ **ما يقوله القانون** (مع الفصول الدقيقة و[Source N])
→ **ما أنصحكم به عملياً**
→ **نقاط انتباه**""",

    "en": """# MODE: STRICTLY SOURCE-GROUNDED REWRITE

## MISSION
Rewrite a complete legal answer using **only** the excerpts you just received
above. You have no other knowledge source.

## ORIGINAL QUESTION
{question}
{draft_section}
## MANDATORY RULES

1. **ABSOLUTE PROHIBITION** on introducing any law, article, text number,
   authority or institution not present **verbatim** in the excerpts above.
2. **Completely ignore** your prior legal knowledge. Only the excerpts above
   exist for you.
3. Every legal assertion MUST cite its source: **[Source N]**.
4. If the draft contained references not present in the excerpts, **remove
   them** without replacing them with other inventions.
5. Do not rephrase legal provisions — use the exact wording from the excerpts
   whenever possible.

## IF THE CONTEXT IS INSUFFICIENT

If the excerpts do not contain enough information to fully answer:
- Clearly state: "⚠️ **Insufficient context** — The available sources do not
  fully cover this question."
- Specify **which exact aspects** are not covered by the excerpts.
- Suggest **which additional documents or legal texts** would be needed.
- **NEVER invent** rules, conditions or penalties to fill the gaps.

## RESPONSE FORMAT
Respond in English. Adopt a warm, professional tone.
For complex situations, structure with:
→ **What I understand from your situation**
→ **What the law says** (with precise articles and [Source N])
→ **My concrete advice**
→ **Points of attention**"""
}

_DRAFT_SECTION_TEMPLATE = {
    "fr": """
## BROUILLON INITIAL (à corriger)
Le brouillon suivant contient possiblement des références juridiques non
soutenues par les extraits. Corrigez-le en supprimant tout contenu inventé.

<<<BROUILLON>>>
{draft}
<<<FIN BROUILLON>>>
""",
    "ar": """
## المسودة الأولية (للتصحيح)
المسودة التالية قد تحتوي على مراجع قانونية غير مدعومة بالمقتطفات.
صححها بحذف كل محتوى مختلق.

<<<مسودة>>>
{draft}
<<<نهاية المسودة>>>
""",
    "en": """
## INITIAL DRAFT (to correct)
The following draft may contain legal references not supported by the excerpts.
Correct it by removing any invented content.

<<<DRAFT>>>
{draft}
<<<END DRAFT>>>
""",
}


def _build_rewrite_messages(
    detected_lang: str,
    question: str,
    context_message: str,
    initial_draft: str = "",
) -> list[dict]:
    """Build the message chain for a context-grounded rewrite.

    This is a **pure function** (no I/O) so it is easy to unit-test.

    Parameters
    ----------
    detected_lang : str
        ``"fr"``, ``"ar"`` or ``"en"``.
    question : str
        The user's original legal question.
    context_message : str
        Pre-formatted context chunks (from ``CONTEXT_INJECTION_TEMPLATE``).
    initial_draft : str, optional
        The first LLM answer that failed grounding validation.  When
        provided, the template embeds it so the model can see exactly
        what to fix.  Omit for prompt-leak recovery to avoid feeding the
        leaked content back.

    Returns
    -------
    list[dict]
        Ready-to-send message list for ``_call_ollama``.
    """
    lang_key = detected_lang if detected_lang in ("ar", "fr") else "en"

    draft_section = ""
    if initial_draft and initial_draft.strip():
        draft_section = _DRAFT_SECTION_TEMPLATE[lang_key].format(
            draft=initial_draft.strip(),
        )

    rewrite_user_prompt = CONTEXT_REWRITE_PROMPT[lang_key].format(
        question=question,
        draft_section=draft_section,
    )

    system_message = (
        SYSTEM_PROMPT.get(lang_key, SYSTEM_PROMPT["en"])
        + "\n\n"
        + GROUNDING_REMINDER.get(lang_key, GROUNDING_REMINDER["en"])
    )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": context_message},
        {"role": "assistant", "content": _get_ack_message(lang_key)},
        {"role": "user", "content": rewrite_user_prompt},
    ]


USER_QUESTION_TEMPLATE_AR = """سؤالي القانوني هو:

{question}

أجب باللغة العربية فقط بصفتك خبيراً قانونياً تونسياً متمرساً. قدم تحليلاً قانونياً مفصلاً وشاملاً يتضمن:
- الإطار القانوني المنطبق (القوانين والفصول)
- تحليل مفصل لكل فصل ذي صلة مع شرح معناه العملي
- الشروط والمتطلبات القانونية
- الإجراءات العملية المتبعة إن وجدت
- التحذيرات والاستثناءات المهمة
- خلاصة شاملة

استخدم المصادر المذكورة أعلاه واذكر رقم المصدر [Source N] عند كل معلومة قانونية."""

USER_QUESTION_TEMPLATE_FR = """Ma question juridique est :

{question}

Répondez uniquement en français en tant qu'expert juridique tunisien chevronné. Fournissez une consultation juridique complète et détaillée comprenant :
- Le cadre juridique applicable (codes, lois, articles)
- Une analyse détaillée article par article avec explication de la portée pratique
- Les conditions et exigences légales
- La procédure à suivre le cas échéant (étapes, documents, autorités compétentes)
- Les points d'attention, exceptions et sanctions éventuelles
- Une synthèse récapitulative

Utilisez les sources ci-dessus et citez le numéro de source [Source N] pour chaque disposition juridique."""

USER_QUESTION_TEMPLATE_EN = """My legal question is:

{question}

Respond only in English as an experienced Tunisian legal expert. Provide a comprehensive legal consultation including:
- The applicable legal framework (codes, laws, articles)
- A detailed article-by-article analysis with practical implications
- Legal conditions and requirements
- Step-by-step procedure where applicable (steps, documents, authorities)
- Important warnings, exceptions, and potential penalties
- A comprehensive summary

Use the sources above and cite the source number [Source N] for each legal provision."""

# Pipeline RAG
# ─────────────────────────────────────────────────────────────

async def ask(
    db: Any,
    question: str,
    top_k: int = 5,
    language_filter: Optional[str] = None,
    response_language: Optional[str] = None,
    document_id: Optional[str] = None,
    llm_model: Optional[str] = None,
    temperature: float = 0.3,
    history: list[dict] | None = None,
    use_domain_router: bool = True,
    use_quality_guard: Optional[bool] = None,
    intent: Optional[str] = None,
    case_id: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> dict:
    """
    Pipeline RAG classique:
    1. détecter la langue
    2. récupérer les chunks pertinents
    3. construire le contexte
    4. appeler le modèle

    When *case_id* is provided the case conversation context (known facts,
    missing facts, matter type …) is injected into the system prompt so the
    legal answer is grounded in the ongoing case.

    Retourne un dictionnaire avec la reponse, les sources et le modèle utilisé.
    """
    settings = get_settings()
    model_name = (llm_model or settings.llm_model).strip()

    # Étape 0: détecter la langue de la question
    # ── Derja normalization (Tunisian dialect → French) ──
    is_derja = False
    derja_original = question
    if getattr(settings, "derja_normalizer_enabled", True):
        derja_effective, derja_original, is_derja = _normalize_if_derja(question)
    else:
        derja_effective = question
    if is_derja:
        # Derja detected: switch to French pipeline, keep original for retrieval
        detected_lang = "fr"
        question = derja_effective  # French-wrapped query for LLM
        retrieval_question = derja_original  # Original Arabic for embedding search
        logger.info("Derja pipeline activated — LLM will receive French, retrieval uses original Arabic")
    else:
        retrieval_question = question  # Normal flow

    if not is_derja:
        detected_lang = response_language if response_language in {"ar", "fr", "en"} else _detect_query_language(question)
    lang_name, lang_instruction = _LANG_LABELS.get(detected_lang, _LANG_LABELS["en"])
    logger.info(f"Detected query language: {detected_lang} ({lang_name})")

    # ── Sprint 6+ : domain routing ──
    domain_name = "unknown"
    domain_config = None
    if getattr(settings, "domain_router_enabled", False) and use_domain_router:
        try:
            domain_name, domain_config = await route_question(
                question=retrieval_question,
                lang=detected_lang,
                targeted_loi_code=document_id,
            )
            logger.info("RAG domain: %s", domain_name)
        except Exception as e:
            logger.warning("Domain routing failed: %s", e)

    # Étape 1: récupérer les passages pertinents
    effective_document_id, scope_reason = await _resolve_effective_document_id(
        db,
        question,
        detected_lang,
        document_id,
    )
    if scope_reason:
        logger.info("Auto document scope applied: %s (%s)", scope_reason, effective_document_id)

    # Step 0.b: optional direct override from highly similar validated correction.
    # Keep strict RAG mode purely grounded on retrieved chunks.
    if not getattr(settings, "strict_grounded_only", False):
        try:
            best_feedback = await feedback_service.get_best_feedback_match(
                db,
                question=question,
                detected_lang=detected_lang,
                source_document_id=effective_document_id,
                organization_id=organization_id,
            )
            if best_feedback:
                logger.info("Using validated feedback override (id=%s, score=%.3f)", best_feedback.get("id"), best_feedback.get("score", 0.0))
                return {
                    "answer": str(best_feedback.get("corrected_answer") or ""),
                    "sources": [],
                    "model": f"{model_name}+feedback",
                    "chunks_used": 0,
                }
        except Exception as e:
            logger.warning("Feedback override lookup failed: %s", e)

    # Do not force same-language retrieval by default; cross-language legal sources
    # are often cleaner and can be translated in the final answer.
    effective_language_filter = language_filter

    retrieval_query = _augment_query_for_specific_legal_scope(retrieval_question, detected_lang)

    effective_top_k = getattr(domain_config, "top_k", top_k) if domain_config else top_k
    retrieval_k = min(max(effective_top_k * 3, effective_top_k + 5), 30)

    # ── Sprint 6+ : partitioned retrieval when intent hints at legal structure ──
    if intent and domain_config and getattr(settings, "partitioned_retrieval_enabled", True):
        try:
            chunks = await legal_retrieval_orchestrator.retrieve_partitioned(
                question=retrieval_query,
                intent=intent,
                search_fn=lambda q, top_k, extra_filter=None: search_service.semantic_search(
                    db, query=q, top_k=top_k,
                    language_filter=effective_language_filter,
                    document_id=effective_document_id,
                    extra_filter=extra_filter,
                    organization_id=organization_id,
                ),
                db=db,
                domain_config=domain_config,
            )
        except Exception as e:
            logger.warning("Partitioned retrieval failed, falling back to semantic_search: %s", e)
            chunks = await search_service.semantic_search(
                db,
                query=retrieval_query,
                top_k=retrieval_k,
                language_filter=effective_language_filter,
                document_id=effective_document_id,
                organization_id=organization_id,
            )
    else:
        chunks = await search_service.semantic_search(
            db,
            query=retrieval_query,
            top_k=retrieval_k,
            language_filter=effective_language_filter,
            document_id=effective_document_id,
            organization_id=organization_id,
        )

    if not chunks:
        no_result_messages = {
            "ar": "لم أجد وثائق ذات صلة بسؤالك في قاعدة البيانات. يرجى التأكد من رفع الوثائق المتعلقة بالموضوع أو إعادة صياغة سؤالك.",
            "fr": "Je n'ai trouvé aucun document pertinent dans la base de données pour votre question. Veuillez vérifier que les documents relatifs au sujet ont été téléchargés ou reformuler votre question.",
            "en": "I could not find any relevant documents in the database for your question. Please ensure the related documents have been uploaded or try rephrasing your question.",
        }
        return {
            "answer": no_result_messages.get(detected_lang, no_result_messages["en"]),
            "sources": [],
            "model": model_name,
            "chunks_used": 0,
        }

    # Étape 1.b: reranker les chunks et garder les meilleurs
    chunks = _rerank_chunks_for_question(question, chunks, detected_lang, domain_config=domain_config)[:effective_top_k]
    reranking_service = _get_reranking_service()
    if await reranking_service.is_available():
        chunks = await reranking_service.rerank(question, chunks)

    cached = llm_cache.get(question, chunks)
    if cached:
        logger.info("LLM cache hit")
        return {
            "answer": cached,
            "sources": _build_source_metadata(chunks),
            "model": f"{model_name}+cache",
            "chunks_used": len(chunks),
            "domain": domain_name,
            "quality_guard_status": None,
            "quality_guard_issues": None,
            "kg_enriched": False,
        }

    if getattr(settings, "strict_grounded_only", False):
        supported_refs = _collect_supported_article_refs(chunks)
        grounded = _build_grounded_synthesis_from_chunks(
            detected_lang,
            question,
            chunks,
            set(),
            supported_refs,
        )
        return {
            "answer": grounded,
            "sources": _build_source_metadata(chunks),
            "model": f"{model_name}+grounded",
            "chunks_used": len(chunks),
        }

    # Étape 2: construire le bloc de contexte
    context = _build_context_block(chunks)
    unique_docs = list({c.get("filename", "unknown") for c in chunks})
    doc_list_str = ", ".join(f'"{d}"' for d in unique_docs)

    # ── Sprint 6+ : KG light enrichment ──
    kg_text = ""
    if getattr(settings, "kg_light_enabled", False):
        try:
            chunk_meta = [c.get("metadata") or {
                "loi_id": c.get("loi_id"),
                "article_id": c.get("article_id"),
            } for c in chunks if c.get("loi_id") or c.get("article_id")]
            if chunk_meta:
                kg_text = await graph_resolver.kg_context_for_rag(
                    db, chunk_meta, max_entities=getattr(settings, "kg_light_max_entities", 6)
                )
        except Exception as e:
            logger.warning("KG light enrichment failed: %s", e)

    context_message = CONTEXT_INJECTION_TEMPLATE.get(detected_lang, CONTEXT_INJECTION_TEMPLATE["en"]).format(
        num_sources=len(chunks),
        context=context,
        doc_list=doc_list_str,
    )
    if kg_text:
        context_message = f"【Informations structurées du graphe juridique】\n{kg_text}\n\n{context_message}"

    try:
        feedback_examples = await feedback_service.get_relevant_feedback_examples(
            db,
            question=question,
            detected_lang=detected_lang,
            limit=2,
            organization_id=organization_id,
        )
        feedback_block = _build_feedback_examples_block(feedback_examples, detected_lang)
        if feedback_block:
            context_message = f"{context_message}\n\n{feedback_block}"
    except Exception as e:
        logger.warning("Failed to load feedback examples: %s", e)

    # Étape 3: préparer la question selon la langue détectée
    question_templates = {
        "ar": USER_QUESTION_TEMPLATE_AR,
        "fr": USER_QUESTION_TEMPLATE_FR,
        "en": USER_QUESTION_TEMPLATE_EN,
    }
    user_question = question_templates.get(
        detected_lang, USER_QUESTION_TEMPLATE_EN
    ).format(question=question)

    # Étape 4: construire le prompt système
    system_message = SYSTEM_PROMPT.get(detected_lang, SYSTEM_PROMPT["en"])

    # ── Sprint 6+ : inject domain persona suffix ──
    domain_suffix = getattr(domain_config, "system_prompt_suffix", "") if domain_config else ""
    if domain_suffix:
        system_message = f"{system_message}\n\n{domain_suffix}"

    # ── Case conversation context injection ──
    if case_id:
        try:
            from app.services.case_conversation_service import build_case_context_for_rag
            case_context_block = await build_case_context_for_rag(db, case_id, detected_lang=detected_lang)
            if case_context_block:
                system_message = f"{system_message}\n\n{case_context_block}"
                logger.info("Injected case conversation context for case_id=%s", case_id)
        except Exception as e:
            logger.warning("Failed to inject case conversation context: %s", e)

    # Étape 5: construire la conversation envoyée au modèle
    messages = [{"role": "system", "content": system_message + "\n\n" + GROUNDING_REMINDER.get(detected_lang, GROUNDING_REMINDER["en"])}]

    # On conserve seulement les derniers échanges pour éviter de dépasser la limite de contexte
    if history:
        # Trim to last 10 exchanges (20 messages) to stay within token limits
        trimmed_history = history[-20:]
        for msg in trimmed_history:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

    # On ajoute le contexte puis la question courante
    messages.append({"role": "user",      "content": context_message})
    messages.append({"role": "assistant", "content": _get_ack_message(detected_lang)})
    messages.append({"role": "user",      "content": user_question})

    # Étape 6: appel du modèle Ollama
    logger.info(
        f"Calling Ollama ({model_name}) | "
        f"lang={detected_lang} | "
        f"chunks={len(chunks)} | "
        f"history={len(history or [])} msgs | "
        f"docs={doc_list_str}"
    )

    try:
        answer = await _call_ollama(
            model=model_name,
            messages=messages,
            temperature=temperature,
            base_url=settings.llm_base_url,
        )

        validation = _validate_answer_grounding(answer, chunks, detected_lang)
        if validation["unsupported_refs"]:
            logger.warning(
                "Unsupported refs detected in model answer; attempting strict reground rewrite before deterministic fallback (unsupported=%s)",
                ", ".join(sorted(validation["unsupported_refs"])),
            )
            rewritten = await _rewrite_answer_grounded(
                settings=settings,
                model_name=model_name,
                detected_lang=detected_lang,
                lang_name=lang_name,
                lang_instruction=lang_instruction,
                context_message=context_message,
                question=question,
                initial_draft=answer,
            )
            rewritten_validation = _validate_answer_grounding(rewritten, chunks, detected_lang)
            if rewritten_validation["unsupported_refs"] or rewritten_validation["should_reground"]:
                if getattr(settings, "strict_grounded_only", False):
                    answer = _build_grounded_synthesis_from_chunks(
                        detected_lang,
                        question,
                        chunks,
                        rewritten_validation["answer_refs"],
                        rewritten_validation["supported_refs"],
                    )
                else:
                    answer = _strip_unsupported_article_refs(
                        rewritten or answer,
                        validation["unsupported_refs"],
                    )
            else:
                answer = rewritten
        elif validation["should_reground"]:
            logger.warning(
                "Model answer failed grounding validation (refs=%s verified=%s unsupported=%s language_ok=%s)",
                ", ".join(sorted(validation["answer_refs"])) if validation["answer_refs"] else "none",
                ", ".join(sorted(validation["verified_refs"])) if validation["verified_refs"] else "none",
                ", ".join(sorted(validation["unsupported_refs"])) if validation["unsupported_refs"] else "none",
                validation["language_ok"],
            )
            rewritten = await _rewrite_answer_grounded(
                settings=settings,
                model_name=model_name,
                detected_lang=detected_lang,
                lang_name=lang_name,
                lang_instruction=lang_instruction,
                context_message=context_message,
                question=question,
                initial_draft=answer,
            )
            rewritten_validation = _validate_answer_grounding(rewritten, chunks, detected_lang)

            if rewritten_validation["should_reground"]:
                if getattr(settings, "strict_grounded_only", False):
                    answer = _build_grounded_synthesis_from_chunks(
                        detected_lang,
                        question,
                        chunks,
                        rewritten_validation["answer_refs"],
                        rewritten_validation["supported_refs"],
                    )
                else:
                    answer = rewritten
            else:
                answer = rewritten

        if _looks_like_prompt_leak(answer):
            logger.warning("Prompt leak detected in model answer; attempting grounded rewrite recovery")
            rewritten = await _rewrite_answer_grounded(
                settings=settings,
                model_name=model_name,
                detected_lang=detected_lang,
                lang_name=lang_name,
                lang_instruction=lang_instruction,
                context_message=context_message,
                question=question,
            )
            if _looks_like_prompt_leak(rewritten):
                if getattr(settings, "strict_grounded_only", False):
                    answer = _build_grounded_fallback(
                        detected_lang,
                        chunks,
                        set(),
                        _collect_supported_article_refs(chunks),
                    )
                else:
                    answer = rewritten
            else:
                answer = rewritten
    except Exception as e:
        logger.error("Ollama call failed: %s", e)
        error_messages = {
            "ar": f"خطأ في الاتصال بنموذج اللغة. {str(e)}",
            "fr": f"Erreur de communication avec le modèle. {str(e)}",
            "en": f"LLM communication error: {str(e)}",
        }
        return {
            "answer": error_messages.get(detected_lang, error_messages["en"]),
            "sources": _build_source_metadata(chunks),
            "model": model_name,
            "chunks_used": len(chunks),
        }

    # Étape 7: retourner la reponse avec les métadonnées des sources
    answer = _apply_final_language_guardrail(
        answer=answer,
        detected_lang=detected_lang,
        question=question,
        chunks=chunks,
        strict_grounded_only=getattr(settings, "strict_grounded_only", False),
    )

    # ── Sprint 6+ : quality guard ──
    qg_result = None
    if use_quality_guard is None:
        use_quality_guard = getattr(settings, "quality_guard_enabled", True)
    if use_quality_guard:
        try:
            qg_result = await audit_and_guard(
                question=question,
                answer=answer,
                chunks=chunks,
                lang=detected_lang,
                enabled=True,
            )
            answer = qg_result["answer"]
        except Exception as e:
            logger.warning("Quality guard audit failed: %s", e)

    sources = _build_source_metadata(chunks)
    llm_cache.set(question, chunks, answer)

    result = {
        "answer": answer,
        "sources": sources,
        "model": model_name,
        "chunks_used": len(chunks),
        "domain": domain_name,
        "quality_guard_status": qg_result.get("status") if qg_result else None,
        "quality_guard_issues": qg_result.get("issues") if qg_result else None,
        "kg_enriched": bool(kg_text),
    }
    if is_derja:
        result["derja_detected"] = True
        result["derja_original"] = derja_original
    return result


async def ask_agentic(
    db: Any,
    question: str,
    top_k: int = 5,
    language_filter: Optional[str] = None,
    response_language: Optional[str] = None,
    document_id: Optional[str] = None,
    llm_model: Optional[str] = None,
    temperature: float = 0.3,
    history: list[dict] | None = None,
    max_attempts: int = 2,
    use_domain_router: bool = True,
    use_quality_guard: Optional[bool] = None,
    intent: Optional[str] = None,
    case_id: Optional[str] = None,
    document_context: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> dict:
    """
    Mode agentique progressif:
    1. détecter l'intention
    2. récupérer et reranker les passages
    3. reformuler si la pertinence est faible
    4. générer une reponse bien fondée sur les meilleurs chunks

    When *case_id* is provided the case conversation context is injected
    into the system prompt (same mechanism as ``ask``).
    """
    t0 = time.perf_counter()
    settings = get_settings()
    model_name = (llm_model or settings.llm_model).strip()
    detected_lang = response_language if response_language in {"ar", "fr", "en"} else _detect_query_language(question)
    lang_name, lang_instruction = _LANG_LABELS.get(detected_lang, _LANG_LABELS["en"])
    intent = _detect_intent(question, detected_lang)
    route_cfg = _route_config_for_intent(intent)
    route_decision = str(route_cfg["route_decision"])
    dynamic_max_attempts = min(max_attempts, int(route_cfg["max_attempts"]))
    retrieval_multiplier = int(route_cfg["retrieval_multiplier"])

    reasoning_steps: list[str] = [
        f"intent_detected:{intent}",
        f"language_detected:{detected_lang}",
        f"route_decision:{route_decision}",
    ]

    # ── Sprint 6+ : domain routing ──
    domain_name = "unknown"
    domain_config = None
    if getattr(settings, "domain_router_enabled", False) and use_domain_router:
        try:
            domain_name, domain_config = await route_question(
                question=question,
                lang=detected_lang,
                targeted_loi_code=document_id,
            )
            reasoning_steps.append(f"domain_routed:{domain_name}")
        except Exception as e:
            logger.warning("Domain routing failed (agentic): %s", e)

    # Keep retrieval cross-language by default for robustness with mixed-quality corpora.
    effective_language_filter = language_filter

    retrieval_ms = 0.0
    generation_ms = 0.0

    current_query = _augment_query_for_specific_legal_scope(question, detected_lang)
    rewritten_query: Optional[str] = None
    final_chunks: list[dict] = []
    retrieval_attempts = 0
    effective_document_id, scope_reason = await _resolve_effective_document_id(
        db,
        question,
        detected_lang,
        document_id,
    )
    if scope_reason:
        reasoning_steps.append(f"document_scope:{scope_reason}")

    # Deterministic short-circuit when an already validated correction matches.
    # Disabled in strict grounded mode so answers always come from retrieved chunks.
    if not getattr(settings, "strict_grounded_only", False):
        try:
            best_feedback = await feedback_service.get_best_feedback_match(
                db,
                question=question,
                detected_lang=detected_lang,
                source_document_id=effective_document_id,
                organization_id=organization_id,
            )
            if best_feedback:
                reasoning_steps.append(f"feedback_override:{best_feedback.get('id')}")
                return {
                    "answer": str(best_feedback.get("corrected_answer") or ""),
                    "sources": [],
                    "model": f"{model_name}+feedback",
                    "chunks_used": 0,
                    "reasoning_steps": reasoning_steps,
                    "retrieval_attempts": 0,
                    "rewritten_query": None,
                    "intent": intent,
                    "route_decision": route_decision,
                    "timings_ms": {
                        "retrieval": 0.0,
                        "generation": 0.0,
                        "total": round((time.perf_counter() - t0) * 1000, 2),
                    },
                    "selected_mode": "agentic",
                }
        except Exception as e:
            logger.warning("Feedback override lookup failed (agentic): %s", e)

    # ── Document-focused short-circuit ──
    # When a document is uploaded AND the question is about the document itself
    # (summarize, explain, fill guide, etc.), skip RAG entirely and focus on the document.
    if document_context and _is_document_focused_question(question, detected_lang):
        reasoning_steps.append("document_focused_mode")
        logger.info("Document-focused mode: skipping RAG, focusing on uploaded document")

        system_msg = _DOC_FOCUSED_SYSTEM_PROMPTS.get(detected_lang, _DOC_FOCUSED_SYSTEM_PROMPTS["en"])
        messages = [{"role": "system", "content": system_msg}]

        if history:
            for msg in history[-10:]:
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": f"[Document]\n\n{document_context}"})
        ack = _get_ack_message(detected_lang)
        messages.append({"role": "assistant", "content": ack})
        messages.append({"role": "user", "content": question})

        try:
            t_gen = time.perf_counter()
            answer = await _call_ollama(
                model=model_name,
                messages=messages,
                temperature=temperature,
                base_url=settings.llm_base_url,
            )
            gen_ms = (time.perf_counter() - t_gen) * 1000
        except Exception as e:
            error_msgs = {
                "ar": f"خطأ في الاتصال بنموذج اللغة. {e}",
                "fr": f"Erreur de communication avec le modèle. {e}",
                "en": f"LLM communication error: {e}",
            }
            answer = error_msgs.get(detected_lang, error_msgs["en"])
            gen_ms = 0.0

        return {
            "answer": answer,
            "sources": [],
            "model": model_name,
            "chunks_used": 0,
            "reasoning_steps": reasoning_steps,
            "retrieval_attempts": 0,
            "rewritten_query": None,
            "intent": intent,
            "route_decision": "document_focused",
            "timings_ms": {
                "retrieval": 0.0,
                "generation": round(gen_ms, 2),
                "total": round((time.perf_counter() - t0) * 1000, 2),
            },
            "selected_mode": "document_focused",
        }

    for attempt in range(1, dynamic_max_attempts + 1):
        retrieval_attempts = attempt
        reasoning_steps.append(f"retrieve_attempt:{attempt}")

        t_retrieve = time.perf_counter()
        effective_top_k = getattr(domain_config, "top_k", top_k) if domain_config else top_k
        retrieval_k = min(max(effective_top_k * retrieval_multiplier, effective_top_k + 5), 30)

        if intent and domain_config and getattr(settings, "partitioned_retrieval_enabled", True):
            try:
                chunks = await legal_retrieval_orchestrator.retrieve_partitioned(
                    question=current_query,
                    intent=intent,
                    search_fn=lambda q, top_k, extra_filter=None: search_service.semantic_search(
                        db, query=q, top_k=top_k,
                        language_filter=effective_language_filter,
                        document_id=effective_document_id,
                        extra_filter=extra_filter,
                        organization_id=organization_id,
                    ),
                    db=db,
                    domain_config=domain_config,
                )
            except Exception as e:
                logger.warning("Partitioned retrieval failed (agentic), falling back: %s", e)
                chunks = await search_service.semantic_search(
                    db,
                    query=current_query,
                    top_k=retrieval_k,
                    language_filter=effective_language_filter,
                    document_id=effective_document_id,
                    organization_id=organization_id,
                )
        else:
            chunks = await search_service.semantic_search(
                db,
                query=current_query,
                top_k=retrieval_k,
                language_filter=effective_language_filter,
                document_id=effective_document_id,
                organization_id=organization_id,
            )
        retrieval_ms += (time.perf_counter() - t_retrieve) * 1000

        if not chunks:
            reasoning_steps.append("no_chunks_found")
        else:
            reranked = _rerank_chunks_for_question(question, chunks, detected_lang, domain_config=domain_config)[:effective_top_k]
            if _is_relevant_enough(question, reranked, detected_lang):
                final_chunks = reranked
                reasoning_steps.append("chunks_accepted")
                break
            reasoning_steps.append("chunks_rejected_low_relevance")

        if attempt < dynamic_max_attempts:
            rewritten_query = _rewrite_query_for_agentic(question, detected_lang, intent)
            current_query = rewritten_query
            reasoning_steps.append("query_rewritten")

    if not final_chunks:
        no_result_messages = {
            "ar": "لم أجد وثائق قانونية كافية للإجابة بدقة. أعدت المحاولة بصياغة موسعة لكن ما زالت النتائج غير كافية.",
            "fr": "Je n'ai pas trouvé assez de documents juridiques pertinents pour répondre avec précision, même après reformulation de la requête.",
            "en": "I could not find enough relevant legal documents to answer accurately, even after query rewriting.",
        }
        return {
            "answer": no_result_messages.get(detected_lang, no_result_messages["en"]),
            "sources": [],
            "model": model_name,
            "chunks_used": 0,
            "reasoning_steps": reasoning_steps,
            "retrieval_attempts": retrieval_attempts,
            "rewritten_query": rewritten_query,
            "intent": intent,
            "route_decision": route_decision,
            "timings_ms": {
                "retrieval": round(retrieval_ms, 2),
                "generation": 0.0,
                "total": round((time.perf_counter() - t0) * 1000, 2),
            },
            "selected_mode": "agentic",
        }

    reranking_service = _get_reranking_service()
    if await reranking_service.is_available():
        final_chunks = await reranking_service.rerank(question, final_chunks)

    if getattr(settings, "strict_grounded_only", False):
        supported_refs = _collect_supported_article_refs(final_chunks)
        grounded = _build_grounded_synthesis_from_chunks(
            detected_lang,
            question,
            final_chunks,
            set(),
            supported_refs,
        )
        reasoning_steps.append("deterministic_grounded_strict_mode")
        return {
            "answer": grounded,
            "sources": _build_source_metadata(final_chunks),
            "model": f"{model_name}+grounded",
            "chunks_used": len(final_chunks),
            "reasoning_steps": reasoning_steps,
            "retrieval_attempts": retrieval_attempts,
            "rewritten_query": rewritten_query,
            "intent": intent,
            "route_decision": route_decision,
            "timings_ms": {
                "retrieval": round(retrieval_ms, 2),
                "generation": 0.0,
                "total": round((time.perf_counter() - t0) * 1000, 2),
            },
            "selected_mode": "agentic",
        }

    # For manager-obligations queries, prefer deterministic grounded synthesis
    # over free-form generation to maximize factual fidelity.
    # Bypass only when strict_grounded_only is enabled.
    if _is_manager_obligations_query(question) and getattr(settings, "strict_grounded_only", False):
        supported_refs = _collect_supported_article_refs(final_chunks)
        grounded = _build_grounded_synthesis_from_chunks(
            detected_lang,
            question,
            final_chunks,
            set(),
            supported_refs,
        )
        reasoning_steps.append("deterministic_grounded_manager_obligations")
        return {
            "answer": grounded,
            "sources": _build_source_metadata(final_chunks),
            "model": f"{model_name}+grounded",
            "chunks_used": len(final_chunks),
            "reasoning_steps": reasoning_steps,
            "retrieval_attempts": retrieval_attempts,
            "rewritten_query": rewritten_query,
            "intent": intent,
            "route_decision": route_decision,
            "timings_ms": {
                "retrieval": round(retrieval_ms, 2),
                "generation": 0.0,
                "total": round((time.perf_counter() - t0) * 1000, 2),
            },
            "selected_mode": "agentic",
        }

    # Construction du contexte et de la question adaptée à l'intention
    context = _build_context_block(final_chunks)
    unique_docs = list({c.get("filename", "unknown") for c in final_chunks})
    doc_list_str = ", ".join(f'"{d}"' for d in unique_docs)

    # ── Sprint 6+ : KG light enrichment ──
    kg_text = ""
    if getattr(settings, "kg_light_enabled", False):
        try:
            chunk_meta = [c.get("metadata") or {
                "loi_id": c.get("loi_id"),
                "article_id": c.get("article_id"),
            } for c in final_chunks if c.get("loi_id") or c.get("article_id")]
            if chunk_meta:
                kg_text = await graph_resolver.kg_context_for_rag(
                    db, chunk_meta, max_entities=getattr(settings, "kg_light_max_entities", 6)
                )
        except Exception as e:
            logger.warning("KG light enrichment failed (agentic): %s", e)

    context_message = CONTEXT_INJECTION_TEMPLATE.get(detected_lang, CONTEXT_INJECTION_TEMPLATE["en"]).format(
        num_sources=len(final_chunks),
        context=context,
        doc_list=doc_list_str,
    )
    if kg_text:
        context_message = f"【Informations structurées du graphe juridique】\n{kg_text}\n\n{context_message}"

    try:
        feedback_examples = await feedback_service.get_relevant_feedback_examples(
            db,
            question=question,
            detected_lang=detected_lang,
            limit=2,
            organization_id=organization_id,
        )
        feedback_block = _build_feedback_examples_block(feedback_examples, detected_lang)
        if feedback_block:
            context_message = f"{context_message}\n\n{feedback_block}"
    except Exception as e:
        logger.warning("Failed to load feedback examples: %s", e)

    question_templates = {
        "ar": USER_QUESTION_TEMPLATE_AR,
        "fr": USER_QUESTION_TEMPLATE_FR,
        "en": USER_QUESTION_TEMPLATE_EN,
    }
    user_question = question_templates.get(detected_lang, USER_QUESTION_TEMPLATE_EN).format(question=question)
    intent_instruction = _intent_suffix_instruction(intent, detected_lang)
    if intent_instruction:
        user_question = f"{user_question}\n\n{intent_instruction}"

    system_message = SYSTEM_PROMPT.get(detected_lang, SYSTEM_PROMPT["en"])

    # ── Sprint 6+ : inject domain persona suffix ──
    domain_suffix = getattr(domain_config, "system_prompt_suffix", "") if domain_config else ""
    if domain_suffix:
        system_message = f"{system_message}\n\n{domain_suffix}"

    # ── Case conversation context injection ──
    if case_id:
        try:
            from app.services.case_conversation_service import build_case_context_for_rag
            case_context_block = await build_case_context_for_rag(db, case_id, detected_lang=detected_lang)
            if case_context_block:
                system_message = f"{system_message}\n\n{case_context_block}"
                reasoning_steps.append("case_context_injected")
                logger.info("Injected case conversation context for case_id=%s (agentic)", case_id)
        except Exception as e:
            logger.warning("Failed to inject case conversation context (agentic): %s", e)

    messages = [{"role": "system", "content": system_message + "\n\n" + GROUNDING_REMINDER.get(detected_lang, GROUNDING_REMINDER["en"])}]

    if history:
        for msg in history[-20:]:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})

    # Inject uploaded document context (separate from RAG chunks)
    if document_context:
        doc_labels = {"fr": "Document joint fourni par l'utilisateur", "ar": "مستند مرفق من المستخدم", "en": "User-uploaded document"}
        doc_label = doc_labels.get(detected_lang, doc_labels["en"])
        messages.append({"role": "user", "content": f"[{doc_label}]\n\n{document_context}"})
        messages.append({"role": "assistant", "content": _get_ack_message(detected_lang)})

    messages.append({"role": "user", "content": context_message})
    messages.append({"role": "assistant", "content": _get_ack_message(detected_lang)})
    messages.append({"role": "user", "content": user_question})

    try:
        t_generation = time.perf_counter()
        answer = await _call_ollama(
            model=model_name,
            messages=messages,
            temperature=temperature,
            base_url=settings.llm_base_url,
        )
        generation_ms += (time.perf_counter() - t_generation) * 1000

        validation = _validate_answer_grounding(answer, final_chunks, detected_lang)
        if validation["unsupported_refs"]:
            reasoning_steps.append("answer_reground_retry")
            rewritten = await _rewrite_answer_grounded(
                settings=settings,
                model_name=model_name,
                detected_lang=detected_lang,
                lang_name=lang_name,
                lang_instruction=lang_instruction,
                context_message=context_message,
                question=question,
                initial_draft=answer,
            )
            rewritten_validation = _validate_answer_grounding(rewritten, final_chunks, detected_lang)

            if rewritten_validation["unsupported_refs"] or rewritten_validation["should_reground"]:
                if getattr(settings, "strict_grounded_only", False):
                    reasoning_steps.append("answer_reground_deterministic")
                    answer = _build_grounded_synthesis_from_chunks(
                        detected_lang,
                        question,
                        final_chunks,
                        rewritten_validation["answer_refs"],
                        rewritten_validation["supported_refs"],
                    )
                else:
                    reasoning_steps.append("answer_reground_kept_llm")
                    answer = _strip_unsupported_article_refs(
                        rewritten or answer,
                        validation["unsupported_refs"],
                    )
            else:
                reasoning_steps.append("answer_reground_recovered")
                answer = rewritten
        elif validation["should_reground"]:
            reasoning_steps.append("answer_reground_retry")
            rewritten = await _rewrite_answer_grounded(
                settings=settings,
                model_name=model_name,
                detected_lang=detected_lang,
                lang_name=lang_name,
                lang_instruction=lang_instruction,
                context_message=context_message,
                question=question,
                initial_draft=answer,
            )
            rewritten_validation = _validate_answer_grounding(rewritten, final_chunks, detected_lang)

            if rewritten_validation["should_reground"]:
                if getattr(settings, "strict_grounded_only", False):
                    reasoning_steps.append("answer_regrounded")
                    answer = _build_grounded_synthesis_from_chunks(
                        detected_lang,
                        question,
                        final_chunks,
                        rewritten_validation["answer_refs"],
                        rewritten_validation["supported_refs"],
                    )
                else:
                    reasoning_steps.append("answer_reground_kept_llm")
                    answer = rewritten
            else:
                reasoning_steps.append("answer_reground_recovered")
                answer = rewritten

        if _looks_like_prompt_leak(answer):
            reasoning_steps.append("prompt_leak_recovered")
            rewritten = await _rewrite_answer_grounded(
                settings=settings,
                model_name=model_name,
                detected_lang=detected_lang,
                lang_name=lang_name,
                lang_instruction=lang_instruction,
                context_message=context_message,
                question=question,
            )
            if _looks_like_prompt_leak(rewritten):
                if getattr(settings, "strict_grounded_only", False):
                    reasoning_steps.append("prompt_leak_fallback")
                    answer = _build_grounded_fallback(
                        detected_lang,
                        final_chunks,
                        set(),
                        _collect_supported_article_refs(final_chunks),
                    )
                else:
                    reasoning_steps.append("prompt_leak_kept_llm")
                    answer = rewritten
            else:
                answer = rewritten
    except Exception as e:
        error_messages = {
            "ar": f"خطأ في الاتصال بنموذج اللغة. {str(e)}",
            "fr": f"Erreur de communication avec le modèle. {str(e)}",
            "en": f"LLM communication error: {str(e)}",
        }
        return {
            "answer": error_messages.get(detected_lang, error_messages["en"]),
            "sources": _build_source_metadata(final_chunks),
            "model": model_name,
            "chunks_used": len(final_chunks),
            "reasoning_steps": reasoning_steps,
            "retrieval_attempts": retrieval_attempts,
            "rewritten_query": rewritten_query,
            "intent": intent,
            "route_decision": route_decision,
            "timings_ms": {
                "retrieval": round(retrieval_ms, 2),
                "generation": round(generation_ms, 2),
                "total": round((time.perf_counter() - t0) * 1000, 2),
            },
            "selected_mode": "agentic",
        }

    answer = _apply_final_language_guardrail(
        answer=answer,
        detected_lang=detected_lang,
        question=question,
        chunks=final_chunks,
        strict_grounded_only=getattr(settings, "strict_grounded_only", False),
    )

    # ── Sprint 6+ : quality guard ──
    qg_result = None
    if use_quality_guard is None:
        use_quality_guard = getattr(settings, "quality_guard_enabled", True)
    if use_quality_guard:
        try:
            qg_result = await audit_and_guard(
                question=question,
                answer=answer,
                chunks=final_chunks,
                lang=detected_lang,
                enabled=True,
            )
            answer = qg_result["answer"]
        except Exception as e:
            logger.warning("Quality guard audit failed (agentic): %s", e)

    return {
        "answer": answer,
        "sources": _build_source_metadata(final_chunks),
        "model": model_name,
        "chunks_used": len(final_chunks),
        "reasoning_steps": reasoning_steps,
        "retrieval_attempts": retrieval_attempts,
        "rewritten_query": rewritten_query,
        "intent": intent,
        "route_decision": route_decision,
        "timings_ms": {
            "retrieval": round(retrieval_ms, 2),
            "generation": round(generation_ms, 2),
            "total": round((time.perf_counter() - t0) * 1000, 2),
        },
        "selected_mode": "agentic",
        "domain": domain_name,
        "quality_guard_status": qg_result.get("status") if qg_result else None,
        "quality_guard_issues": qg_result.get("issues") if qg_result else None,
        "kg_enriched": bool(kg_text),
    }


async def ask_auto(
    db: Any,
    question: str,
    top_k: int = 5,
    language_filter: Optional[str] = None,
    response_language: Optional[str] = None,
    document_id: Optional[str] = None,
    llm_model: Optional[str] = None,
    temperature: float = 0.3,
    history: list[dict] | None = None,
    use_domain_router: bool = True,
    use_quality_guard: Optional[bool] = None,
    intent: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> dict:
    """Sélectionne automatiquement le mode classique ou agentique."""
    t0 = time.perf_counter()
    settings = get_settings()
    detected_lang = response_language if response_language in {"ar", "fr", "en"} else _detect_query_language(question)
    intent = _detect_intent(question, detected_lang)
    selected_mode, reason = _select_mode_for_auto(question, intent, settings)

    if selected_mode == "agentic":
        result = await ask_agentic(
            db,
            question=question,
            top_k=top_k,
            language_filter=language_filter,
            response_language=response_language,
            document_id=document_id,
            llm_model=llm_model,
            temperature=temperature,
            history=history,
            use_domain_router=use_domain_router,
            use_quality_guard=use_quality_guard,
            intent=intent,
            organization_id=organization_id,
        )
        result["selected_mode"] = "agentic"
        result["auto_reason"] = reason
        return result

    classic = await ask(
        db,
        question=question,
        top_k=top_k,
        language_filter=language_filter,
        response_language=response_language,
        document_id=document_id,
        llm_model=llm_model,
        temperature=temperature,
        history=history,
        use_domain_router=use_domain_router,
        use_quality_guard=use_quality_guard,
        intent=intent,
        organization_id=organization_id,
    )

    classic.update(
        {
            "reasoning_steps": [
                f"intent_detected:{intent}",
                "route_decision:classic_direct",
                "single_pass_generation",
            ],
            "retrieval_attempts": 1 if classic.get("chunks_used", 0) > 0 else 0,
            "rewritten_query": None,
            "intent": intent,
            "route_decision": "classic_direct",
            "timings_ms": {
                "retrieval": 0.0,
                "generation": 0.0,
                "total": round((time.perf_counter() - t0) * 1000, 2),
            },
            "selected_mode": "classic",
            "auto_reason": reason,
        }
    )
    return classic


def _backoff_delay(attempt: int, base: float, maximum: float) -> float:
    """Exponential backoff with jitter: base * 2^attempt + random jitter."""
    import random
    delay = min(base * (2 ** attempt), maximum)
    jitter = random.uniform(0, delay * 0.25)
    return delay + jitter


async def _call_ollama(
    model: str,
    messages: list[dict],
    temperature: float,
    base_url: str = "http://localhost:11434",
) -> str:
    """Appelle l'API native Ollama avec retry exponentiel et timeouts configurables."""
    settings = get_settings()
    url = f"{base_url}/api/chat"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
        "options": {
            "num_ctx": 8192,
            "top_p": 0.9,
        },
    }

    max_retries = settings.llm_max_retries
    timeout = httpx.Timeout(
        connect=settings.llm_timeout_connect,
        read=settings.llm_timeout_read,
        write=30.0,
        pool=10.0,
    )
    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                message = data.get("message")
                if not isinstance(message, dict):
                    raise RuntimeError(f"Malformed Ollama response: missing message object: {data!r}")
                content = message.get("content")
                if not isinstance(content, str):
                    raise RuntimeError(f"Malformed Ollama response: missing message content: {data!r}")
                return content
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError,
                    httpx.RemoteProtocolError, httpx.PoolTimeout) as e:
                last_error = e
                if attempt < max_retries:
                    delay = _backoff_delay(
                        attempt, settings.llm_backoff_base, settings.llm_backoff_max
                    )
                    logger.warning(
                        "Transient Ollama failure on attempt %s/%s: %r — retrying in %.1fs",
                        attempt, max_retries, e, delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "Ollama call failed after %s attempts: %r", max_retries, e,
                    )
                continue
            except httpx.HTTPStatusError as e:
                last_error = e
                if attempt < max_retries and e.response.status_code >= 500:
                    delay = _backoff_delay(
                        attempt, settings.llm_backoff_base, settings.llm_backoff_max
                    )
                    logger.warning(
                        "Ollama HTTP %s on attempt %s/%s — retrying in %.1fs",
                        e.response.status_code, attempt, max_retries, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error(
                    "Ollama returned HTTP %s (non-retryable): %s",
                    e.response.status_code, e,
                )
                raise

    if last_error is not None:
        raise last_error
    raise RuntimeError("Ollama call failed without explicit error")


async def call_ollama(
    model: str,
    messages: list[dict],
    temperature: float,
    base_url: str = "http://localhost:11434",
) -> str:
    """Public wrapper around _call_ollama — use this from other modules."""
    return await _call_ollama(
        model=model,
        messages=messages,
        temperature=temperature,
        base_url=base_url,
    )


async def _call_ollama_stream(
    model: str,
    messages: list[dict],
    temperature: float,
    base_url: str = "http://localhost:11434",
):
    """Streaming variant — yields content tokens as they arrive from Ollama."""
    settings = get_settings()
    url = f"{base_url}/api/chat"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
        "options": {
            "num_ctx": 8192,
            "top_p": 0.9,
        },
    }

    timeout = httpx.Timeout(
        connect=settings.llm_timeout_connect,
        read=settings.llm_timeout_read,
        write=30.0,
        pool=10.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = data.get("message")
                if isinstance(msg, dict):
                    token = msg.get("content", "")
                    if token:
                        yield token
                if data.get("done"):
                    break


async def ask_stream(
    db: Any,
    question: str,
    top_k: int = 5,
    language_filter: Optional[str] = None,
    document_id: Optional[str] = None,
    llm_model: Optional[str] = None,
    temperature: float = 0.3,
    history: list[dict] | None = None,
    use_domain_router: bool = True,
    use_quality_guard: Optional[bool] = None,
    intent: Optional[str] = None,
    organization_id: Optional[str] = None,
):
    """
    Streaming RAG pipeline — yields SSE events:
      event: sources   data: [...]     (sent first)
      event: token     data: "..."     (one per LLM token)
      event: done      data: {}        (final)
    """
    settings = get_settings()
    model_name = (llm_model or settings.llm_model).strip()
    detected_lang = _detect_query_language(question)
    lang_name, lang_instruction = _LANG_LABELS.get(detected_lang, _LANG_LABELS["en"])

    # ── Sprint 6+ : domain routing ──
    domain_name = "unknown"
    domain_config = None
    if getattr(settings, "domain_router_enabled", False) and use_domain_router:
        try:
            domain_name, domain_config = await route_question(
                question=question,
                lang=detected_lang,
                targeted_loi_code=document_id,
            )
        except Exception as e:
            logger.warning("Domain routing failed (stream): %s", e)

    effective_document_id, scope_reason = await _resolve_effective_document_id(
        db, question, detected_lang, document_id,
    )

    effective_language_filter = language_filter
    retrieval_query = _augment_query_for_specific_legal_scope(question, detected_lang)
    effective_top_k = getattr(domain_config, "top_k", top_k) if domain_config else top_k
    retrieval_k = min(max(effective_top_k * 3, effective_top_k + 5), 30)

    # ── Sprint 6+ : partitioned retrieval when intent hints at legal structure ──
    if intent and domain_config and getattr(settings, "partitioned_retrieval_enabled", True):
        try:
            chunks = await legal_retrieval_orchestrator.retrieve_partitioned(
                question=retrieval_query,
                intent=intent,
                search_fn=lambda q, top_k, extra_filter=None: search_service.semantic_search(
                    db, query=q, top_k=top_k,
                    language_filter=effective_language_filter,
                    document_id=effective_document_id,
                    extra_filter=extra_filter,
                    organization_id=organization_id,
                ),
                db=db,
                domain_config=domain_config,
            )
        except Exception as e:
            logger.warning("Partitioned retrieval failed (stream), falling back: %s", e)
            chunks = await search_service.semantic_search(
                db,
                query=retrieval_query,
                top_k=retrieval_k,
                language_filter=effective_language_filter,
                document_id=effective_document_id,
                organization_id=organization_id,
            )
    else:
        chunks = await search_service.semantic_search(
            db,
            query=retrieval_query,
            top_k=retrieval_k,
            language_filter=effective_language_filter,
            document_id=effective_document_id,
            organization_id=organization_id,
        )

    if not chunks:
        no_result_messages = {
            "ar": "لم أجد وثائق ذات صلة بسؤالك في قاعدة البيانات.",
            "fr": "Je n'ai trouvé aucun document pertinent pour votre question.",
            "en": "No relevant documents found for your question.",
        }
        yield {"event": "sources", "data": json.dumps([])}
        yield {"event": "token", "data": json.dumps(no_result_messages.get(detected_lang, no_result_messages["en"]))}
        yield {"event": "done", "data": json.dumps({"model": model_name, "chunks_used": 0})}
        return

    chunks = _rerank_chunks_for_question(question, chunks, detected_lang, domain_config=domain_config)[:effective_top_k]
    reranking_service = _get_reranking_service()
    if await reranking_service.is_available():
        chunks = await reranking_service.rerank(question, chunks)

    # Send sources immediately so the UI can show them while generating
    yield {"event": "sources", "data": json.dumps(_build_source_metadata(chunks))}

    # Build context and messages (same as classic ask)
    context = _build_context_block(chunks)
    unique_docs = list({c.get("filename", "unknown") for c in chunks})
    doc_list_str = ", ".join(f'"{d}"' for d in unique_docs)

    # ── Sprint 6+ : KG light enrichment ──
    kg_text = ""
    if getattr(settings, "kg_light_enabled", False):
        try:
            chunk_meta = [c.get("metadata") or {
                "loi_id": c.get("loi_id"),
                "article_id": c.get("article_id"),
            } for c in chunks if c.get("loi_id") or c.get("article_id")]
            if chunk_meta:
                kg_text = await graph_resolver.kg_context_for_rag(
                    db, chunk_meta, max_entities=getattr(settings, "kg_light_max_entities", 6)
                )
        except Exception as e:
            logger.warning("KG light enrichment failed (stream): %s", e)

    context_message = CONTEXT_INJECTION_TEMPLATE.get(detected_lang, CONTEXT_INJECTION_TEMPLATE["en"]).format(
        num_sources=len(chunks), context=context, doc_list=doc_list_str,
    )
    if kg_text:
        context_message = f"【Informations structurées du graphe juridique】\n{kg_text}\n\n{context_message}"

    question_templates = {"ar": USER_QUESTION_TEMPLATE_AR, "fr": USER_QUESTION_TEMPLATE_FR, "en": USER_QUESTION_TEMPLATE_EN}
    user_question = question_templates.get(detected_lang, USER_QUESTION_TEMPLATE_EN).format(question=question)
    system_message = SYSTEM_PROMPT.get(detected_lang, SYSTEM_PROMPT["en"])

    # ── Sprint 6+ : inject domain persona suffix ──
    domain_suffix = getattr(domain_config, "system_prompt_suffix", "") if domain_config else ""
    if domain_suffix:
        system_message = f"{system_message}\n\n{domain_suffix}"

    messages = [{"role": "system", "content": system_message + "\n\n" + GROUNDING_REMINDER.get(detected_lang, GROUNDING_REMINDER["en"])}]
    if history:
        for msg in history[-20:]:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": context_message})
    messages.append({"role": "assistant", "content": _get_ack_message(detected_lang)})
    messages.append({"role": "user", "content": user_question})

    # Stream tokens
    try:
        async for token in _call_ollama_stream(
            model=model_name,
            messages=messages,
            temperature=temperature,
            base_url=settings.llm_base_url,
        ):
            yield {"event": "token", "data": json.dumps(token)}
    except Exception as e:
        logger.error("Streaming LLM error: %s", e)
        yield {"event": "error", "data": json.dumps(str(e))}

    # NOTE: Quality guard (audit_and_guard) is intentionally NOT run in streaming
    # mode. Streaming yields tokens incrementally — the full answer is not available
    # until the stream completes on the client side. Post-stream auditing would
    # require buffering the entire response, negating the streaming benefit.
    # For audited answers, use the classic (/ask) or agentic (/ask-agentic) endpoints.
    yield {
        "event": "done",
        "data": json.dumps({
            "model": model_name,
            "chunks_used": len(chunks),
            "domain": domain_name,
            "kg_enriched": bool(kg_text),
            "quality_guard_status": "skipped_streaming",
        })
    }


def _get_ack_message(lang: str) -> str:
    """Petit message d'accusé de réception avant la vraie question."""
    ack = {
        "ar": "تم استلام الوثائق. أنا جاهز للإجابة على سؤالك باللغة العربية بناءً على المصادر المقدمة فقط.",
        "fr": "Documents reçus. Je suis prêt à répondre à votre question en français en me basant uniquement sur les sources fournies.",
        "en": "Documents received. I'm ready to answer your question in English based solely on the provided sources.",
    }
    return ack.get(lang, ack["en"])


# ─────────────────────────────────────────────────────────────
# Extraction des exigences (Sprint 1)
# ─────────────────────────────────────────────────────────────

EXIGENCE_EXTRACTION_PROMPT = """You are a **Tunisian legal compliance expert** specializing in regulatory requirement extraction.

Your task is to analyze the following legal article text and extract **all regulatory requirements**.

For the given article, identify and list:

1. **OBLIGATIONS** — Actions that are mandatory (explicit "doit", "est tenu", "must", "يجب")
2. **PROHIBITIONS** — Actions that are forbidden (explicit "il est interdit", "cannot", "لا يجوز")
3. **CONDITIONS** — Conditional statements or applicability requirements
4. **SANCTIONS** — Penalties, fines, or consequences for non-compliance

**IMPORTANT RULES:**
- Extract ONLY requirements that are EXPLICITLY stated in the article text.
- Do NOT infer, generalize, or add implied requirements.
- For each requirement, provide:
  - **Type** (obligation|prohibition|condition|sanction)
  - **Text** (exact quotation or precise paraphrase from the article)
  - **Confidence** (high|medium|low)

**Output format** — JSON array, one requirement per object:
```json
[
  {
    "type": "obligation|prohibition|condition|sanction",
    "text": "Exact requirement from the article",
    "confidence": "high|medium|low",
    "rationale": "Brief explanation why this is extracted"
  }
]
```

If the article text contains NO regulatory requirements, return an empty array: `[]`

---

**Article text to analyze:**
{article_text}

---

Extract requirements now. Return ONLY valid JSON array (no markdown, no extra text)."""


async def extract_exigences_from_text(
    article_text: str,
    article_reference: str = "Unknown",
    base_url: str = "http://localhost:11434",
    model: str = None,
) -> list[dict]:
    """
    Extrait les exigences réglementaires d'un article à l'aide du LLM.

    La fonction retourne une liste de dictionnaires avec:
    type, text, confidence, rationale et article_reference.
    """
    if model is None:
        model = get_settings().llm_model

    if not article_text or len(article_text.strip()) < 20:
        return []

    prompt = EXIGENCE_EXTRACTION_PROMPT.format(article_text=article_text)

    messages = [
        {"role": "user", "content": prompt}
    ]

    try:
        response = await _call_ollama(
            model=model,
            messages=messages,
            temperature=0.1,  # Low temperature for consistent extraction
            base_url=base_url,
        )

        # Parse JSON response
        response = response.strip()

        # Try to extract JSON array from response
        if not response.startswith('['):
            # Look for JSON array in response
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                response = match.group(0)
            else:
                logger.warning("No JSON array found in LLM response for article %s", article_reference)
                return []

        exigences = json.loads(response)

        if not isinstance(exigences, list):
            logger.warning("LLM response is not a list for article %s", article_reference)
            return []

        # Enrich with article reference and validate
        enriched = []
        for exig in exigences:
            if not isinstance(exig, dict):
                continue

            exig_type = str(exig.get("type", "")).lower().strip()
            if exig_type not in ("obligation", "prohibition", "condition", "sanction"):
                continue

            text = str(exig.get("text", "")).strip()
            if len(text) < 5:
                continue

            enriched.append({
                "type": exig_type,
                "text": text,
                "confidence": str(exig.get("confidence", "medium")).lower().strip(),
                "rationale": str(exig.get("rationale", "")).strip(),
                "article_reference": article_reference,
            })

        logger.info("Extracted %d exigences from article %s", len(enriched), article_reference)
        return enriched

    except json.JSONDecodeError as e:
        logger.error("JSON parse error extracting exigences from %s: %s", article_reference, e)
        return []
    except Exception as e:
        logger.error("Error extracting exigences from %s: %s", article_reference, e)
        return []

