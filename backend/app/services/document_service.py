"""
Document service — upload, process, store, list, delete with MongoDB.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import sys
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from weakref import WeakValueDictionary

from pymongo.errors import DuplicateKeyError
from tqdm import tqdm

from app.config import get_settings
from app.database import get_collection
from app.processing.article_segmenter import build_page_map, segment_text_into_articles
from app.processing.chunker import build_records
from app.processing.extractor import EXTRACTORS
from app.services import audit_service, llm_service
from app.services.embedding_service import embed_texts_async
from app.services.faiss_index import faiss_manager
from app.services.search_service import invalidate_embedding_dimension_cache

logger = logging.getLogger(__name__)
settings = get_settings()

_EXIGENCE_TYPES = {"obligation", "prohibition", "condition", "sanction"}
_ARTICLE_REF_RE = re.compile(r"(?:Article|article|الفصل|فصل)\s*([0-9]+)", re.IGNORECASE)
SUPPORTED_EXTENSIONS = set(EXTRACTORS.keys())
_UPLOAD_LOCKS: WeakValueDictionary[str, asyncio.Lock] = WeakValueDictionary()
_UPLOAD_LOCKS_GUARD = asyncio.Lock()



async def _get_upload_lock(file_hash: str) -> asyncio.Lock:
    async with _UPLOAD_LOCKS_GUARD:
        lock = _UPLOAD_LOCKS.get(file_hash)
        if lock is None:
            lock = asyncio.Lock()
            _UPLOAD_LOCKS[file_hash] = lock
        return lock


def _doc_to_out(doc: dict | None) -> dict | None:
    if not doc:
        return None
    return {
        "id": doc.get("id"),
        "filename": doc.get("filename"),
        "file_type": doc.get("file_type"),
        "file_size": doc.get("file_size"),
        "language": doc.get("language"),
        "total_pages": doc.get("total_pages"),
        "total_chunks": doc.get("total_chunks"),
        "ocr_used": doc.get("ocr_used"),
        "status": doc.get("status"),
        "error_message": doc.get("error_message"),
        "document_type": doc.get("document_type"),
        "loi_id": doc.get("loi_id"),
        "organization_id": doc.get("organization_id"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _chunk_to_out(chunk: dict) -> dict:
    return {
        "id": chunk.get("id"),
        "document_id": chunk.get("document_id"),
        "chunk_index": chunk.get("chunk_index"),
        "text": chunk.get("text"),
        "page_number": chunk.get("page_number"),
        "section": chunk.get("section"),
        "language": chunk.get("language"),
        "ocr_used": chunk.get("ocr_used"),
        "char_count": chunk.get("char_count"),
    }


def _raw_page_to_out(raw_page: dict) -> dict:
    return {
        "id": raw_page.get("id"),
        "document_id": raw_page.get("document_id"),
        "page_number": raw_page.get("page_number"),
        "raw_text": raw_page.get("raw_text"),
        "ocr_used": raw_page.get("ocr_used"),
        "extracted_at": raw_page.get("extracted_at"),
    }


def _source_to_out(source: dict) -> dict:
    return {
        "id": source.get("id"),
        "document_id": source.get("document_id"),
        "source_path": source.get("source_path"),
        "file_hash": source.get("file_hash"),
        "language": source.get("language"),
        "uploaded_at": source.get("uploaded_at"),
    }


def _cleaned_text_to_out(cleaned: dict) -> dict:
    return {
        "id": cleaned.get("id"),
        "document_id": cleaned.get("document_id"),
        "page_number": cleaned.get("page_number"),
        "raw_page_id": cleaned.get("raw_page_id"),
        "version": cleaned.get("version"),
        "cleaned_text": cleaned.get("cleaned_text"),
        "transformation_rules": cleaned.get("transformation_rules", []),
        "rules_summary": cleaned.get("rules_summary"),
        "cleaned_at": cleaned.get("cleaned_at"),
    }


def _exigence_to_out(exigence: dict) -> dict:
    return {
        "id": exigence.get("id"),
        "document_id": exigence.get("document_id"),
        "cleaned_text_id": exigence.get("cleaned_text_id"),
        "page_number": exigence.get("page_number"),
        "article_reference": exigence.get("article_reference"),
        "exigence_type": exigence.get("exigence_type"),
        "text": exigence.get("text"),
        "confidence_score": exigence.get("confidence_score"),
        "source_citation": exigence.get("source_citation"),
        "extracted_at": exigence.get("extracted_at"),
    }


def _normalize_for_match(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[^\w\u0600-\u06FF]+", "", text, flags=re.UNICODE)
    return text


def _extract_article_refs(text: str) -> set[str]:
    return {match.group(1) for match in _ARTICLE_REF_RE.finditer(text)}


def _token_overlap_score(candidate: str, source: str) -> float:
    candidate_tokens = {
        token for token in re.split(r"\W+", candidate.lower()) if len(token) >= 3
    }
    source_tokens = {
        token for token in re.split(r"\W+", source.lower()) if len(token) >= 3
    }
    if not candidate_tokens:
        return 0.0
    shared = candidate_tokens.intersection(source_tokens)
    return len(shared) / len(candidate_tokens)


def _is_grounded_exigence(exigence: dict, cleaned_text: str) -> bool:
    exigence_type = str(exigence.get("type", "")).strip().lower()
    if exigence_type not in _EXIGENCE_TYPES:
        return False

    text = str(exigence.get("text", "")).strip()
    if len(text) < 10:
        return False

    article = str(exigence.get("article", "")).strip()
    source_article_refs = _extract_article_refs(cleaned_text)
    extracted_article_refs = _extract_article_refs(article)
    if extracted_article_refs and not extracted_article_refs.intersection(source_article_refs):
        return False

    normalized_source = _normalize_for_match(cleaned_text)
    normalized_text = _normalize_for_match(text)
    if not normalized_text:
        return False

    if normalized_text in normalized_source or normalized_source in normalized_text:
        return True

    if _token_overlap_score(text, cleaned_text) >= 0.5:
        return True

    return False


class TextCleaningRules:
    """Non-destructive text cleaning with transformation tracking."""

    @staticmethod
    def apply_cleaning(raw_text: str) -> tuple[str, list[dict], str]:
        cleaned = raw_text
        rules_applied: list[dict] = []

        before = cleaned
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n\n+", "\n", cleaned)
        if before != cleaned:
            rules_applied.append(
                {
                    "rule": "normalize_whitespace",
                    "pattern": "[ \\t]+ | \\n\\n+",
                    "description": "Collapsed multiple spaces/tabs and newlines",
                }
            )

        before = cleaned
        cleaned = "".join(c for c in cleaned if ord(c) >= 32 or c in "\t\n\r")
        if before != cleaned:
            rules_applied.append(
                {
                    "rule": "remove_control_chars",
                    "pattern": "chr(0-31) except \\t\\n\\r",
                    "description": "Removed control characters",
                }
            )

        before = cleaned
        invisible_chars = ["\u200b", "\u200c", "\u200d", "\u200e", "\u200f", "\ufeff"]
        for char in invisible_chars:
            cleaned = cleaned.replace(char, "")
        if before != cleaned:
            rules_applied.append(
                {
                    "rule": "remove_invisible_chars",
                    "pattern": "zero-width | BOM | directional marks",
                    "description": "Removed invisible Unicode characters",
                }
            )

        before = cleaned
        cleaned = unicodedata.normalize("NFC", cleaned)
        if before != cleaned:
            rules_applied.append(
                {
                    "rule": "normalize_unicode_nfc",
                    "pattern": "NFC normalization",
                    "description": "Applied NFC Unicode normalization",
                }
            )

        before = cleaned
        lines = cleaned.split("\n")
        lines = [line.rstrip() for line in lines]
        cleaned = "\n".join(lines).strip()
        if before != cleaned:
            rules_applied.append(
                {
                    "rule": "trim_whitespace",
                    "pattern": "^\\s+ | \\s+$",
                    "description": "Trimmed leading/trailing whitespace",
                }
            )

        summary = "; ".join(r["rule"] for r in rules_applied) if rules_applied else "no_cleaning_applied"
        return cleaned, rules_applied, summary


async def clean_and_store_pages(
    db,
    doc_id: str,
    raw_pages: list[dict],
) -> int:
    if not raw_pages:
        return 0

    from app.processing.legal_cleaner import clean_page as legal_clean_page, detect_repeated_elements

    all_raw_texts = [p.get("raw_text", "") for p in raw_pages]
    repeated_elements = detect_repeated_elements(all_raw_texts)
    now = datetime.now(timezone.utc)
    cleaned_text_docs: list[dict] = []

    for raw_page in raw_pages:
        basic_text, basic_rules, _ = TextCleaningRules.apply_cleaning(raw_page.get("raw_text", ""))
        legal_text, legal_rules, _ = legal_clean_page(basic_text, repeated_elements=repeated_elements)
        all_rules = basic_rules + legal_rules
        summary = "; ".join(r["rule"] for r in all_rules) if all_rules else "no_cleaning_applied"

        cleaned_text_docs.append(
            {
                "id": str(uuid.uuid4()),
                "document_id": doc_id,
                "page_number": raw_page.get("page_number"),
                "raw_page_id": raw_page.get("id"),
                "version": 1,
                "cleaned_text": legal_text,
                "transformation_rules": all_rules,
                "rules_summary": summary,
                "cleaned_at": now,
            }
        )

    if cleaned_text_docs:
        await get_collection("document_cleaned_texts").insert_many(cleaned_text_docs)

    return len(cleaned_text_docs)


async def _update_document(doc_id: str, updates: dict) -> None:
    updates["updated_at"] = datetime.now(timezone.utc)
    await get_collection("documents").update_one({"id": doc_id}, {"$set": updates})


async def create_pending_upload(
    db,
    filename: str,
    file_bytes: bytes,
    *,
    approval_type: str,
    requested_by: Optional[str] = None,
    organization_id: Optional[str] = None,
    loi_id: Optional[str] = None,
) -> dict:
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    doc_id = str(uuid.uuid4())
    ext = Path(filename).suffix.lower()
    saved_path = upload_dir / f"{doc_id}{ext}"
    saved_path.write_bytes(file_bytes)
    now = datetime.now(timezone.utc)
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    doc_doc = {
        "id": doc_id,
        "filename": filename,
        "file_type": ext.lstrip("."),
        "file_size": len(file_bytes),
        "status": "pending_approval",
        "approval_type": approval_type,
        "requested_by": requested_by,
        "organization_id": organization_id,
        "loi_id": loi_id,
        "created_at": now,
        "updated_at": now,
        "language": None,
        "total_pages": 0,
        "total_chunks": 0,
        "ocr_used": False,
        "error_message": None,
    }
    await get_collection("documents").insert_one(doc_doc)
    await get_collection("document_sources").insert_one({
        "id": str(uuid.uuid4()),
        "document_id": doc_id,
        "source_path": str(saved_path),
        "file_hash": f"pending:{doc_id}:{file_hash}",
        "original_file_hash": file_hash,
        "language": None,
        "uploaded_at": now,
    })
    return _doc_to_out(doc_doc)


async def reject_pending_upload(db, doc_id: str, reason: str = "Refusé par le super admin") -> dict | None:
    doc = await get_collection("documents").find_one({"id": doc_id})
    if not doc or doc.get("status") != "pending_approval":
        return None
    await _update_document(doc_id, {"status": "rejected", "error_message": reason})
    return _doc_to_out(await get_collection("documents").find_one({"id": doc_id}))


async def approve_pending_document(
    db,
    doc_id: str,
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> dict:
    doc = await get_collection("documents").find_one({"id": doc_id})
    if not doc or doc.get("status") != "pending_approval":
        raise ValueError("Demande de document introuvable ou déjà traitée")
    if doc.get("approval_type") != "document_upload":
        raise ValueError("Cette demande n'est pas un upload de document standard")

    source = await get_collection("document_sources").find_one({"document_id": doc_id})
    if not source or not source.get("source_path"):
        raise ValueError("Fichier source introuvable pour cette demande")

    source_path = Path(source["source_path"])
    if not source_path.exists():
        raise ValueError("Fichier source introuvable sur le disque")

    file_bytes = source_path.read_bytes()
    filename = doc["filename"]
    await delete_document(db, doc_id)
    return await upload_document(
        db,
        filename,
        file_bytes,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        organization_id=doc.get("organization_id"),
    )


async def approve_pending_amendment(
    db,
    doc_id: str,
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> dict:
    doc = await get_collection("documents").find_one({"id": doc_id})
    if not doc or doc.get("status") != "pending_approval":
        raise ValueError("Demande d'amendement introuvable ou déjà traitée")
    if doc.get("approval_type") != "amendment_upload":
        raise ValueError("Cette demande n'est pas un upload d'amendement")

    source = await get_collection("document_sources").find_one({"document_id": doc_id})
    if not source or not source.get("source_path"):
        raise ValueError("Fichier source introuvable pour cette demande")

    source_path = Path(source["source_path"])
    if not source_path.exists():
        raise ValueError("Fichier source introuvable sur le disque")

    file_bytes = source_path.read_bytes()
    filename = doc["filename"]
    loi_id = doc.get("loi_id")
    await delete_document(db, doc_id)
    return await upload_amendment_document(
        db,
        filename,
        file_bytes,
        loi_id=loi_id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


async def upload_document(
    db,
    filename: str,
    file_bytes: bytes,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    organization_id: str | None = None,
) -> dict:
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    upload_lock = await _get_upload_lock(file_hash)

    async with upload_lock:
        existing_source = await get_collection("document_sources").find_one({"file_hash": file_hash})
        if existing_source:
            existing_doc = await get_collection("documents").find_one({"id": existing_source.get("document_id")})
            same_org = (
                not organization_id
                or existing_doc.get("organization_id") == organization_id
            ) if existing_doc else False
            if existing_doc and existing_doc.get("status") == "ready" and same_org:
                return _doc_to_out(existing_doc)

        doc_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower()
        saved_path = upload_dir / f"{doc_id}{ext}"
        saved_path.write_bytes(file_bytes)
        now = datetime.now(timezone.utc)

        doc_doc = {
            "id": doc_id,
            "filename": filename,
            "file_type": ext.lstrip("."),
            "file_size": len(file_bytes),
            "status": "processing",
            "created_at": now,
            "updated_at": now,
            "language": None,
            "total_pages": 0,
            "total_chunks": 0,
            "ocr_used": False,
            "error_message": None,
            "organization_id": organization_id,
        }
        await get_collection("documents").insert_one(doc_doc)

        source_doc = {
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "source_path": str(saved_path),
            "file_hash": file_hash,
            "language": None,
            "uploaded_at": now,
        }

        try:
            await get_collection("document_sources").insert_one(source_doc)
        except DuplicateKeyError:
            await get_collection("documents").delete_one({"id": doc_id})
            saved_path.unlink(missing_ok=True)
            existing_source = await get_collection("document_sources").find_one({"file_hash": file_hash})
            if existing_source:
                existing_doc = await get_collection("documents").find_one({"id": existing_source.get("document_id")})
                if existing_doc:
                    return _doc_to_out(existing_doc)
            raise

        try:
            extractor = EXTRACTORS.get(ext)
            if extractor is None:
                await _update_document(doc_id, {"status": "error", "error_message": f"Unsupported file type: {ext}"})
                doc = await get_collection("documents").find_one({"id": doc_id})
                return _doc_to_out(doc)

            logger.info("Processing: %s", filename)
            with tqdm(total=4, desc=f"  {filename}", unit="step", leave=True, file=sys.stderr) as pbar:
                pbar.set_postfix_str("extracting")
                pages = extractor(saved_path, original_filename=filename)
                pbar.update(1)

                if not pages:
                    await _update_document(doc_id, {"status": "error", "error_message": "No text extracted"})
                    doc = await get_collection("documents").find_one({"id": doc_id})
                    return _doc_to_out(doc)

                extracted_at = datetime.now(timezone.utc)
                raw_pages: list[dict] = []
                for page_data in pages:
                    page_text = (page_data.get("text") or "").strip()
                    if not page_text:
                        continue
                    raw_pages.append(
                        {
                            "id": str(uuid.uuid4()),
                            "document_id": doc_id,
                            "page_number": int(page_data.get("page", 1)),
                            "raw_text": page_text,
                            "ocr_used": bool(page_data.get("ocr_used", False)),
                            "extracted_at": extracted_at,
                        }
                    )

                if raw_pages:
                    await get_collection("document_raw_pages").insert_many(raw_pages)
                    await clean_and_store_pages(db, doc_id, raw_pages)

                cleaned_pages_for_exigence = await get_collection("document_cleaned_texts").find({"document_id": doc_id}).to_list(length=2000)
                detected_language = llm_service._get_detect_query_language(
                    cleaned_pages_for_exigence[0].get("cleaned_text", "") if cleaned_pages_for_exigence else ""
                )
                if cleaned_pages_for_exigence:
                    await extract_and_store_exigences(db, doc_id, cleaned_pages_for_exigence, detected_language)

                pbar.set_postfix_str("chunking")
                records = build_records(
                    pages,
                    filename,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                pbar.update(1)

                if not records:
                    await _update_document(doc_id, {"status": "error", "error_message": "No chunks produced"})
                    doc = await get_collection("documents").find_one({"id": doc_id})
                    return _doc_to_out(doc)

                pbar.set_postfix_str(f"embedding {len(records)} chunks")
                texts = [r["text"] for r in records]
                embeddings = await embed_texts_async(texts)
                pbar.update(1)

                pbar.set_postfix_str("storing in DB")
                any_ocr = False
                languages_seen: set[str] = set()
                max_page = 0
                chunk_docs: list[dict] = []

                for rec, emb in zip(records, embeddings):
                    meta = rec["metadata"]
                    chunk_docs.append(
                        {
                            "id": str(uuid.uuid4()),
                            "document_id": doc_id,
                            "chunk_index": meta["chunk_index"],
                            "text": rec["text"],
                            "embedding": emb,
                            "page_number": meta["page"],
                            "section": meta.get("section"),
                            "source_article": meta.get("source_article"),
                            "source_section": meta.get("source_section"),
                            "is_forced_split": meta.get("is_forced_split", False),
                            "language": meta["language"],
                            "ocr_used": meta["ocr_used"],
                            "char_count": len(rec["text"]),
                            "created_at": datetime.now(timezone.utc),
                            "organization_id": organization_id,
                        }
                    )
                    if meta["ocr_used"]:
                        any_ocr = True
                    languages_seen.add(meta["language"])
                    max_page = max(max_page, meta["page"])

                if chunk_docs:
                    await get_collection("chunks").insert_many(chunk_docs)
                    invalidate_embedding_dimension_cache()
                    await faiss_manager.add_vectors(chunk_docs)

                language = "+".join(sorted(languages_seen)) if languages_seen else "unknown"
                await get_collection("documents").update_one(
                    {"id": doc_id},
                    {
                        "$set": {
                            "total_pages": max_page,
                            "total_chunks": len(records),
                            "ocr_used": any_ocr,
                            "language": language,
                            "status": "ready",
                            "updated_at": datetime.now(timezone.utc),
                        }
                    },
                )
                await get_collection("document_sources").update_one(
                    {"document_id": doc_id},
                    {"$set": {"language": language}},
                )
                pbar.update(1)

            logger.info("Done %s: %s chunks stored", filename, len(records))
            doc = await get_collection("documents").find_one({"id": doc_id})
            return _doc_to_out(doc)

        except Exception as e:
            logger.exception("Processing failed for %s", filename)
            await get_collection("documents").update_one(
                {"id": doc_id},
                {
                    "$set": {
                        "status": "error",
                        "error_message": str(e)[:500],
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            doc = await get_collection("documents").find_one({"id": doc_id})
            return _doc_to_out(doc)


async def get_document(db, doc_id: str) -> Optional[dict]:
    return _doc_to_out(await get_collection("documents").find_one({"id": doc_id}))


async def get_document_source(db, doc_id: str) -> Optional[dict]:
    source = await get_collection("document_sources").find_one({"document_id": doc_id})
    return _source_to_out(source) if source else None


async def list_documents(
    db,
    skip: int = 0,
    limit: int = 50,
    organization_id: str | None = None,
) -> tuple[list[dict], int]:
    query = {"organization_id": organization_id} if organization_id else {}
    total = await get_collection("documents").count_documents(query)
    cursor = get_collection("documents").find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = [_doc_to_out(doc) async for doc in cursor]
    return docs, int(total)


async def get_chunks(db, doc_id: str, skip: int = 0, limit: int = 100) -> tuple[list[dict], int]:
    total = await get_collection("chunks").count_documents({"document_id": doc_id})
    cursor = (
        get_collection("chunks")
        .find({"document_id": doc_id})
        .sort("chunk_index", 1)
        .skip(skip)
        .limit(limit)
    )
    chunks = [_chunk_to_out(chunk) async for chunk in cursor]
    return chunks, int(total)


async def get_raw_pages(db, doc_id: str, skip: int = 0, limit: int = 100) -> tuple[list[dict], int]:
    total = await get_collection("document_raw_pages").count_documents({"document_id": doc_id})
    cursor = (
        get_collection("document_raw_pages")
        .find({"document_id": doc_id})
        .sort("page_number", 1)
        .skip(skip)
        .limit(limit)
    )
    raw_pages = [_raw_page_to_out(page) async for page in cursor]
    return raw_pages, int(total)


async def get_cleaned_pages(db, doc_id: str, skip: int = 0, limit: int = 100) -> tuple[list[dict], int]:
    total = await get_collection("document_cleaned_texts").count_documents({"document_id": doc_id})
    cursor = (
        get_collection("document_cleaned_texts")
        .find({"document_id": doc_id})
        .sort([("page_number", 1), ("version", -1)])
        .skip(skip)
        .limit(limit)
    )
    cleaned_pages = [_cleaned_text_to_out(page) async for page in cursor]
    return cleaned_pages, int(total)


class ExigenceExtractor:
    """Extract legal exigences using LLM."""

    EXTRACTION_PROMPT = """You are a legal expert specializing in Tunisian law. Your task is to extract all legal exigences (requirements) from the given legal text.

A legal exigence is any normative requirement that states what MUST be done (obligation), what MUST NOT be done (prohibition), what CONDITIONS must be met, or what SANCTIONS apply.

Categories:
- **obligation**: A mandatory requirement (e.g., "must", "shall", "is required to")
- **prohibition**: A forbidden requirement (e.g., "must not", "shall not", "is prohibited")
- **condition**: A prerequisite or conditional requirement (e.g., "if", "provided that", "subject to")
- **sanction**: A penalty or consequence (e.g., "shall be punished", "penalty", "forfeiture")

The legal text to analyze:
---
{text}
---

Please extract all exigences and return a JSON array with this exact structure (return ONLY valid JSON, no markdown, no code blocks):
[
  {{
    "type": "obligation|prohibition|condition|sanction",
    "text": "the exact exigence text extracted from the source",
    "article": "article reference if mentioned (e.g., 'Article 95', 'الفصل 95')",
    "confidence": 0.95,
    "citation": "surrounding context where this exigence appears"
  }},
  ...
]

If no exigences found, return an empty array: []

Important:
- Extract the EXACT text from the source, preserving language
- Be thorough - include ALL normative requirements
- Do not invent, infer, paraphrase, or normalize legal wording beyond what is explicitly visible in the text
- If the text is too noisy or unclear to quote faithfully, return [] for that part instead of guessing
- Confidence should be 0.0 to 1.0
- Return ONLY JSON, no other text"""

    @staticmethod
    async def extract_exigences(
        cleaned_text: str,
        page_number: int,
        language: str = "unknown",
    ) -> list[dict]:
        try:
            settings = get_settings()
            prompt = ExigenceExtractor.EXTRACTION_PROMPT.format(text=cleaned_text)
            response_text = await llm_service.call_ollama(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Tunisian legal expert. Extract only exigences explicitly visible in the text, as JSON only."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                base_url=settings.llm_base_url,
            )
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```", 1)[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            import json

            exigences = json.loads(response_text)
            grounded_exigences: list[dict] = []
            for exigence in exigences if isinstance(exigences, list) else []:
                if not isinstance(exigence, dict):
                    continue
                if not _is_grounded_exigence(exigence, cleaned_text):
                    continue
                exigence["confidence"] = float(exigence.get("confidence", 0.5))
                exigence["type"] = str(exigence.get("type", "")).strip().lower()
                exigence["page_number"] = page_number
                exigence["language"] = language
                grounded_exigences.append(exigence)
            return grounded_exigences
        except Exception as e:
            logger.warning("Exigence extraction failed for page %s: %s", page_number, e)
            return []


async def extract_and_store_exigences(
    db,
    doc_id: str,
    cleaned_pages: list[dict],
    language: str = "unknown",
) -> int:
    if not cleaned_pages:
        return 0

    exigence_docs: list[dict] = []
    now = datetime.now(timezone.utc)

    for cleaned_page in cleaned_pages:
        extracted = await ExigenceExtractor.extract_exigences(
            cleaned_page.get("cleaned_text", ""),
            cleaned_page.get("page_number", 0),
            language=language,
        )
        for exig in extracted:
            exigence_docs.append(
                {
                    "id": str(uuid.uuid4()),
                    "document_id": doc_id,
                    "cleaned_text_id": cleaned_page.get("id"),
                    "page_number": cleaned_page.get("page_number"),
                    "article_reference": exig.get("article"),
                    "exigence_type": exig.get("type", "obligation"),
                    "text": exig.get("text", ""),
                    "confidence_score": exig.get("confidence", 0.0),
                    "source_citation": exig.get("citation"),
                    "extracted_at": now,
                }
            )

    if exigence_docs:
        await get_collection("exigences").insert_many(exigence_docs)
        logger.info("Extracted and stored %s exigences for document %s", len(exigence_docs), doc_id)

    return len(exigence_docs)


async def get_exigences(
    db,
    doc_id: str,
    exigence_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[dict], int, dict]:
    query: dict = {"document_id": doc_id}
    if exigence_type:
        query["exigence_type"] = exigence_type

    total = await get_collection("exigences").count_documents(query)
    cursor = (
        get_collection("exigences")
        .find(query)
        .sort([("page_number", 1), ("confidence_score", -1)])
        .skip(skip)
        .limit(limit)
    )
    exigences = [_exigence_to_out(exigence) async for exigence in cursor]

    type_counts: dict[str, int] = {}
    type_cursor = (
        get_collection("exigences")
        .aggregate([
            {"$match": {"document_id": doc_id}},
            {"$group": {"_id": "$exigence_type", "count": {"$sum": 1}}},
        ])
    )
    async for row in type_cursor:
        type_counts[row["_id"]] = row["count"]

    return exigences, int(total), type_counts


# ─────────────────────────────────────────────────────────────
# Amendment upload — article-level diff and replacement
# ─────────────────────────────────────────────────────────────

def _normalize_article_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _diff_articles(
    old_articles: list[dict],
    new_articles: list[dict],
) -> dict:
    old_map = {a["article_key"]: a for a in old_articles}
    new_map = {a["article_key"]: a for a in new_articles}

    added = []
    modified = []
    removed = []
    unchanged = []

    for key, new_art in new_map.items():
        if key not in old_map:
            added.append(new_art)
        else:
            old_norm = _normalize_article_text(old_map[key]["text"])
            new_norm = _normalize_article_text(new_art["text"])
            if old_norm != new_norm:
                modified.append({"old": old_map[key], "new": new_art})
            else:
                unchanged.append(new_art)

    for key in old_map:
        if key not in new_map:
            removed.append(old_map[key])

    return {
        "added": added,
        "modified": modified,
        "removed": removed,
        "unchanged": unchanged,
    }


def _detect_page_language(text: str) -> str:
    arabic = len(re.findall(r"[؀-ۿ]", text))
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


def _split_pages_by_language(
    cleaned_pages: list[dict],
) -> dict[str, list[dict]]:
    """Group cleaned pages by detected language (fr / ar)."""
    groups: dict[str, list[dict]] = {"fr": [], "ar": []}
    for page in cleaned_pages:
        lang = _detect_page_language(page.get("cleaned_text", ""))
        if lang == "ar":
            groups["ar"].append(page)
        else:
            groups["fr"].append(page)
    return groups


def _segment_by_language(
    cleaned_pages: list[dict],
    loi_code: str,
) -> list[dict]:
    """Segment pages into articles, treating each language independently."""
    groups = _split_pages_by_language(cleaned_pages)
    all_articles: list[dict] = []

    for lang, pages in groups.items():
        if not pages:
            continue
        full_text, page_map = build_page_map(pages)
        articles = segment_text_into_articles(
            full_text, loi_code, page_map, language=lang,
        )
        all_articles.extend(articles)

    # Deduplicate by article_key — if same article appears in both languages,
    # keep the one with more text (the substantive version)
    seen: dict[str, dict] = {}
    for art in all_articles:
        key = art["article_key"]
        if key not in seen or len(art["text"]) > len(seen[key]["text"]):
            seen[key] = art
    return list(seen.values())


async def _detect_loi_from_text(text: str) -> tuple[dict | None, dict | None]:
    """
    Scan text for references to existing lois (by name or code).
    Searches in both French and Arabic independently.
    Returns (loi, existing_document) or (None, None).
    """
    text_norm = unicodedata.normalize("NFKC", text)

    all_lois = await get_collection("lois").find({}).to_list(length=1000)
    best_loi = None
    best_score = 0

    for loi in all_lois:
        score = 0
        loi_name = (loi.get("name") or "").strip()
        loi_code = (loi.get("code") or "").strip()

        # Match French name (case-insensitive)
        if loi_name:
            name_lower = loi_name.lower()
            if name_lower in text_norm.lower():
                score = len(loi_name)

        # Match Arabic name (no case, exact substring in normalized text)
        arabic_chars = re.findall(r"[؀-ۿ]+", loi_name)
        for arabic_token in arabic_chars:
            if len(arabic_token) >= 3 and arabic_token in text_norm:
                score = max(score, len(arabic_token) + 5)

        # Match code (word boundary)
        if loi_code and re.search(
            r"\b" + re.escape(loi_code) + r"\b", text, re.IGNORECASE
        ):
            score = max(score, len(loi_code) + 10)

        if score > best_score:
            best_score = score
            best_loi = loi

    if not best_loi:
        return None, None

    existing_doc = await get_collection("documents").find_one({
        "loi_id": best_loi["id"],
        "status": "ready",
    })
    return best_loi, existing_doc


async def upload_amendment_document(
    db,
    filename: str,
    file_bytes: bytes,
    loi_id: str | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> dict:
    """
    Upload an amendment document (e.g. from JORT). The system:
    1. Extracts text from the uploaded file
    2. Auto-detects the target loi by scanning the text for law references
    3. Finds the existing document linked to that loi
    4. Compares articles and applies changes (add/modify/repeal)
    5. Replaces the old document with the updated version

    Returns a summary with diff stats and the new document.
    """
    from pathlib import Path as _Path

    # ── Step 1: Extract text from the new file ──────────────────────
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    doc_id = str(uuid.uuid4())
    ext = _Path(filename).suffix.lower()
    saved_path = upload_dir / f"{doc_id}{ext}"
    saved_path.write_bytes(file_bytes)
    now = datetime.now(timezone.utc)

    extractor = EXTRACTORS.get(ext)
    if extractor is None:
        saved_path.unlink(missing_ok=True)
        raise ValueError(f"Unsupported file type: {ext}")

    pages = extractor(saved_path, original_filename=filename)
    if not pages:
        saved_path.unlink(missing_ok=True)
        raise ValueError("No text extracted from the uploaded file")

    # ── Step 2: Auto-detect target loi from content ─────────────────
    preview_text = "\n".join(
        (p.get("text") or "")[:2000] for p in pages[:5]
    )

    loi = None
    existing_doc = None

    if loi_id:
        loi = await get_collection("lois").find_one({"id": loi_id})
        if not loi:
            saved_path.unlink(missing_ok=True)
            raise ValueError(f"Loi '{loi_id}' not found")
        existing_doc = await get_collection("documents").find_one({
            "loi_id": loi_id, "status": "ready",
        })
    else:
        loi, existing_doc = await _detect_loi_from_text(preview_text)
        if not loi:
            saved_path.unlink(missing_ok=True)
            raise ValueError(
                "Impossible de détecter la loi cible dans le document. "
                "Aucune loi existante n'a été trouvée dans le texte. "
                "Veuillez spécifier loi_id manuellement."
            )
        loi_id = loi["id"]
        logger.info("Auto-detected loi: %s (%s)", loi.get("code"), loi.get("name"))

    loi_code = loi.get("code", "LOI")

    extracted_at = datetime.now(timezone.utc)
    raw_pages: list[dict] = []
    for page_data in pages:
        page_text = (page_data.get("text") or "").strip()
        if not page_text:
            continue
        raw_pages.append({
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "page_number": int(page_data.get("page", 1)),
            "raw_text": page_text,
            "ocr_used": bool(page_data.get("ocr_used", False)),
            "extracted_at": extracted_at,
        })

    # Clean pages in memory for article segmentation
    from app.processing.legal_cleaner import clean_page as legal_clean_page, detect_repeated_elements

    all_raw_texts = [p.get("raw_text", "") for p in raw_pages]
    repeated_elements = detect_repeated_elements(all_raw_texts)
    new_cleaned_pages: list[dict] = []
    for raw_page in raw_pages:
        basic_text, basic_rules, _ = TextCleaningRules.apply_cleaning(raw_page.get("raw_text", ""))
        legal_text, legal_rules, _ = legal_clean_page(basic_text, repeated_elements=repeated_elements)
        new_cleaned_pages.append({
            "page_number": raw_page.get("page_number"),
            "cleaned_text": legal_text,
        })

    # ── Step 2: Segment new document into articles (per language) ────
    new_articles = _segment_by_language(new_cleaned_pages, loi_code)

    # ── Step 3: Segment old document into articles (per language) ──
    diff_result = {"added": [], "modified": [], "removed": [], "unchanged": []}
    old_doc_id = None

    if existing_doc:
        old_doc_id = existing_doc["id"]
        old_cleaned = await get_collection("document_cleaned_texts").find(
            {"document_id": old_doc_id}
        ).sort("page_number", 1).to_list(length=None)

        if old_cleaned:
            old_articles = _segment_by_language(old_cleaned, loi_code)
            diff_result = _diff_articles(old_articles, new_articles)

    # ── Step 4: Apply article-level changes to loi articles/versions ──
    articles_col = get_collection("articles")
    versions_col = get_collection("article_versions")
    applied_ops = []

    for new_art in diff_result["added"]:
        art_doc = {
            "id": str(uuid.uuid4()),
            "loi_id": loi_id,
            "article_key": new_art["article_key"],
            "article_number": new_art["article_number"],
            "article_heading": new_art["article_heading"],
            "hierarchy_titre": new_art["hierarchy"].get("titre"),
            "hierarchy_chapitre": new_art["hierarchy"].get("chapitre"),
            "hierarchy_section": new_art["hierarchy"].get("section"),
            "created_at": now,
        }
        await articles_col.insert_one(art_doc)
        ver_doc = {
            "id": str(uuid.uuid4()),
            "article_id": art_doc["id"],
            "version_num": 1,
            "text": new_art["text"],
            "status": "active",
            "language": new_art.get("language", loi.get("language", "fr")),
            "source_document_id": doc_id,
            "source_pages": new_art.get("pages", []),
            "created_at": now,
        }
        await versions_col.insert_one(ver_doc)
        applied_ops.append({
            "type": "ADD",
            "article_key": new_art["article_key"],
            "article_number": new_art["article_number"],
        })

    for mod in diff_result["modified"]:
        new_art = mod["new"]
        existing_article = await articles_col.find_one({
            "loi_id": loi_id,
            "article_key": new_art["article_key"],
        })
        if existing_article:
            active_v = await versions_col.find_one(
                {"article_id": existing_article["id"], "status": "active"},
                sort=[("version_num", -1)],
            )
            old_version_id = None
            if active_v:
                old_version_id = active_v["id"]
                await versions_col.update_one(
                    {"id": active_v["id"]},
                    {"$set": {"status": "superseded", "updated_at": now}},
                )
            all_versions = await versions_col.find(
                {"article_id": existing_article["id"]}, {"version_num": 1}
            ).to_list(length=None)
            max_v = max((int(v.get("version_num", 0)) for v in all_versions), default=0)

            new_ver = {
                "id": str(uuid.uuid4()),
                "article_id": existing_article["id"],
                "version_num": max_v + 1,
                "text": new_art["text"],
                "status": "active",
                "language": new_art.get("language", loi.get("language", "fr")),
                "source_document_id": doc_id,
                "source_pages": new_art.get("pages", []),
                "created_at": now,
            }
            await versions_col.insert_one(new_ver)

            await audit_service.log_event(
                db, "version_superseded",
                loi_id=loi_id,
                article_id=existing_article["id"],
                old_version_id=old_version_id,
                new_version_id=new_ver["id"],
                actor="amendment_upload",
            )
            applied_ops.append({
                "type": "REPLACE",
                "article_key": new_art["article_key"],
                "article_number": new_art["article_number"],
                "old_version_id": old_version_id,
                "new_version_id": new_ver["id"],
            })
        else:
            art_doc = {
                "id": str(uuid.uuid4()),
                "loi_id": loi_id,
                "article_key": new_art["article_key"],
                "article_number": new_art["article_number"],
                "article_heading": new_art["article_heading"],
                "created_at": now,
            }
            await articles_col.insert_one(art_doc)
            ver_doc = {
                "id": str(uuid.uuid4()),
                "article_id": art_doc["id"],
                "version_num": 1,
                "text": new_art["text"],
                "status": "active",
                "language": new_art.get("language", loi.get("language", "fr")),
                "source_document_id": doc_id,
                "source_pages": new_art.get("pages", []),
                "created_at": now,
            }
            await versions_col.insert_one(ver_doc)
            applied_ops.append({
                "type": "ADD",
                "article_key": new_art["article_key"],
                "article_number": new_art["article_number"],
            })

    for old_art in diff_result["removed"]:
        existing_article = await articles_col.find_one({
            "loi_id": loi_id,
            "article_key": old_art["article_key"],
        })
        if existing_article:
            active_v = await versions_col.find_one(
                {"article_id": existing_article["id"], "status": "active"},
            )
            if active_v:
                await versions_col.update_one(
                    {"id": active_v["id"]},
                    {"$set": {"status": "repealed", "updated_at": now}},
                )
                await audit_service.log_event(
                    db, "article_repealed",
                    loi_id=loi_id,
                    article_id=existing_article["id"],
                    old_version_id=active_v["id"],
                    actor="amendment_upload",
                )
            applied_ops.append({
                "type": "REPEAL",
                "article_key": old_art["article_key"],
                "article_number": old_art["article_number"],
            })

    # ── Step 4b: Notify all company profiles about amendment ─────────
    from app.services.notification_service import notify_amendment_summary

    total_notifs = 0
    try:
        total_notifs = await notify_amendment_summary(
            db,
            loi_id=loi_id,
            loi_code=loi_code,
            loi_name=loi.get("name", loi_code),
            diff={
                "added": len(diff_result["added"]),
                "modified": len(diff_result["modified"]),
                "removed": len(diff_result["removed"]),
            },
            operations=applied_ops,
        )
    except Exception:
        logger.warning("Failed to send amendment notifications", exc_info=True)

    # ── Step 5: Replace old document with new one ───────────────────
    if old_doc_id:
        await delete_document(db, old_doc_id)

    new_doc = await upload_document(
        db, filename, file_bytes,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if new_doc and new_doc.get("id"):
        await get_collection("documents").update_one(
            {"id": new_doc["id"]},
            {"$set": {"document_type": "loi_principale", "loi_id": loi_id}},
        )

    await audit_service.log_event(
        db, "amendment_uploaded",
        loi_id=loi_id,
        details={
            "old_document_id": old_doc_id,
            "new_document_id": new_doc.get("id") if new_doc else None,
            "filename": filename,
            "added": len(diff_result["added"]),
            "modified": len(diff_result["modified"]),
            "removed": len(diff_result["removed"]),
            "unchanged": len(diff_result["unchanged"]),
        },
        actor="amendment_upload",
    )

    # Clean up the temp extraction file
    saved_path.unlink(missing_ok=True)

    logger.info(
        "Amendment upload complete: %s → added=%d modified=%d removed=%d unchanged=%d",
        filename,
        len(diff_result["added"]),
        len(diff_result["modified"]),
        len(diff_result["removed"]),
        len(diff_result["unchanged"]),
    )

    return {
        "document": new_doc,
        "old_document_id": old_doc_id,
        "diff": {
            "added": len(diff_result["added"]),
            "modified": len(diff_result["modified"]),
            "removed": len(diff_result["removed"]),
            "unchanged": len(diff_result["unchanged"]),
        },
        "operations": applied_ops,
        "notifications_sent": total_notifs,
        "message": (
            f"Document '{filename}' mis à jour: "
            f"{len(diff_result['added'])} ajoutés, "
            f"{len(diff_result['modified'])} modifiés, "
            f"{len(diff_result['removed'])} supprimés, "
            f"{len(diff_result['unchanged'])} inchangés."
            + (f" {total_notifs} notification(s) envoyée(s)." if total_notifs else "")
        ),
    }


async def delete_document(db, doc_id: str) -> bool:
    upload_dir = settings.upload_dir
    for file_path in upload_dir.glob(f"{doc_id}.*"):
        file_path.unlink(missing_ok=True)

    deleted_related = 0
    for collection_name in [
        "chunks",
        "document_raw_pages",
        "document_cleaned_texts",
        "document_sources",
        "exigences",
        "amendment_operations",
    ]:
        result = await get_collection(collection_name).delete_many({"document_id": doc_id})
        deleted_related += int(result.deleted_count)

    doc_result = await get_collection("documents").delete_one({"id": doc_id})
    deleted_documents = int(doc_result.deleted_count)

    # Consider cleanup successful if we removed either the document itself
    # or any dependent records tied to the given document_id.
    ok = (deleted_documents + deleted_related) > 0
    if ok:
        invalidate_embedding_dimension_cache()
        await faiss_manager.remove_by_document_id(doc_id)
    return ok


async def clear_all_documents(db) -> int:
    doc_count = await get_collection("documents").count_documents({})
    if doc_count == 0:
        return 0

    upload_dir = settings.upload_dir
    if upload_dir.exists():
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                file_path.unlink(missing_ok=True)

    for collection_name in [
        "chunks",
        "documents",
        "document_sources",
        "document_raw_pages",
        "document_cleaned_texts",
        "exigences",
        "amendment_operations",
    ]:
        await get_collection(collection_name).delete_many({})

    logger.info("Cleared database: %s documents removed", doc_count)
    invalidate_embedding_dimension_cache()
    await faiss_manager.rebuild()
    return int(doc_count)


async def cleanup_orphaned_uploads(db, max_age_hours: int = 48) -> int:
    """Remove uploaded files not referenced by any document or older than max_age_hours."""
    upload_dir = settings.upload_dir
    if not upload_dir.exists():
        return 0

    # Collect known doc IDs from the database
    known_ids: set[str] = set()
    async for doc in get_collection("documents").find({}, {"_id": 1}):
        known_ids.add(str(doc["_id"]))

    now = datetime.now(timezone.utc)
    removed = 0
    for file_path in upload_dir.iterdir():
        if not file_path.is_file():
            continue
        file_doc_id = file_path.stem  # filename is {doc_id}.ext
        if file_doc_id in known_ids:
            continue
        # Check age for safety — only remove files older than threshold
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
        age_hours = (now - mtime).total_seconds() / 3600
        if age_hours >= max_age_hours:
            file_path.unlink(missing_ok=True)
            removed += 1
    if removed:
        logger.info("Cleaned up %d orphaned upload(s) older than %dh", removed, max_age_hours)
    return removed


async def reindex_all_documents(
    db,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> dict:
    """Rebuild chunks + embeddings for all documents using stored raw pages."""
    total_docs = await get_collection("documents").count_documents({})
    await get_collection("chunks").delete_many({})
    invalidate_embedding_dimension_cache()

    processed_docs = 0
    total_chunks = 0
    now = datetime.now(timezone.utc)

    async for doc in get_collection("documents").find({}):
        doc_id = doc.get("id")
        filename = doc.get("filename") or "unknown"

        raw_pages = await get_collection("document_raw_pages").find(
            {"document_id": doc_id}
        ).sort("page_number", 1).to_list(length=None)

        pages = [
            {
                "text": page.get("raw_text", ""),
                "page": page.get("page_number", 1),
                "ocr_used": bool(page.get("ocr_used", False)),
            }
            for page in raw_pages
            if page.get("raw_text")
        ]

        if not pages:
            continue

        records = build_records(
            pages,
            filename,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        if not records:
            continue

        embeddings = await embed_texts_async([r["text"] for r in records])

        any_ocr = False
        languages_seen: set[str] = set()
        max_page = 0
        chunk_docs: list[dict] = []

        for rec, emb in zip(records, embeddings):
            meta = rec["metadata"]
            chunk_docs.append(
                {
                    "id": str(uuid.uuid4()),
                    "document_id": doc_id,
                    "chunk_index": meta["chunk_index"],
                    "text": rec["text"],
                    "embedding": emb,
                    "page_number": meta["page"],
                    "section": meta.get("section"),
                    "source_article": meta.get("source_article"),
                    "source_section": meta.get("source_section"),
                    "is_forced_split": meta.get("is_forced_split", False),
                    "language": meta["language"],
                    "ocr_used": meta["ocr_used"],
                    "char_count": len(rec["text"]),
                    "created_at": now,
                }
            )
            if meta["ocr_used"]:
                any_ocr = True
            languages_seen.add(meta["language"])
            max_page = max(max_page, meta["page"])

        if chunk_docs:
            await get_collection("chunks").insert_many(chunk_docs)
            total_chunks += len(chunk_docs)

        language = "+".join(sorted(languages_seen)) if languages_seen else doc.get("language") or "unknown"
        await get_collection("documents").update_one(
            {"id": doc_id},
            {
                "$set": {
                    "total_pages": max_page or doc.get("total_pages"),
                    "total_chunks": len(records),
                    "ocr_used": any_ocr or doc.get("ocr_used", False),
                    "language": language,
                    "updated_at": now,
                }
            },
        )

        processed_docs += 1

    await faiss_manager.rebuild()
    return {
        "documents_total": int(total_docs),
        "documents_reindexed": int(processed_docs),
        "chunks_rebuilt": int(total_chunks),
    }


async def bulk_upload_from_data(
    db,
    data_dir: Path,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[dict]:
    files = sorted(
        f for f in data_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        return []

    results: list[dict] = []
    logger.info("Bulk upload: %s files from %s", len(files), data_dir)

    for file_path in tqdm(files, desc="Overall", unit="file", file=sys.stderr):
        content = file_path.read_bytes()
        doc = await upload_document(
            db,
            file_path.name,
            content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        results.append(doc)

    ok = sum(1 for r in results if r.get("status") == "ready")
    fail = len(results) - ok
    total_chunks = sum(r.get("total_chunks", 0) for r in results)
    logger.info("Bulk upload done: %s succeeded, %s failed, %s total chunks", ok, fail, total_chunks)
    return results
