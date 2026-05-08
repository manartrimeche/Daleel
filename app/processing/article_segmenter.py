"""
Article-level segmentation for French and Arabic legal texts.

Produces one structured unit per article, with full hierarchy tracking
(Titre → Chapitre → Section → Article).

Each result dict contains:
  article_number   : "95" | "95 bis"
  article_key      : "CT-Art-95"  (loi_code + article_number)
  article_heading  : "Article 95 — De l'obligation de sécurité"
  text             : full article text (heading included)
  hierarchy        : {titre, chapitre, section}
  pages            : [45, 46]   (list of page numbers spanned)
  char_start       : int
  char_end         : int
  language         : "fr" | "ar"
"""

import re
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# ── Arabic digit normalisation ──────────────────────────────────────────────
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def _norm_num(s: str) -> str:
    """Convert Arabic-Indic digits to Western digits and strip whitespace."""
    return s.translate(_ARABIC_DIGITS).strip()


# ── Hierarchy patterns (French) ─────────────────────────────────────────────
_TITRE_FR = re.compile(
    r"^[ \t]*(?:TITRE|Titre)\s+((?:[IVXivx]+|\d+)\b[^\n]{0,120})",
    re.MULTILINE,
)
_CHAPITRE_FR = re.compile(
    r"^[ \t]*(?:CHAPITRE|Chapitre)\s+((?:[IVXivx]+|\d+)\b[^\n]{0,120})",
    re.MULTILINE,
)
_SECTION_FR = re.compile(
    r"^[ \t]*(?:Section|SECTION|Sous-section|Sous-Section)\s+((?:[IVXivx]+|\d+)\b[^\n]{0,120})",
    re.MULTILINE,
)

# ── Hierarchy patterns (Arabic) ─────────────────────────────────────────────
_TITRE_AR = re.compile(
    r"^[ \t]*(?:الباب|باب)\s+([^\n]{1,120})",
    re.MULTILINE,
)
_CHAPITRE_AR = re.compile(
    r"^[ \t]*(?:القسم|قسم|الجزء|جزء)\s+([^\n]{1,120})",
    re.MULTILINE,
)
_SECTION_AR = re.compile(
    r"^[ \t]*(?:الفرع|فرع)\s+([^\n]{1,120})",
    re.MULTILINE,
)

# ── Article patterns ────────────────────────────────────────────────────────
# French: "Article 95", "Article 95 bis", "Art. 95"
_ARTICLE_FR = re.compile(
    r"^[ \t]*(?:Article|Art\.?)\s+"
    r"(\d+(?:\s*bis|\s*ter|\s*quater|\s*quinquies|\-\d+)?)"
    r"\b([^\n]{0,200})?$",
    re.MULTILINE | re.IGNORECASE,
)

# Arabic: "الفصل 95", "فصل 95", "المادة 95", "مادة 95"
_ARTICLE_AR = re.compile(
    r"^[ \t]*(?:الفصل|فصل|المادة|مادة)\s+"
    r"([\d٠-٩]+(?:\s*(?:مكرر|ثانيًا|ثالثًا))?)"
    r"\b([^\n]{0,200})?$",
    re.MULTILINE,
)


# ── Event types ─────────────────────────────────────────────────────────────
_EVT_TITRE = "titre"
_EVT_CHAPITRE = "chapitre"
_EVT_SECTION = "section"
_EVT_ARTICLE = "article"

# Hierarchy reset map: when we see X, reset all levels below X
_RESETS = {
    _EVT_TITRE:    {_EVT_CHAPITRE, _EVT_SECTION},
    _EVT_CHAPITRE: {_EVT_SECTION},
    _EVT_SECTION:  set(),
}


def _build_events(text: str, language: str) -> List[Tuple[int, str, str, str]]:
    """
    Scan *text* for all hierarchy + article markers.

    Returns a list of (position, event_type, raw_number_or_heading, full_line)
    sorted by position ascending.
    """
    events: List[Tuple[int, str, str, str]] = []

    def _add(pattern: re.Pattern, evt_type: str, group_num: int = 1):
        for m in pattern.finditer(text):
            raw = (m.group(group_num) or "").strip()
            full_line = text[m.start(): text.find("\n", m.start())].strip() if "\n" in text[m.start():] else text[m.start():].strip()
            events.append((m.start(), evt_type, raw, full_line))

    if language in ("fr", "fr+ar", "unknown"):
        _add(_TITRE_FR, _EVT_TITRE)
        _add(_CHAPITRE_FR, _EVT_CHAPITRE)
        _add(_SECTION_FR, _EVT_SECTION)
        _add(_ARTICLE_FR, _EVT_ARTICLE)

    if language in ("ar", "fr+ar"):
        _add(_TITRE_AR, _EVT_TITRE)
        _add(_CHAPITRE_AR, _EVT_CHAPITRE)
        _add(_SECTION_AR, _EVT_SECTION)
        _add(_ARTICLE_AR, _EVT_ARTICLE)

    # For unknown/ambiguous docs, try both
    if language == "unknown":
        _add(_TITRE_AR, _EVT_TITRE)
        _add(_CHAPITRE_AR, _EVT_CHAPITRE)
        _add(_SECTION_AR, _EVT_SECTION)
        _add(_ARTICLE_AR, _EVT_ARTICLE)

    events.sort(key=lambda e: e[0])
    return events


def _chars_to_pages(
    char_start: int,
    char_end: int,
    page_map: List[Tuple[int, int, int]],
) -> List[int]:
    """Return sorted list of page numbers that overlap [char_start, char_end)."""
    pages = set()
    for seg_start, seg_end, page_num in page_map:
        if seg_start < char_end and seg_end > char_start:
            pages.add(page_num)
    return sorted(pages)


def _make_article_key(loi_code: str, article_number: str) -> str:
    """Generate a stable unique key: e.g. 'CT-Art-95', 'CT-Art-95bis'."""
    # Normalize: collapse spaces, remove internal spaces
    num_clean = re.sub(r"\s+", "", article_number.strip())
    return f"{loi_code.upper()}-Art-{num_clean}"


def _detect_language(text: str) -> str:
    """Lightweight language detector for article text."""
    arabic = len(re.findall(r"[\u0600-\u06FF]", text))
    latin = len(re.findall(r"[a-zA-ZÀ-ÿ]", text))
    total = arabic + latin
    if total == 0:
        return "unknown"
    ratio = arabic / total
    if ratio > 0.60:
        return "ar"
    if ratio < 0.25:
        return "fr"
    return "fr+ar"


def segment_text_into_articles(
    full_text: str,
    loi_code: str,
    page_map: List[Tuple[int, int, int]],
    language: str = "fr",
) -> List[Dict]:
    """
    Segment a full legal document text into article-level units.

    Args:
        full_text : Concatenation of all cleaned pages (see build_page_map helper).
        loi_code  : Short code for the loi (e.g. "CT", "CS", "LP63").
        page_map  : List of (char_start, char_end, page_number) tuples.
        language  : Expected language hint ("fr" | "ar" | "fr+ar").

    Returns:
        List of article dicts (see module docstring for schema).
    """
    if not full_text.strip():
        return []

    events = _build_events(full_text, language)
    if not events:
        logger.warning(f"[{loi_code}] No article markers found in text ({len(full_text)} chars)")
        return []

    # ── Walk events, maintaining hierarchy state ──
    hierarchy: Dict[str, Optional[str]] = {
        _EVT_TITRE: None,
        _EVT_CHAPITRE: None,
        _EVT_SECTION: None,
    }

    pending_article: Optional[Dict] = None
    results: List[Dict] = []

    def _close_article(end_pos: int):
        nonlocal pending_article
        if pending_article is None:
            return
        art_text = full_text[pending_article["char_start"]: end_pos].strip()
        if len(art_text) < 10:
            pending_article = None
            return
        pending_article["text"] = art_text
        pending_article["char_end"] = end_pos
        pending_article["pages"] = _chars_to_pages(
            pending_article["char_start"], end_pos, page_map
        )
        pending_article["language"] = _detect_language(art_text)
        results.append(pending_article)
        pending_article = None

    for pos, evt_type, raw, full_line in events:
        if evt_type == _EVT_ARTICLE:
            # Close any open article
            _close_article(pos)
            # Start new article
            num_norm = _norm_num(raw)
            heading = full_line if full_line else f"Article {num_norm}"
            pending_article = {
                "article_number": num_norm,
                "article_key": _make_article_key(loi_code, num_norm),
                "article_heading": heading,
                "hierarchy": {
                    "titre": hierarchy[_EVT_TITRE],
                    "chapitre": hierarchy[_EVT_CHAPITRE],
                    "section": hierarchy[_EVT_SECTION],
                },
                "char_start": pos,
                "char_end": pos,
                "pages": [],
                "text": "",
                "language": language,
            }
        else:
            # Hierarchy event — close open article if it's a higher-level marker
            if evt_type in (_EVT_TITRE, _EVT_CHAPITRE):
                _close_article(pos)
            # Update hierarchy state
            hierarchy[evt_type] = full_line if full_line else raw
            # Reset lower levels
            for lower in _RESETS.get(evt_type, set()):
                hierarchy[lower] = None

    # Close the last article
    _close_article(len(full_text))

    # ── Deduplicate by article_key (keep first occurrence) ──
    seen_keys: set = set()
    unique: List[Dict] = []
    for art in results:
        k = art["article_key"]
        if k not in seen_keys:
            seen_keys.add(k)
            unique.append(art)
        else:
            logger.debug(f"[{loi_code}] Duplicate article_key skipped: {k}")

    logger.info(f"[{loi_code}] Segmented {len(unique)} articles from {len(full_text):,} chars")
    return unique


def build_page_map(
    cleaned_pages: List[Dict],
) -> Tuple[str, List[Tuple[int, int, int]]]:
    """
    Concatenate cleaned page dicts into a single string and build a page map.

    Args:
        cleaned_pages: List of dicts with keys 'page_number' and 'cleaned_text'
                       (or ORM objects with the same attributes).

    Returns:
        (full_text, page_map)
        page_map: List of (char_start, char_end, page_number) tuples.
    """
    page_map: List[Tuple[int, int, int]] = []
    parts: List[str] = []
    offset = 0

    for page in cleaned_pages:
        # Support both dicts and ORM objects
        if isinstance(page, dict):
            page_num = page.get("page_number", 0)
            text = page.get("cleaned_text", "") or ""
        else:
            page_num = getattr(page, "page_number", 0)
            text = getattr(page, "cleaned_text", "") or ""

        start = offset
        chunk = text + "\n\n"
        parts.append(chunk)
        offset += len(chunk)
        page_map.append((start, offset, page_num))

    return "".join(parts), page_map
