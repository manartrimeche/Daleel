"""
Derja Normalizer — Tunisian dialect pre-processor for Daleel.

Detects Tunisian Arabic dialect (Derja / دارجة تونسية) in user queries
and normalizes them to French before they enter the RAG pipeline.

Why French and not MSA?
  Tests show Qwen 2.5:7b handles French far better than Arabic.
  The legal corpus is predominantly in French.  Normalizing derja → French
  gives the best retrieval AND generation quality.

Architecture:
  1. detect_derja()   — heuristic: does the text contain derja markers?
  2. normalize_query() — replace derja tokens → French, restructure sentence
  3. The caller (llm_service.ask / autonomous_agent.run) invokes
     normalize_if_derja() which combines detection + normalization and
     returns (normalized_query, original_query, is_derja).

The original query is kept so the answer can acknowledge the user's
dialect if needed.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Derja → French dictionary
# ═══════════════════════════════════════════════════════════════════════════════
# Each entry: derja_form → French equivalent.
# Ordered longest-first at compile time to avoid partial matches.

_DERJA_DICT: dict[str, str] = {
    # ── Interrogatives & connectors ──
    "شنوة": "quoi / que",
    "شنو": "quoi / que",
    "شنوا": "quoi / que",
    "آش": "que / quoi",
    "علاش": "pourquoi",
    "وقتاش": "quand",
    "كيفاش": "comment",
    "وين": "où",
    "شكون": "qui",
    "قداش": "combien",
    "أشنو": "quoi",
    "شني": "quoi",

    # ── Verbs — common Tunisian forms ──
    "نحب": "je veux",
    "نحبّ": "je veux",
    "يحب": "il veut",
    "تحب": "elle veut / tu veux",
    "نجّم": "je peux",
    "نجم": "je peux",
    "يجّم": "il peut",
    "ينجّم": "il peut",
    "ننجّم": "je peux",
    "نعرف": "je sais / je connais",
    "نخدم": "je travaille",
    "خدّام": "je travaille / employé",
    "يخدم": "il travaille",
    "تخدم": "elle travaille",
    "نمشي": "j'aller / je vais",
    "مشيت": "je suis allé",
    "نعمل": "je fais",
    "نعملو": "nous faisons",
    "عملت": "j'ai fait",
    "خلّص": "payer",
    "خلّصني": "il m'a payé",
    "ما خلّصنيش": "il ne m'a pas payé",
    "عطاوني": "ils m'ont donné",
    "ما عطاونيش": "ils ne m'ont pas donné",
    "عطاني": "il m'a donné",
    "ما عطانيش": "il ne m'a pas donné",
    "طردوني": "ils m'ont licencié",
    "طردني": "il m'a licencié",
    "سكّروا": "ils ont fermé",
    "حلّوا": "ils ont ouvert",
    "فتحوا": "ils ont ouvert",
    "نفتح": "j'ouvre / je crée",
    "نسكّر": "je ferme",
    "نشكي": "je porte plainte / je dépose une plainte",
    "شكيت": "j'ai porté plainte",
    "نقاضي": "je poursuis en justice",
    "نوقّع": "je signe",
    "وقّعت": "j'ai signé",
    "نخلّص": "je paie",
    "ندفع": "je paie",
    "نستنّى": "j'attends",
    "قالولي": "ils m'ont dit",
    "قالّي": "il m'a dit",

    # ── Negation patterns ──
    "ما": "ne ... pas",
    "ماش": "ne ... pas",
    "مانيش": "je ne suis pas",
    "ماهوش": "il n'est pas / ce n'est pas",
    "ماهيش": "elle n'est pas",

    # ── Nouns — legal & work context ──
    "باتروني": "mon employeur / mon patron",
    "باترون": "employeur / patron",
    "الباترون": "l'employeur",
    "خدمة": "travail / emploi",
    "عقد خدمة": "contrat de travail",
    "الخدمة": "le travail",
    "بلاصة": "poste / place",
    "بلاصت خدمة": "poste de travail",
    "للتفقدية": "à l'inspection du travail",
    "التفقدية": "l'inspection du travail",
    "تفقدية الشغل": "inspection du travail",
    "الشغل": "le travail",
    "المحكمة": "le tribunal",
    "الحاكم": "le juge",
    "المحامي": "l'avocat",
    "محامي": "avocat",
    "الحقوق": "les droits",
    "حقوقي": "mes droits",
    "الصلح": "la conciliation",
    "مجلس التأديب": "conseil de discipline",
    "الكناس": "la CNSS (sécurité sociale)",
    "CNSS": "CNSS",
    "الضمان الاجتماعي": "la sécurité sociale",
    "الشركة": "l'entreprise / la société",
    "شركة": "entreprise / société",
    "المصنع": "l'usine",
    "الحانوت": "le magasin / le commerce",
    "الفلوس": "l'argent / le salaire",
    "السوالار": "le salaire",
    "المعاش": "la pension / la retraite",
    "العطلة": "le congé / les vacances",
    "عطلة مرضية": "congé maladie",
    "عطلة سنوية": "congé annuel",
    "ساعات الخدمة": "heures de travail",
    "ساعات إضافية": "heures supplémentaires",
    "التعويض": "l'indemnité",
    "تعويض": "indemnité",
    "التقاعد": "la retraite",
    "الطرد": "le licenciement",
    "طرد تعسفي": "licenciement abusif",
    "الاستقالة": "la démission",
    "العقد": "le contrat",
    "عقد": "contrat",
    "الوثائق": "les documents",
    "وثيقة": "document",
    "الوصل": "le reçu",
    "كشف الخلاص": "bulletin de paie",
    "بطاقة خلاص": "fiche de paie",
    "رخصة": "autorisation / licence",
    "ضريبة": "impôt",
    "الضرائب": "les impôts",
    "باتندا": "patente (taxe professionnelle)",

    # ── Time expressions ──
    "شهور": "mois",
    "شهر": "mois",
    "عام": "année",
    "سنة": "année",
    "سنين": "années",
    "يوم": "jour",
    "أيام": "jours",
    "جمعة": "semaine",
    "الليلة": "ce soir / aujourd'hui",
    "غدوة": "demain",
    "البارح": "hier",
    "توّا": "maintenant",
    "من بعد": "après",
    "قبل": "avant",

    # ── Prepositions & adverbs ──
    "باش": "pour / afin de",
    "فيسع": "vite / rapidement",
    "ياسر": "beaucoup",
    "برشا": "beaucoup",
    "شوية": "un peu",
    "زادة": "aussi / également",
    "كان": "si / seulement",
    "بالحق": "mais / cependant",
    "أما": "mais",
    "خاطر": "parce que",
    "على خاطر": "parce que",
    "كيف": "comme / quand",
    "كيما": "comme",
    "عند": "chez / avoir",
    "عندي": "j'ai",
    "عندو": "il a",
    "عندها": "elle a",
    "ماعنديش": "je n'ai pas",
    "مع": "avec",
    "متاع": "de / appartenant à",
    "متاعي": "mon / ma / le mien",

    # ── Common phrases ──
    "شنوة نعمل": "que dois-je faire",
    "شنوة الحل": "quelle est la solution",
    "شنوة الإجراءات": "quelles sont les procédures",
    "ما نجّمش": "je ne peux pas",
    "لازمني": "j'ai besoin de / il me faut",
    "يلزمني": "j'ai besoin de",
    "لازم": "il faut",
    "يلزم": "il faut",
    "موش عادل": "ce n'est pas juste",
    "حرام عليه": "c'est injuste",
    "واش": "est-ce que",
    "هل نجّم": "est-ce que je peux",
}

# Compile sorted patterns (longest first to avoid partial matches)
_DERJA_PATTERNS: list[tuple[re.Pattern, str]] = []
for _derja, _french in sorted(_DERJA_DICT.items(), key=lambda x: len(x[0]), reverse=True):
    # Word-boundary-aware pattern
    # Arabic doesn't use \b well, so we use lookahead/lookbehind for non-Arabic chars
    _pat = re.compile(
        r"(?<![ء-ي])" + re.escape(_derja) + r"(?![ء-ي])",
        re.UNICODE,
    )
    _DERJA_PATTERNS.append((_pat, _french))


# ═══════════════════════════════════════════════════════════════════════════════
# Derja detection markers — words/forms that only appear in Tunisian dialect
# ═══════════════════════════════════════════════════════════════════════════════

_DERJA_MARKERS = re.compile(
    r"(?:"
    # Interrogatives unique to Tunisian
    r"شنوة|شنو|شنوا|آش(?:نو)?|علاش|وقتاش|كيفاش|قداش"
    r"|"
    # Verbs with Tunisian conjugation (prefix ن for 1st person)
    r"نحب|نجّم|نجم|ننجّم|نخدم|نمشي|نعمل|نقاضي|نشكي|نسكّر|نفتح|نوقّع|نخلّص"
    r"|"
    # Negation pattern: ما...ش (ma...sh)
    r"ما\s*\S+ش\b|مانيش|ماهوش|ماهيش|ماعنديش"
    r"|"
    # Tunisian-specific nouns
    r"باتروني?|التفقدية|الكناس|السوالار|باتندا|الفلوس|بلاصة|خدّام"
    r"|"
    # Connectors / adverbs unique to derja
    r"باش|ياسر|برشا|فيسع|توّا|غدوة|البارح|على\s*خاطر|بالحق|متاع[يو]?"
    r"|"
    # Common phrases
    r"شنوة\s+نعمل|شنوة\s+الحل|هل\s+نجّم|لازمني|يلزمني"
    r")",
    re.UNICODE,
)

# Minimum markers to trigger derja detection
_MIN_DERJA_MARKERS = 2

# Arabic Unicode block (same as text_utils)
_ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════


def detect_derja(text: str) -> bool:
    """
    Detect whether *text* contains Tunisian dialect (Derja).

    Returns True if at least _MIN_DERJA_MARKERS distinct derja markers are found
    AND the text contains Arabic script characters.
    """
    if not text or not text.strip():
        return False

    # Must contain Arabic characters
    if len(_ARABIC_RE.findall(text)) < 2:
        return False

    # Count distinct marker matches
    matches = _DERJA_MARKERS.findall(text)
    return len(matches) >= _MIN_DERJA_MARKERS


def normalize_derja_to_french(text: str) -> str:
    """
    Replace known Tunisian dialect tokens with their French equivalents.

    The result is a hybrid Arabic/French sentence that the LLM can understand.
    For best results, the full query should be wrapped with a clarifying prompt.
    """
    result = text

    for pattern, replacement in _DERJA_PATTERNS:
        result = pattern.sub(replacement, result)

    # Clean up multiple spaces
    result = re.sub(r"\s{2,}", " ", result).strip()

    return result


def build_derja_context_note(original: str, normalized: str) -> str:
    """
    Build a context note that helps the LLM understand the original was
    in Tunisian dialect and has been normalized.

    This is injected into the user message so the LLM has both the
    original intent and the French translation.
    """
    return (
        f"[L'utilisateur a posé sa question en dialecte tunisien (derja). "
        f"Voici la question originale : « {original} ». "
        f"Traduction approximative en français : « {normalized} ». "
        f"Réponds en français de manière claire et professionnelle.]"
    )


def normalize_if_derja(text: str) -> tuple[str, str, bool]:
    """
    Main entry point for the Daleel pipeline.

    Returns:
        (effective_query, original_query, is_derja)

    - If derja is detected: effective_query contains the French-normalized
      version wrapped with a context note.  original_query is preserved.
    - If not derja: effective_query == original_query, is_derja is False.
    """
    if not detect_derja(text):
        return text, text, False

    normalized = normalize_derja_to_french(text)

    logger.info(
        "Derja detected — normalizing query.\n  Original : %s\n  Normalized: %s",
        text,
        normalized,
    )

    effective = build_derja_context_note(text, normalized)

    return effective, text, True
