"""
Text utility functions: cleaning, Arabic normalization, language detection, and garble checks.
"""

import re
import unicodedata

_ARABIC_BLOCK_RE = re.compile(
    r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]"
)
_LATIN_BLOCK_RE = re.compile(r"[A-Za-zÀ-ÿ]")
_ARABIC_DIACRITICS_RE = re.compile(
    r"[ؐ-ًؚ-ٰٟۖ-ۭ]"
)
_SPACED_ARABIC_LETTERS_RE = re.compile(
    r"(?<!\S)(?:[ء-ي]\s+){2,}[ء-ي](?!\S)"
)
_ISOLATED_LATIN_NOISE_RE = re.compile(r"\b[A-Za-z]{1,2}\b")
_DISALLOWED_OCR_CHARS_RE = re.compile(
    r"[^"
    r"؀-ۿ"        # Arabic
    r"A-Za-zÀ-ÿ"  # Latin (kept to avoid dropping meaningful acronyms)
    r"0-9٠-٩"     # Western + Arabic-Indic digits
    r"\s\n\r\t"
    r"\.,:!\?\-_/\\%\"'()\[\]\{\}"
    r"،؛؟«»"
    r"]"
)

_STRAY_ZERO_IN_ARABIC_RE = re.compile(
    r"(?<=[؀-ۿ.,؛])\s+0\s+(?=[؀-ۿ])"
)
_STRAY_DIGIT_EOL_RE = re.compile(
    r"(?<=[؀-ۿ])[.\s]+\d{1,2}\s*$", re.MULTILINE
)
_STRAY_DIGIT_BOL_RE = re.compile(
    r"^\s*\d{1,2}\s+(?=[؀-ۿ])", re.MULTILINE
)
_ISOLATED_AR_LETTER_RE = re.compile(
    r"(?<=[؀-ۿ])\s+([؀-ۿ])\s+(?=[؀-ۿ]{2,})"
)
_LEADING_ISOLATED_LETTER_RE = re.compile(
    r"^\s*[؀-ۿ]\s+(?=[؀-ۿ]{2,})", re.MULTILINE
)
_TRAILING_ISOLATED_LETTER_RE = re.compile(
    r"(?<=[؀-ۿ]{2})\s+[؀-ۿ]\s*$", re.MULTILINE
)
_TRIPLE_ARABIC_CHAR_RE = re.compile(
    r"([؀-ۿ])\1{2,}"
)
_STRAY_SYMBOL_IN_ARABIC_RE = re.compile(
    r"(?<=[؀-ۿ])\s*[#@&\*\^~`|\\<>{}\"]+\s*(?=[؀-ۿ])"
)
_DOUBLE_DASH_RE = re.compile(r"\s*--+\s*")
_ORPHAN_PAREN_RE = re.compile(
    r"(?<=[؀-ۿ])\s*[\(\)]\s*(?=[؀-ۿ])"
)

_LEGAL_AR_OCR_CORRECTIONS = {
    "التاسيسي": "التأسيسي",
    "التاسيسئ": "التأسيسي",
    "الاساسية": "الأساسية",
    "الاولي": "الأولى",
    "الاخري": "الأخرى",
    "الاعضاءء": "الأعضاء",
    "الاملية": "الأهلية",
    "الاحكام": "الأحكام",
    "الاسهم": "الأسهم",
    "الاجال": "الآجال",
    "المختصف": "المختصة",
    "يتقزر": "يتقرر",
    "باالقاكون": "بالقانون",
    "باالقانون": "بالقانون",
    "المؤسسسة": "المؤسسة",
    "المؤسسسات": "المؤسسات",
    "الشرككة": "الشركة",
    "القانوة": "القانون",
    "الاقتصااد": "الاقتصاد",
    "واحااك": "واحدة",
    "بطاةاللايف": "بطاقة التعريف",
    "الاكهد": "الاقتضاء",
    "التهلم": "المسلمة",
    "قاد": "بطاقات",
    "فلللمبوع": "للأسبوع",
    "فيلللم": "في",
}

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
    "٠١٢٣٤٥٦٧٨٩"
    "۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)
_ARABIC_CHAR_TRANSLATION = str.maketrans({
    "أ": "ا",  # alef with hamza above -> alef
    "إ": "ا",  # alef with hamza below -> alef
    "آ": "ا",  # alef with madda -> alef
    "ٱ": "ا",  # alef wasla -> alef
    "ى": "ي",  # alef maqsura -> ya
    "ۀ": "ة",  # heh with yeh above -> ta marbuta
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
    """
    if ta_marbuta_form not in {"ة", "ه"}:
        raise ValueError("ta_marbuta_form must be either ta marbuta or heh")
    if not text:
        return ""

    # 1) Canonical Unicode normalization to fold compatibility forms.
    cleaned = unicodedata.normalize("NFKC", text)

    # 2) Remove control and invisible direction marks that pollute OCR output.
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    invisible_marks = "\u200b\u200c\u200d\u200e\u200f\ufeff"
    cleaned = re.sub(f"[{invisible_marks}]", "", cleaned)

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

    # 7) Remove stray digits/symbols injected by OCR.
    cleaned = _STRAY_ZERO_IN_ARABIC_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+0\s+(?=[؀-ۿ])", " ", cleaned)
    cleaned = re.sub(r"(?<=[؀-ۿ.,؛؟])\s+0\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = _STRAY_DIGIT_EOL_RE.sub(".", cleaned)
    cleaned = re.sub(r"\s+\d{1,2}\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = _STRAY_DIGIT_BOL_RE.sub("", cleaned)
    cleaned = _STRAY_SYMBOL_IN_ARABIC_RE.sub(" ", cleaned)
    cleaned = _DOUBLE_DASH_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\.(\s*\.)+", ".", cleaned)
    cleaned = re.sub(r"(?<=[؀-ۿ،؛؟])\s*[\(\)]\s*(?=[؀-ۿ،؛؟])", " ", cleaned)
    cleaned = _ORPHAN_PAREN_RE.sub(" ", cleaned)

    # 7b) Remove isolated single Arabic letters (OCR word fragments).
    for _ in range(3):
        cleaned = _ISOLATED_AR_LETTER_RE.sub(" ", cleaned)
        cleaned = re.sub(r"(?<=[؀-ۿ،؛؟]{2})\s+([؀-ۿ])\s+(?=[؀-ۿ]{2})", " ", cleaned)
    cleaned = _LEADING_ISOLATED_LETTER_RE.sub("", cleaned)
    cleaned = _TRAILING_ISOLATED_LETTER_RE.sub("", cleaned)

    # 7c) Fix triple+ consecutive Arabic characters (OCR stutter).
    cleaned = _TRIPLE_ARABIC_CHAR_RE.sub(r"\1\1", cleaned)

    # 8) Remove short isolated Latin noise while preserving longer legal acronyms.
    cleaned = _ISOLATED_LATIN_NOISE_RE.sub(" ", cleaned)

    # 9) Drop non-Arabic corruption symbols while keeping legal punctuation/digits.
    cleaned = _DISALLOWED_OCR_CHARS_RE.sub(" ", cleaned)

    # 10) Apply known OCR corrections for legal Arabic terms.
    for wrong, correct in _LEGAL_AR_OCR_CORRECTIONS.items():
        cleaned = cleaned.replace(wrong, correct)

    # 11) Normalize boundaries between Arabic letters and digits.
    cleaned = re.sub(r"(?<=[ء-ي])(?=[0-9])", " ", cleaned)
    cleaned = re.sub(r"(?<=[0-9])(?=[ء-ي])", " ", cleaned)

    # 12) Fix punctuation spacing for clean RTL tokenization.
    cleaned = re.sub(r"\s+([،؛؟\.,:!\)\]\}])", r"\1", cleaned)
    cleaned = re.sub(r"([«\(\[\{])\s+", r"\1", cleaned)
    cleaned = re.sub(r"([،؛؟\.,:!])(?=[^\s\n\)\]\}»])", r"\1 ", cleaned)

    # 13) Final whitespace normalization.
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


_FRENCH_ACCENT_RE = re.compile(r"[àâäéèêëïîôùûüÿçœæ]", re.IGNORECASE)
_FRENCH_MARKERS = [
    "quelles", "quelle", "quel", "quels", "comment", "pourquoi",
    "est-ce", "dans", "pour", "les", "des", "une", "que", "qui",
    "sont", "cette", "avec", "sur", "selon", "droit", "loi",
    "article", "societe", "juridique", "contrat",
    "tribunal", "code", "conditions", "obligations",
]


def detect_query_language(text: str) -> str:
    """
    Detect the dominant language of a user query or short text.

    More nuanced than detect_language() -- uses French word markers and accent
    detection for better accuracy on short legal queries.

    Returns: 'ar', 'fr', or 'en'
    """
    if not text:
        return "en"
    arabic_chars = len(_ARABIC_BLOCK_RE.findall(text))
    if arabic_chars >= 2:
        return "ar"
    if _FRENCH_ACCENT_RE.search(text):
        return "fr"
    lower = text.lower()
    french_count = sum(1 for w in _FRENCH_MARKERS if w in lower)
    if french_count >= 2:
        return "fr"
    return "en"


def is_text_garbled(
    text: str,
    expect_arabic: bool = False,
    raw_text: str | None = None,
) -> bool:
    """
    Detect garbled/broken text extraction, especially from problematic Arabic PDFs.
    """
    stripped = text.strip()
    if len(stripped) < 30:
        return False

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
