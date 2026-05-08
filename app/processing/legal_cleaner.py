"""
Legal document noise cleaner — Sprint 4 (Step 3 of the workflow).

Removes structural/editorial noise from legal texts while rigorously
preserving all juridical content.

Noise suppressed:
  ✗ Repetitive headers and footers (detected via cross-page frequency analysis)
  ✗ Isolated page numbers  (e.g., a line containing only "47")
  ✗ Decorative separators  (lines of dashes, stars, underscores…)
  ✗ Non-normative editorial notes ("Paru au JORT n°…", "Erratum", "Rectificatif…")
  ✗ Publisher colophons (printing/edition notices)

Juridical content always preserved (whitelist):
  ✓ Amendment markers : "Modifié par", "Ajouté par", "Abrogé par"…
  ✓ Legal references  : "Loi n°", "Décret n°", "Article N"…
  ✓ Dates of entry into force
  ✓ Arabic equivalents of the above
"""

import re
import logging
from collections import Counter
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# ── Whitelist patterns (always preserve) ────────────────────────────────────

_PRESERVE_PATTERNS: list[re.Pattern] = [
    # FR amendment markers
    re.compile(
        r"\b(?:Modif[ié]|Ajout[ée]|Abrog[ée]|Remplac[ée]|Ins[eé]r[ée]|Supprim[ée])\s+"
        r"(?:par|selon|en vertu|au sens)",
        re.IGNORECASE,
    ),
    # FR legal references
    re.compile(
        r"\b(?:Loi|D[eé]cret|Arr[eê]t[eé]|Code|Ordonnance)\s+(?:n[o°]|num[eé]ro)?\s*"
        r"[\d]{2,}[\-/][\d]+",
        re.IGNORECASE,
    ),
    # Article headings (FR + AR)
    re.compile(
        r"^[ \t]*(?:Article|Art\.?|الفصل|المادة|فصل|مادة)\s+\d",
        re.IGNORECASE | re.MULTILINE,
    ),
    # Dates mentioning entry into force
    re.compile(r"\b(?:entr[eé]e? en vigueur|applicable|publié|date d'effet)\b", re.IGNORECASE),
    # AR amendment markers
    re.compile(r"\b(?:عُدِّل|أُضيف|أُلغي|استُبدل)\b"),
    # Explicit section/titre headings
    re.compile(
        r"^[ \t]*(?:TITRE|Titre|CHAPITRE|Chapitre|Section|الباب|القسم|الفرع)\s+",
        re.IGNORECASE | re.MULTILINE,
    ),
]

# ── Noise patterns (to suppress) ────────────────────────────────────────────

# A line that is ONLY a number (possibly flanked by dashes or spaces)
_PAGE_NUMBER_RE = re.compile(r"^\s*[-–—]?\s*\d{1,4}\s*[-–—]?\s*$")

# A line made entirely of non-alphanumeric / decorative characters
_DECORATION_RE = re.compile(r"^[\s\-─═_=\*•·~◦○●▪▫□■▬►◄«»\u2500-\u257F]+$")

# Non-normative editorial / JORT publishing notes
_EDITORIAL_RE = re.compile(
    r"(?:"
    r"Paru au\b|"
    r"Journal\s+Officiel\b|"
    r"J\.?O\.?R\.?T\.?\b|"
    r"Rectificatif\b|"
    r"Erratum\b|"
    r"Errata\b|"
    r"Note\s+de\s+la\s+r[eé]daction|"
    r"Note\s+d['\u2019]ordre|"
    r"(?:Imprim|Edition|Édition|Tirage)\b.*(?:officiel|national|tunis|SODIPER)\b"
    r")",
    re.IGNORECASE,
)

# Arabic editorial noise
_EDITORIAL_AR_RE = re.compile(
    r"(?:"
    r"نُشر في الرائد الرسمي|"
    r"الرائد الرسمي للجمهورية التونسية|"
    r"تصحيح خطأ|"
    r"ملاحظة التحرير"
    r")"
)

# Very short meaningless lines (1-3 non-arabic, non-latin chars, mostly punctuation)
_JUNK_LINE_RE = re.compile(r"^[\s\(\)\[\]\{\}\.,;:\!\?\/\\\|@#\$%\^&\*\+\=<>]{1,4}$")


# ── Public API ───────────────────────────────────────────────────────────────

def _should_preserve(line: str) -> bool:
    """Return True if a line must never be removed (whitelist check)."""
    for pat in _PRESERVE_PATTERNS:
        if pat.search(line):
            return True
    return False


def detect_repeated_elements(pages_texts: List[str], threshold_ratio: float = 0.30) -> set[str]:
    """
    Cross-page frequency analysis: find lines that appear in ≥ threshold_ratio of pages.

    These are structural elements (headers, footers, running titles) that should
    be removed as noise — unless they match the preservation whitelist.

    Args:
        pages_texts     : List of raw page texts (one item per page).
        threshold_ratio : Minimum fraction of pages a line must appear in to be flagged.
                          Default 0.30 (appears in ≥ 30 % of pages).

    Returns:
        Set of normalised line strings to remove.
    """
    if len(pages_texts) < 3:
        # Not enough pages for reliable frequency analysis
        return set()

    total_pages = len(pages_texts)
    line_counts: Counter = Counter()

    for text in pages_texts:
        # Count each unique line once per page (set dedup per page)
        unique_lines: set[str] = set()
        for raw_line in text.splitlines():
            norm = raw_line.strip()
            # Skip blank, very long (content), or very short (junk) lines
            if 3 <= len(norm) <= 180:
                unique_lines.add(norm)
        for norm_line in unique_lines:
            line_counts[norm_line] += 1

    threshold = max(2, int(total_pages * threshold_ratio))
    candidates = {line for line, count in line_counts.items() if count >= threshold}

    # Apply preservation whitelist
    repeated = {line for line in candidates if not _should_preserve(line)}

    if repeated:
        logger.info(
            f"LegalCleaner: detected {len(repeated)} repeated header/footer elements "
            f"(threshold: {threshold}/{total_pages} pages)"
        )

    return repeated


def clean_page(
    text: str,
    repeated_elements: Optional[set[str]] = None,
) -> Tuple[str, List[dict], str]:
    """
    Clean a single legal page text.

    Applies in order:
      1. Preserve whitelist check (skip noise rules for protected lines)
      2. Remove isolated page numbers
      3. Remove decoration lines
      4. Remove editorial/JORT notes
      5. Remove repeated header/footer elements (if repeated_elements supplied)
      6. Remove junk lines
      7. Re-normalise whitespace

    Args:
        text              : Raw or previously-cleaned page text.
        repeated_elements : Set produced by detect_repeated_elements() for this document.

    Returns:
        (cleaned_text, rules_applied, rules_summary)
        rules_applied : list of dicts {rule, count, examples}
        rules_summary : human-readable string
    """
    if not text or not text.strip():
        return text, [], "no_content"

    lines = text.splitlines()
    cleaned_lines: List[str] = []

    stats: dict[str, list[str]] = {
        "page_number": [],
        "decoration": [],
        "editorial_note": [],
        "repeated_element": [],
        "junk_line": [],
    }

    for line in lines:
        stripped = line.strip()

        # ── 0. Always preserve whitelisted content ──
        if stripped and _should_preserve(stripped):
            cleaned_lines.append(line)
            continue

        # ── 1. Isolated page number ──
        if _PAGE_NUMBER_RE.match(line):
            stats["page_number"].append(stripped)
            continue

        # ── 2. Decoration line ──
        if stripped and _DECORATION_RE.match(stripped):
            stats["decoration"].append(stripped[:30])
            continue

        # ── 3. Editorial / JORT note ──
        if stripped and (_EDITORIAL_RE.search(stripped) or _EDITORIAL_AR_RE.search(stripped)):
            stats["editorial_note"].append(stripped[:60])
            continue

        # ── 4. Repeated element (header / footer) ──
        if repeated_elements and stripped in repeated_elements:
            stats["repeated_element"].append(stripped[:60])
            continue

        # ── 5. Junk punctuation-only line ──
        if stripped and _JUNK_LINE_RE.match(stripped):
            stats["junk_line"].append(stripped)
            continue

        cleaned_lines.append(line)

    # Re-join and normalise consecutive blank lines
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()

    # Build transformation_rules (same schema as TextCleaningRules)
    rules_applied: List[dict] = []
    for rule_name, examples in stats.items():
        if examples:
            rules_applied.append({
                "rule": f"legal_cleaner_{rule_name}",
                "count": len(examples),
                "examples": examples[:3],
                "description": _RULE_DESCRIPTIONS.get(rule_name, rule_name),
            })

    summary = (
        "; ".join(f"{r['rule']}({r['count']})" for r in rules_applied)
        if rules_applied
        else "legal_cleaner: no_noise_found"
    )

    return cleaned, rules_applied, summary


def clean_document_pages(
    pages: List[Tuple[str, int]],
) -> List[Tuple[str, List[dict], str, int]]:
    """
    Clean an entire document's pages with cross-page frequency analysis.

    Args:
        pages: List of (raw_text, page_number) tuples, in page order.

    Returns:
        List of (cleaned_text, rules_applied, rules_summary, page_number).
    """
    if not pages:
        return []

    raw_texts = [text for text, _ in pages]
    repeated = detect_repeated_elements(raw_texts)

    results = []
    total_noise = 0
    for raw_text, page_num in pages:
        cleaned, rules, summary = clean_page(raw_text, repeated_elements=repeated)
        total_noise += sum(r["count"] for r in rules)
        results.append((cleaned, rules, summary, page_num))

    if total_noise:
        logger.info(f"LegalCleaner: removed {total_noise} noise items across {len(pages)} pages")

    return results


# ── Internal helpers ─────────────────────────────────────────────────────────

_RULE_DESCRIPTIONS: dict[str, str] = {
    "page_number":       "Removed isolated page number",
    "decoration":        "Removed decorative separator line",
    "editorial_note":    "Removed non-normative editorial/JORT note",
    "repeated_element":  "Removed repeated header/footer element",
    "junk_line":         "Removed junk punctuation-only line",
}
