"""
Text utility functions: cleaning, Arabic normalization, language detection, and garble checks.
"""

import re
import unicodedata

_ARABIC_BLOCK_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)
_LATIN_BLOCK_RE = re.compile(r"[A-Za-z\u00C0-\u00FF]")
_ARABIC_DIACRITICS_RE = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)
_SPACED_ARABIC_LETTERS_RE = re.compile(
    r"(?<!\S)(?:[\u0621-\u064A]\s+){2,}[\u0621-\u064A](?!\S)"
)
_ISOLATED_LATIN_NOISE_RE = re.compile(r"\b[A-Za-z]{1,2}\b")
_DISALLOWED_OCR_CHARS_RE = re.compile(
    r"[^"
    r"\u0600-\u06FF"        # Arabic
    r"A-Za-z\u00C0-\u00FF"  # Latin (kept to avoid dropping meaningful acronyms)
    r"0-9\u0660-\u0669"     # Western + Arabic-Indic digits
    r"\s\n\r\t"
    r"\.,:!\?\-_/\\%\"'()\[\]\{\}"
    r"،؛؟«»"
    r"]"
)

_ARABIC_PUNCT_TRANSLATION = str.maketrans({
    ",": "،",
    ";": "؛",
    "?": "؟",
    "٬": "،",
    "٫": ".",
    "“": "\"",
    "”": "\"",
    "„": "\"",
    "‘": "'",
    "’": "'",
    "‐": "-",
    "‑": "-",
    "‒": "-",
    "–": "-",
    "—": "-",
    "−": "-",
})
_ARABIC_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)
_ARABIC_CHAR_TRANSLATION = str.maketrans({
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ى": "ي",
    "ۀ": "ة",
})


def clean_text(text: str) -> str:
    """Unicode-normalize, strip control chars, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fix_arabic(text: str) -> str:
    """
    Apply Arabic reshaping only (letter joining/connecting forms).
    Does not apply BiDi visual reordering, so text remains in logical order.
    """
    try:
        import arabic_reshaper
        return arabic_reshaper.reshape(text)
    except ImportError:
        return text


def clean_arabic_ocr_text(text: str, ta_marbuta_form: str = "ة") -> str:
    """
    Clean OCR-generated Arabic legal text for NLP classification.

    Rules are deterministic and regex-driven to keep output stable across runs.

    Args:
        text: Raw OCR text (Arabic legal content with potential OCR noise).
        ta_marbuta_form: Normalization target for ta marbuta:
            - "ة": keep ta marbuta as ta marbuta (default, lower data loss)
            - "ه": normalize ta marbuta to heh for stricter token unification
    """
    if ta_marbuta_form not in {"ة", "ه"}:
        raise ValueError("ta_marbuta_form must be either 'ة' or 'ه'")
    if not text:
        return ""

    # 1) Canonical Unicode normalization to fold compatibility forms.
    cleaned = unicodedata.normalize("NFKC", text)

    # 2) Remove control and invisible direction marks that pollute OCR output.
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    cleaned = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\ufeff]", "", cleaned)

    # 3) Normalize punctuation and digits to one consistent representation.
    cleaned = cleaned.translate(_ARABIC_PUNCT_TRANSLATION)
    cleaned = cleaned.translate(_ARABIC_DIGIT_TRANSLATION)

    # 4) Normalize key Arabic characters requested for stable NLP matching.
    cleaned = cleaned.translate(_ARABIC_CHAR_TRANSLATION)
    if ta_marbuta_form == "ه":
        cleaned = cleaned.replace("ة", "ه")

    # 5) Remove Arabic diacritics and tatweel to reduce OCR variability.
    cleaned = _ARABIC_DIACRITICS_RE.sub("", cleaned)
    cleaned = cleaned.replace("ـ", "")

    # 6) Repair broken words split as single letters (common OCR issue).
    cleaned = _SPACED_ARABIC_LETTERS_RE.sub(
        lambda m: re.sub(r"\s+", "", m.group(0)),
        cleaned,
    )

    # 7) Remove short isolated Latin noise while preserving longer legal acronyms.
    cleaned = _ISOLATED_LATIN_NOISE_RE.sub(" ", cleaned)

    # 8) Drop non-Arabic corruption symbols while keeping legal punctuation/digits.
    cleaned = _DISALLOWED_OCR_CHARS_RE.sub(" ", cleaned)

    # 9) Normalize boundaries between Arabic letters and digits (e.g., "الفصل12").
    cleaned = re.sub(r"(?<=[\u0621-\u064A])(?=[0-9])", " ", cleaned)
    cleaned = re.sub(r"(?<=[0-9])(?=[\u0621-\u064A])", " ", cleaned)

    # 10) Fix punctuation spacing for clean RTL tokenization.
    cleaned = re.sub(r"\s+([،؛؟\.,:!\)\]\}])", r"\1", cleaned)
    cleaned = re.sub(r"([«\(\[\{])\s+", r"\1", cleaned)
    cleaned = re.sub(r"([،؛؟\.,:!])(?=[^\s\n\)\]\}»])", r"\1 ", cleaned)

    # 11) Final whitespace normalization (stable for downstream classifiers).
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def detect_language(text: str) -> str:
    """
    Fast heuristic language detector based on Unicode block counts.
    Returns: 'ar', 'fr', 'ar+fr', or 'unknown'
    """
    arabic = len(_ARABIC_BLOCK_RE.findall(text))
    latin = len(_LATIN_BLOCK_RE.findall(text))
    total = arabic + latin
    if total == 0:
        return "unknown"
    ratio = arabic / total
    if ratio > 0.65:
        return "ar"
    if ratio < 0.25:
        return "fr"
    return "ar+fr"


def is_text_garbled(
    text: str,
    expect_arabic: bool = False,
    raw_text: str | None = None,
) -> bool:
    """
    Detect garbled/broken text extraction, especially from problematic Arabic PDFs.

    Args:
        text: Cleaned text (after clean_text()).
        expect_arabic: True if the document is expected to contain Arabic.
        raw_text: Original text before clean_text(), to inspect stripped controls.
    """
    stripped = text.strip()
    if len(stripped) < 30:
        return False

    # Check raw text for control-character-heavy extraction.
    if raw_text is not None:
        raw_len = len(raw_text)
        if raw_len > 0:
            control_raw = len(re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", raw_text))
            if control_raw / raw_len > 0.03:
                return True

    arabic_chars = len(_ARABIC_BLOCK_RE.findall(text))
    latin_chars = len(_LATIN_BLOCK_RE.findall(text))
    control = len(re.findall(r"[\r\x00-\x08\x0b\x0c\x0e-\x1f]", text))
    total_len = len(text)

    if total_len > 0 and control / total_len > 0.05:
        return True

    if expect_arabic:
        alpha_total = arabic_chars + latin_chars
        if alpha_total > 20 and arabic_chars / alpha_total < 0.15:
            return True

    words = text.split()
    if len(words) > 10:
        single_char_words = sum(1 for w in words if len(w) == 1 and not w.isdigit())
        if single_char_words / len(words) > 0.35:
            return True

    return False
