"""
Case Document Service — Document intake and analysis for compliance cases.

This module extends the case management system with:
- Document role classification (incoming_request, evidence, policy, etc.)
- OCR/text extraction for images and scanned PDFs
- Document summarization using LLM
- Entity extraction (dates, parties, obligations, deadlines, references)
- Analysis result storage in case context

Integrates with:
- document_service.py for base document processing
- extractor.py and ocr.py for text extraction
- llm_service.py for classification and extraction
"""

from __future__ import annotations

import logging
import uuid
import re
from datetime import datetime, timezone, date
from typing import Optional
from pathlib import Path

from app.database import get_collection
from app.config import get_settings
from app.services import document_service, llm_service, audit_service

logger = logging.getLogger(__name__)
settings = get_settings()

# ─────────────────────────────────────────────────────────────
# Document Roles
# ─────────────────────────────────────────────────────────────

DOCUMENT_ROLES = (
    "incoming_request",    # External request/inquiry received
    "evidence",            # Supporting evidence for case
    "policy",              # Internal policy document
    "contract",            # Contract or agreement
    "authority_notice",    # Notice from regulatory authority
    "draft_response",      # Draft response being prepared
    "other",               # Uncategorized
)

# ─────────────────────────────────────────────────────────────
# Document Type Classifications
# ─────────────────────────────────────────────────────────────

DOCUMENT_TYPES = (
    "legal_opinion",
    "regulatory_filing",
    "court_decision",
    "administrative_notice",
    "contract",
    "policy_document",
    "correspondence",
    "evidence_material",
    "identification_document",
    "financial_record",
    "unknown",
)

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def _is_image_file(filename: str) -> bool:
    """Check if file is an image that needs OCR."""
    ext = Path(filename).suffix.lower()
    return ext in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"}


def _is_scanned_pdf(filename: str, content_preview: str | None = None) -> bool:
    """Heuristic to detect scanned PDFs that may need OCR."""
    ext = Path(filename).suffix.lower()
    if ext != ".pdf":
        return False
    # If we have preview text and it's very short or garbled, likely scanned
    if content_preview:
        # Check if text is suspiciously short
        cleaned = content_preview.strip()
        if len(cleaned) < 100:
            return True
        # Check for garbled text patterns (control chars OR high non-ASCII)
        garbled_chars = sum(1 for c in cleaned
                          if (ord(c) < 32 and c not in '\n\r\t')  # Control chars
                          or (ord(c) > 127 and not (0x0600 <= ord(c) <= 0x06FF)))  # Non-Arabic high bytes
        if garbled_chars > len(cleaned) * 0.1:  # >10% garbled chars
            return True
    return False


# ─────────────────────────────────────────────────────────────
# Serializers
# ─────────────────────────────────────────────────────────────

def _case_doc_analysis_to_dict(doc: dict) -> dict:
    """Serialize case document with analysis."""
    return {
        "id": doc.get("id"),
        "case_id": doc.get("case_id"),
        "document_id": doc.get("document_id"),
        "role": doc.get("role", "other"),
        "label": doc.get("label"),
        "attached_by": doc.get("attached_by"),
        "attached_at": doc.get("attached_at"),
        "analysis": doc.get("analysis"),
    }


def _doc_analysis_result_to_dict(doc: dict) -> dict:
    """Serialize document analysis results."""
    return {
        "document_id": doc.get("document_id"),
        "case_document_id": doc.get("case_document_id"),
        "document_type": doc.get("document_type", "unknown"),
        "summary": doc.get("summary", ""),
        "entities": doc.get("entities", {}),
        "obligations": doc.get("obligations", []),
        "deadlines": doc.get("deadlines", []),
        "parties": doc.get("parties", []),
        "legal_references": doc.get("legal_references", []),
        "confidence": doc.get("confidence", 0.0),
        "analyzed_at": doc.get("analyzed_at"),
        "ocr_used": doc.get("ocr_used", False),
    }


def _extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    if not text:
        return {}

    text = text.strip()
    if text.startswith("```"):
        # Remove opening code block
        text = text.split("```", 1)[1]
        # Remove language identifier if present
        if text.startswith("json"):
            text = text[4:]
        # Remove closing code block
        if "```" in text:
            text = text.rsplit("```", 1)[0]
        text = text.strip()

    try:
        import json
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _parse_flexible_date(date_str: str | None) -> date | None:
    """Parse various date formats commonly found in legal documents.

    Supports:
    - ISO format: 2024-01-15
    - French format: 15 janvier 2024
    - French short: 15/01/2024
    """
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # Try ISO format first
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    # Try French short format: 15/01/2024
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        pass

    # Try French long format: 15 janvier 2024
    french_months = {
        "janvier": 1, "février": 2, "fevrier": 2, "mars": 3,
        "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
        "août": 8, "aout": 8, "septembre": 9, "octobre": 10,
        "novembre": 11, "décembre": 12, "decembre": 12,
    }

    import re
    pattern = r"(\d{1,2})\s+([a-zéû]+)\s+(\d{4})"
    match = re.match(pattern, date_str.lower())
    if match:
        day, month_str, year = match.groups()
        month = french_months.get(month_str)
        if month:
            try:
                return date(int(year), month, int(day))
            except ValueError:
                pass

    return None


# ─────────────────────────────────────────────────────────────
# Document Classification
# ─────────────────────────────────────────────────────────────

CLASSIFICATION_PROMPT = """You are a legal document classification expert specializing in Tunisian and international law.

Analyze the following document content and classify it according to these types:
- legal_opinion: Formal legal analysis or opinion
- regulatory_filing: Submission to regulatory authority
- court_decision: Court judgment or decision
- administrative_notice: Notice from administrative body
- contract: Agreement between parties
- policy_document: Internal policy or procedure
- correspondence: Letters, emails, informal communication
- evidence_material: Supporting evidence, photos, records
- identification_document: ID cards, passports, registration docs
- financial_record: Financial statements, invoices, receipts
- unknown: Cannot determine

Also extract:
1. Document language (ar/fr/en)
2. Brief summary (max 200 words)
3. Primary document type
4. Confidence score (0.0-1.0)

Document content:
---
{text_sample}
---

Return ONLY valid JSON in this exact format:
{{
  "document_type": "type_from_list_above",
  "language": "ar|fr|en",
  "summary": "brief summary in document's language",
  "confidence": 0.85
}}

Return ONLY JSON, no other text."""


async def classify_document(
    text_sample: str,
    language_hint: str = "auto",
) -> dict:
    """Classify a document using LLM."""
    if not text_sample or len(text_sample.strip()) < 20:
        return {
            "document_type": "unknown",
            "language": language_hint if language_hint != "auto" else "unknown",
            "summary": "",
            "confidence": 0.0,
        }

    # Truncate sample if too long
    sample = text_sample[:4000] if len(text_sample) > 4000 else text_sample

    try:
        prompt = CLASSIFICATION_PROMPT.format(text_sample=sample)
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal document classifier. Return ONLY valid JSON."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            base_url=settings.llm_base_url,
        )

        response = response.strip()
        if response.startswith("```"):
            response = response.split("```", 1)[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()

        import json
        result = json.loads(response)

        # Validate and normalize
        doc_type = result.get("document_type", "unknown").lower()
        if doc_type not in DOCUMENT_TYPES:
            doc_type = "unknown"

        return {
            "document_type": doc_type,
            "language": result.get("language", "unknown"),
            "summary": result.get("summary", "")[:500],
            "confidence": float(result.get("confidence", 0.5)),
        }
    except Exception as e:
        logger.warning("Document classification failed: %s", e)
        return {
            "document_type": "unknown",
            "language": "unknown",
            "summary": "",
            "confidence": 0.0,
        }


# ─────────────────────────────────────────────────────────────
# Entity Extraction
# ─────────────────────────────────────────────────────────────

ENTITY_EXTRACTION_PROMPT = """You are a legal entity extraction expert. Extract structured information from the following document.

Extract these entities:
1. Parties: Names of individuals, companies, organizations mentioned
2. Dates: Important dates mentioned (signed dates, effective dates, etc.)
3. Deadlines: Due dates, response deadlines, expiration dates
4. Obligations: Legal obligations, requirements, duties mentioned
5. Legal References: Article numbers, law references, regulation citations
6. Monetary Amounts: Financial figures with currencies

Document content:
---
{text_content}
---

Return ONLY valid JSON in this exact format:
{{
  "parties": ["Party 1", "Party 2"],
  "dates": ["2024-01-15", "2024-03-01"],
  "deadlines": [
    {{"description": "Response deadline", "date": "2024-02-01", "urgent": true}}
  ],
  "obligations": [
    {{"description": "Must submit report", "deadline": "2024-02-15", "source": "Article 5"}}
  ],
  "legal_references": [
    {{"type": "article", "number": "5", "law": "Law 63-2004"}}
  ],
  "monetary_amounts": [
    {{"amount": "50000", "currency": "TND", "context": "Penalty amount"}}
  ],
  "confidence": 0.85
}}

Return ONLY JSON, no other text. Use ISO 8601 date format (YYYY-MM-DD) where possible."""


async def extract_entities(
    text_content: str,
    language: str = "unknown",
) -> dict:
    """Extract structured entities from document text."""
    if not text_content or len(text_content.strip()) < 20:
        return {
            "parties": [],
            "dates": [],
            "deadlines": [],
            "obligations": [],
            "legal_references": [],
            "monetary_amounts": [],
            "confidence": 0.0,
        }

    # Truncate if too long (process in chunks for very long docs)
    sample = text_content[:6000] if len(text_content) > 6000 else text_content

    try:
        prompt = ENTITY_EXTRACTION_PROMPT.format(text_content=sample)
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal entity extraction system. Return ONLY valid JSON."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            base_url=settings.llm_base_url,
        )

        response = response.strip()
        if response.startswith("```"):
            response = response.split("```", 1)[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()

        import json
        result = json.loads(response)

        # Validate and normalize
        return {
            "parties": result.get("parties", [])[:20],  # Limit array sizes
            "dates": result.get("dates", [])[:10],
            "deadlines": result.get("deadlines", [])[:10],
            "obligations": result.get("obligations", [])[:15],
            "legal_references": result.get("legal_references", [])[:10],
            "monetary_amounts": result.get("monetary_amounts", [])[:10],
            "confidence": float(result.get("confidence", 0.5)),
        }
    except Exception as e:
        logger.warning("Entity extraction failed: %s", e)
        return {
            "parties": [],
            "dates": [],
            "deadlines": [],
            "obligations": [],
            "legal_references": [],
            "monetary_amounts": [],
            "confidence": 0.0,
        }


# ─────────────────────────────────────────────────────────────
# OCR Integration
# ─────────────────────────────────────────────────────────────

async def extract_text_with_ocr(
    file_bytes: bytes,
    filename: str,
    hint_arabic: bool = True,
) -> dict:
    """Extract text from image or scanned document using OCR.

    Returns dict with:
    - text: extracted text
    - ocr_used: True
    - page_count: 1 (for images)
    """
    from app.processing.ocr import ocr_image_array
    from PIL import Image
    import io
    import numpy as np

    try:
        # Load image from bytes
        img = Image.open(io.BytesIO(file_bytes))
        img_array = np.array(img)

        # Run OCR
        text = ocr_image_array(img_array, hint_arabic=hint_arabic)

        return {
            "text": text,
            "ocr_used": True,
            "page_count": 1,
            "success": bool(text and len(text.strip()) > 10),
        }
    except Exception as e:
        logger.error("OCR extraction failed for %s: %s", filename, e)
        return {
            "text": "",
            "ocr_used": True,
            "page_count": 0,
            "success": False,
            "error": str(e),
        }


# ─────────────────────────────────────────────────────────────
# Document Upload + Attach
# ─────────────────────────────────────────────────────────────

async def upload_and_attach_document(
    db,
    case_id: str,
    filename: str,
    file_bytes: bytes,
    role: str = "other",
    label: Optional[str] = None,
    attached_by: str = "system",
    run_analysis: bool = True,
    skip_embedding: bool = False,  # For case docs, we may skip vector indexing
) -> dict:
    """Upload a document, attach it to a case, and optionally analyze it.

    This is the main entry point for case document intake.
    """
    # Validate case exists
    case = await get_collection("compliance_cases").find_one({"id": case_id})
    if not case:
        raise ValueError(f"Case '{case_id}' not found")

    # Validate role
    if role not in DOCUMENT_ROLES:
        role = "other"

    # Step 1: Upload document using existing document service
    doc_result = await document_service.upload_document(
        db,
        filename=filename,
        file_bytes=file_bytes,
    )

    if not doc_result:
        raise ValueError("Document upload failed")

    if doc_result.get("status") == "error":
        raise ValueError(f"Document processing failed: {doc_result.get('error_message', 'unknown error')}")

    document_id = doc_result["id"]

    # Step 2: Attach to case with role
    case_doc = await _attach_document_with_role(
        db,
        case_id=case_id,
        document_id=document_id,
        role=role,
        label=label,
        attached_by=attached_by,
    )

    # Step 3: Run analysis if requested
    analysis_result = None
    if run_analysis:
        try:
            analysis_result = await analyze_case_document(
                db,
                case_id=case_id,
                case_document_id=case_doc["id"],
                force_ocr=False,  # Document service already ran OCR if needed
            )
        except Exception as e:
            logger.warning("Document analysis failed for %s: %s", document_id, e)
            # Don't fail the upload if analysis fails

    # Log audit event
    await audit_service.log_event(
        db,
        "case_document_uploaded",
        actor=attached_by,
        details={
            "case_id": case_id,
            "document_id": document_id,
            "case_document_id": case_doc["id"],
            "role": role,
            "filename": filename,
        },
    )

    return {
        "case_document": case_doc,
        "document": doc_result,
        "analysis": analysis_result,
    }


async def _attach_document_with_role(
    db,
    case_id: str,
    document_id: str,
    role: str,
    label: Optional[str] = None,
    attached_by: str = "system",
) -> dict:
    """Internal: Attach document to case with role and metadata."""
    # Check for duplicate attachment
    existing = await get_collection("case_documents").find_one(
        {"case_id": case_id, "document_id": document_id}
    )
    if existing:
        raise ValueError(f"Document '{document_id}' already attached to case '{case_id}'")

    now = _now()
    case_doc = {
        "id": _new_id(),
        "case_id": case_id,
        "document_id": document_id,
        "role": role,
        "label": label,
        "attached_by": attached_by,
        "attached_at": now,
        "analysis": None,
    }

    await get_collection("case_documents").insert_one(case_doc)
    await get_collection("compliance_cases").update_one(
        {"id": case_id}, {"$set": {"updated_at": now}}
    )

    return _case_doc_analysis_to_dict(case_doc)


# ─────────────────────────────────────────────────────────────
# Document Analysis
# ─────────────────────────────────────────────────────────────

async def analyze_case_document(
    db,
    case_id: str,
    case_document_id: str,
    force_ocr: bool = False,
) -> dict:
    """Analyze a case document: classify, summarize, extract entities.

    Stores analysis results in the case_documents collection.
    """
    # Get case document record
    case_doc = await get_collection("case_documents").find_one(
        {"id": case_document_id, "case_id": case_id}
    )
    if not case_doc:
        raise ValueError(f"Case document '{case_document_id}' not found in case '{case_id}'")

    document_id = case_doc["document_id"]

    # Get the actual document
    doc = await get_collection("documents").find_one({"id": document_id})
    if not doc:
        raise ValueError(f"Document '{document_id}' not found")

    # Get cleaned text for analysis
    cleaned_pages = await get_collection("document_cleaned_texts").find(
        {"document_id": document_id}
    ).sort("page_number", 1).to_list(length=None)

    if not cleaned_pages:
        # Try raw pages
        raw_pages = await get_collection("document_raw_pages").find(
            {"document_id": document_id}
        ).sort("page_number", 1).to_list(length=None)
        texts = [p.get("raw_text", "") for p in raw_pages]
    else:
        texts = [p.get("cleaned_text", "") for p in cleaned_pages]

    full_text = "\n\n".join(texts)

    # If no text and force_ocr requested, try OCR
    ocr_used = False
    if not full_text.strip() and force_ocr:
        source = await get_collection("document_sources").find_one({"document_id": document_id})
        if source:
            from pathlib import Path
            source_path = Path(source.get("source_path", ""))
            if source_path.exists() and _is_image_file(source_path.name):
                ocr_result = await extract_text_with_ocr(
                    source_path.read_bytes(),
                    source_path.name,
                    hint_arabic=bool(re.search(r"[\u0600-\u06FF]", doc.get("filename", "")))
                )
                full_text = ocr_result.get("text", "")
                ocr_used = ocr_result.get("ocr_used", False)

    # Detect language
    language = llm_service._get_detect_query_language(full_text[:1000])

    # Run classification
    classification = await classify_document(full_text[:4000], language)

    # Run entity extraction
    entities = await extract_entities(full_text[:6000], language)

    # Build analysis result
    analysis = {
        "document_type": classification["document_type"],
        "language": classification["language"],
        "summary": classification["summary"],
        "entities": entities,
        "ocr_used": ocr_used or doc.get("ocr_used", False),
        "analyzed_at": _now(),
        "confidence": (classification["confidence"] + entities.get("confidence", 0)) / 2,
        "text_sample": full_text[:500] if full_text else "",
    }

    # Store analysis in case_documents
    await get_collection("case_documents").update_one(
        {"id": case_document_id},
        {"$set": {"analysis": analysis, "updated_at": _now()}}
    )

    # Also store in dedicated collection for complex queries
    analysis_record = {
        "id": _new_id(),
        "case_id": case_id,
        "case_document_id": case_document_id,
        "document_id": document_id,
        **analysis,
    }

    # Upsert analysis record
    await get_collection("case_document_analyses").replace_one(
        {"case_document_id": case_document_id},
        analysis_record,
        upsert=True,
    )

    logger.info("Document analysis complete: case_doc=%s, type=%s",
                case_document_id, classification["document_type"])

    return _doc_analysis_result_to_dict(analysis_record)


# ─────────────────────────────────────────────────────────────
# Query and Retrieval
# ─────────────────────────────────────────────────────────────

async def get_case_document_with_analysis(
    db,
    case_id: str,
    case_document_id: str,
) -> dict | None:
    """Get a case document with its analysis."""
    case_doc = await get_collection("case_documents").find_one(
        {"id": case_document_id, "case_id": case_id}
    )
    if not case_doc:
        return None

    # Get document details
    doc = await get_collection("documents").find_one(
        {"id": case_doc["document_id"]}
    )

    result = _case_doc_analysis_to_dict(case_doc)
    if doc:
        result["document"] = document_service._doc_to_out(doc)

    return result


async def list_case_documents_with_analysis(
    db,
    case_id: str,
    role: Optional[str] = None,
    document_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    """List case documents with analysis, optionally filtered by role or type."""
    query: dict = {"case_id": case_id}
    if role:
        query["role"] = role

    total = await get_collection("case_documents").count_documents(query)

    # Use aggregation to join with analysis if filtering by document type
    if document_type:
        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "case_document_analyses",
                    "localField": "id",
                    "foreignField": "case_document_id",
                    "as": "analysis_doc",
                }
            },
            {
                "$match": {
                    "$or": [
                        {"analysis.document_type": document_type},
                        {"analysis_doc.document_type": document_type},
                    ]
                }
            },
            {"$sort": {"attached_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
        ]
        cursor = get_collection("case_documents").aggregate(pipeline)
    else:
        cursor = (
            get_collection("case_documents")
            .find(query)
            .sort("attached_at", -1)
            .skip(skip)
            .limit(limit)
        )

    docs = []
    async for doc in cursor:
        enriched = _case_doc_analysis_to_dict(doc)
        # Get basic document info
        d = await get_collection("documents").find_one({"id": doc["document_id"]})
        if d:
            enriched["document"] = {
                "id": d["id"],
                "filename": d["filename"],
                "file_type": d["file_type"],
                "status": d["status"],
                "total_pages": d.get("total_pages", 0),
            }
        docs.append(enriched)

    return docs, int(total)


async def find_documents_by_entity(
    db,
    case_id: str,
    entity_type: str,  # "party", "deadline", "obligation", "legal_reference"
    entity_value: Optional[str] = None,
) -> list[dict]:
    """Find case documents containing specific entities."""
    query: dict = {"case_id": case_id}

    if entity_type == "party":
        query["analysis.entities.parties"] = {"$exists": True, "$ne": []}
        if entity_value:
            query["analysis.entities.parties"] = {
                "$regex": entity_value, "$options": "i"
            }
    elif entity_type == "deadline":
        query["analysis.entities.deadlines"] = {"$exists": True, "$ne": []}
    elif entity_type == "obligation":
        query["analysis.entities.obligations"] = {"$exists": True, "$ne": []}
    elif entity_type == "legal_reference":
        query["analysis.entities.legal_references"] = {"$exists": True, "$ne": []}

    cursor = get_collection("case_documents").find(query).sort("attached_at", -1)

    docs = []
    async for doc in cursor:
        docs.append(_case_doc_analysis_to_dict(doc))

    return docs


# ─────────────────────────────────────────────────────────────
# Legacy Attach (for compatibility)
# ─────────────────────────────────────────────────────────────

async def attach_existing_document(
    db,
    case_id: str,
    document_id: str,
    role: str = "other",
    label: Optional[str] = None,
    attached_by: str = "system",
    run_analysis: bool = True,
) -> dict:
    """Attach an already-uploaded document to a case with role and optional analysis."""
    # Validate case
    case = await get_collection("compliance_cases").find_one({"id": case_id})
    if not case:
        raise ValueError(f"Case '{case_id}' not found")

    # Validate document
    doc = await get_collection("documents").find_one({"id": document_id})
    if not doc:
        raise ValueError(f"Document '{document_id}' not found")

    if doc.get("status") != "ready":
        raise ValueError(f"Document '{document_id}' is not ready (status: {doc.get('status')})")

    # Validate role
    if role not in DOCUMENT_ROLES:
        role = "other"

    # Check for duplicate
    existing = await get_collection("case_documents").find_one(
        {"case_id": case_id, "document_id": document_id}
    )
    if existing:
        raise ValueError(f"Document '{document_id}' already attached to case '{case_id}'")

    # Create case document record
    now = _now()
    case_doc = {
        "id": _new_id(),
        "case_id": case_id,
        "document_id": document_id,
        "role": role,
        "label": label,
        "attached_by": attached_by,
        "attached_at": now,
        "analysis": None,
    }

    await get_collection("case_documents").insert_one(case_doc)
    await get_collection("compliance_cases").update_one(
        {"id": case_id}, {"$set": {"updated_at": now}}
    )

    # Run analysis if requested
    if run_analysis:
        try:
            await analyze_case_document(db, case_id, case_doc["id"])
        except Exception as e:
            logger.warning("Analysis failed for attached document: %s", e)

    return _case_doc_analysis_to_dict(case_doc)
