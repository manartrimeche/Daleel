"""
Smart chunking — section-aware splitting for legal / administrative docs.
"""

import re
import hashlib
import logging
from typing import Dict, List, Tuple

from app.config import get_settings
from app.processing.text_utils import clean_text, clean_arabic_ocr_text, detect_language

logger = logging.getLogger(__name__)

_AR_SECTION_RE = re.compile(
    r"^(?:على\s+أساس|الفصل|المادة|البند)\b.*$",
    re.MULTILINE | re.UNICODE,
)
_FR_SECTION_RE = re.compile(
    r"^(?:Article|Alinéa|Alinea|Chapitre|Section|Titre)\b.*$",
    re.MULTILINE | re.IGNORECASE | re.UNICODE,
)
_EN_SECTION_RE = re.compile(
    r"^(?:Article|Section|Chapter|Clause|Paragraph)\b.*$",
    re.MULTILINE | re.IGNORECASE | re.UNICODE,
)
_ANY_SECTION_RE = re.compile(
    r"^(?:على\s+أساس|الفصل|المادة|البند|Article|Alinéa|Alinea|Chapitre|Section|Titre|Chapter|Clause|Paragraph)\b.*$",
    re.MULTILINE | re.IGNORECASE | re.UNICODE,
)


def _is_low_quality(text: str, lang: str) -> bool:
    """Reject pages that are mostly noise (OCR garbage, too short, repetitive)."""
    stripped = text.strip()
    if len(stripped) < 30:
        return True
    words = stripped.split()
    if len(words) < 5:
        return True
    unique_words = set(w.lower() for w in words if len(w) > 2)
    if len(words) > 10 and len(unique_words) / len(words) < 0.15:
        return True
    alnum = sum(1 for c in stripped if c.isalnum())
    if len(stripped) > 0 and alnum / len(stripped) < 0.25:
        return True
    return False


class ChunkingService:
    def __init__(
        self,
        max_size: int | None = None,
        overlap: int | None = None,
        min_chunk_size: int | None = None,
    ) -> None:
        settings = get_settings()
        self.max_size = max_size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap
        self.min_chunk_size = min_chunk_size or 300

    def chunk_text(self, text: str, language: str) -> list[dict]:
        cleaned = clean_text(text).strip()
        if not cleaned:
            return []

        requested_lang = (language or "").strip().lower()
        if requested_lang in {"ar", "fr", "en"}:
            split_lang = requested_lang
            meta_lang = requested_lang
        else:
            split_lang = "mixed"
            meta_lang = detect_language(cleaned)

        sections, found = self._split_sections(cleaned, split_lang)
        if not found:
            return self._fallback_sliding(cleaned, meta_lang)

        chunks: list[dict] = []
        for heading, body in sections:
            if not body:
                continue
            section_chunks = self._chunk_section(body, heading, meta_lang)
            chunks.extend(section_chunks)

        chunks = self._merge_short_chunks(chunks)
        for idx, item in enumerate(chunks):
            item["metadata"]["chunk_index"] = idx
        return chunks

    def _split_sections(self, text: str, language: str) -> tuple[list[tuple[str, str]], bool]:
        section_re = self._select_section_regex(language)
        matches = list(section_re.finditer(text))
        if not matches:
            return [("", text)], False

        sections: list[tuple[str, str]] = []
        if matches[0].start() > 0:
            preamble = text[: matches[0].start()].strip()
            if preamble:
                sections.append(("", preamble))

        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            heading = match.group().strip()
            body = text[match.start(): end].strip()
            sections.append((heading, body))

        return sections, True

    def _select_section_regex(self, language: str) -> re.Pattern:
        if language.startswith("ar"):
            return _AR_SECTION_RE
        if language.startswith("fr"):
            return _FR_SECTION_RE
        if language.startswith("en"):
            return _EN_SECTION_RE
        return _ANY_SECTION_RE

    def _chunk_section(self, body: str, heading: str, language: str) -> list[dict]:
        source_article, source_section = self._classify_heading(heading)
        forced = len(body) > self.max_size

        if not forced:
            return [
                {
                    "text": body,
                    "metadata": {
                        "source_article": source_article,
                        "source_section": source_section,
                        "language": language,
                        "is_forced_split": False,
                    },
                }
            ]

        chunks = self._split_long_text(body)
        return [
            {
                "text": chunk,
                "metadata": {
                    "source_article": source_article,
                    "source_section": source_section,
                    "language": language,
                    "is_forced_split": True,
                },
            }
            for chunk in chunks
        ]

    def _split_long_text(self, text: str) -> list[str]:
        step = max(self.max_size - self.overlap, 1)
        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.max_size, text_len)
            chunk = text[start:end]
            chunks.append(chunk)
            if end >= text_len:
                break
            start = end - self.overlap

        return chunks

    def _fallback_sliding(self, text: str, language: str) -> list[dict]:
        raw_chunks = sliding_chunks(
            text,
            size=self.max_size,
            overlap=self.overlap,
            min_len=1,
        )
        forced = len(raw_chunks) > 1
        chunks = [
            {
                "text": chunk,
                "metadata": {
                    "source_article": None,
                    "source_section": None,
                    "language": language,
                    "is_forced_split": forced,
                },
            }
            for chunk in raw_chunks
        ]
        chunks = self._merge_short_chunks(chunks)
        for idx, item in enumerate(chunks):
            item["metadata"]["chunk_index"] = idx
        return chunks

    def _merge_short_chunks(self, chunks: list[dict]) -> list[dict]:
        if not chunks:
            return []

        merged: list[dict] = []
        pending: dict | None = None

        for item in chunks:
            if pending is not None:
                merged.append(self._merge_chunk_pair(pending, item))
                pending = None
                continue

            if len(item["text"]) < self.min_chunk_size:
                pending = item
                continue

            merged.append(item)

        if pending is not None:
            if merged:
                merged[-1] = self._merge_chunk_pair(merged[-1], pending)
            else:
                merged.append(pending)

        return merged

    def _merge_chunk_pair(self, base: dict, extra: dict) -> dict:
        text = base["text"].rstrip() + "\n" + extra["text"].lstrip()
        meta = dict(base["metadata"])
        meta["is_forced_split"] = (
            meta.get("is_forced_split", False)
            or extra["metadata"].get("is_forced_split", False)
        )
        if not meta.get("source_article"):
            meta["source_article"] = extra["metadata"].get("source_article")
        if not meta.get("source_section"):
            meta["source_section"] = extra["metadata"].get("source_section")
        if not meta.get("language"):
            meta["language"] = extra["metadata"].get("language")
        return {"text": text, "metadata": meta}

    def _classify_heading(self, heading: str) -> tuple[str | None, str | None]:
        if not heading:
            return None, None

        heading_lower = heading.lower()
        if heading_lower.startswith("article") or heading_lower.startswith("المادة"):
            return heading, None

        return None, heading


def split_sections(text: str) -> List[Tuple[str, str]]:
    """Split text at section headings → list of (heading, body)."""
    matches = list(_ANY_SECTION_RE.finditer(text))
    if not matches:
        return [("", text)]

    sections = []
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("preamble", preamble))

    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = m.group().strip()
        body = text[m.start(): end].strip()
        sections.append((title, body))

    return sections


def sliding_chunks(
    text: str,
    size: int | None = None,
    overlap: int | None = None,
    min_len: int | None = None,
) -> List[str]:
    """Split text into overlapping chunks at sentence boundaries."""
    settings = get_settings()
    size = size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap
    min_len = min_len or settings.min_chunk_len

    sentences = re.split(r"(?<=[.!?؟])\s+|\n\n+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks: List[str] = []
    current: List[str] = []
    cur_len: int = 0

    for sent in sentences:
        s_len = len(sent)
        if cur_len + s_len > size and current:
            chunks.append(" ".join(current))
            # Sentence-level overlap: keep trailing sentences that fit in overlap
            overlap_sents: List[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) > overlap:
                    break
                overlap_sents.insert(0, s)
                overlap_len += len(s)
            current = overlap_sents
            cur_len = overlap_len
        current.append(sent)
        cur_len += s_len

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if len(c) >= min_len]


def make_chunk_id(source: str, page: int, idx: int) -> str:
    raw = f"{source}|page{page}|chunk{idx}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def build_records(
    pages: List[Dict],
    source_name: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Dict]:
    """
    Convert extracted pages → list of chunk records with metadata.
    """
    records: List[Dict] = []
    chunk_idx = 0
    chunker = ChunkingService(
        max_size=chunk_size,
        overlap=chunk_overlap,
        min_chunk_size=300,
    )

    for page_data in pages:
        raw = clean_text(page_data["text"])
        page_num = page_data["page"]
        ocr_used = page_data["ocr_used"]

        if not raw:
            continue

        lang = detect_language(raw)

        if lang in ("ar", "ar+fr") and ocr_used:
            raw = clean_arabic_ocr_text(raw)

        if _is_low_quality(raw, lang):
            logger.debug("Skipping low-quality page %d of %s", page_num, source_name)
            continue

        chunks = chunker.chunk_text(raw, lang)
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            heading = meta.get("source_article") or meta.get("source_section")
            records.append({
                "id": make_chunk_id(source_name, page_num, chunk_idx),
                "text": chunk["text"],
                "metadata": {
                    "source": source_name,
                    "page": page_num,
                    "section": heading if heading not in ("", "preamble") else None,
                    "source_article": meta.get("source_article"),
                    "source_section": meta.get("source_section"),
                    "language": meta.get("language", lang),
                    "ocr_used": ocr_used,
                    "chunk_index": chunk_idx,
                    "is_forced_split": meta.get("is_forced_split", False),
                },
            })
            chunk_idx += 1

    return records
