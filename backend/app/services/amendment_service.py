"""
Amendment Service — Sprint 5 (Steps 10–12 of the workflow).

Step 10: classify_document()         — mark a document as 'modificatif'
Step 11: extract_amendment_ops()     — LLM extraction of ADD/REPLACE/MODIFY/REPEAL ops
Step 12: apply_amendment_operation() — immutable versioning (new ArticleVersion, audit log)
         apply_all_pending()         — apply all pending ops for a document
"""

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.database import get_collection
from app.services import audit_service, llm_service

logger = logging.getLogger(__name__)
settings = get_settings()



# ─────────────────────────────────────────────────────────────
# LLM Prompt
# ─────────────────────────────────────────────────────────────

_EXTRACTION_PROMPT = """You are a Tunisian legal expert specializing in legislative amendments.

Analyze the following amendment document and extract every modification operation that affects the articles of the target law.

**Target Law:** {loi_name} (internal code: {loi_code})

**Amendment Text:**
---
{text}
---

For EACH operation found, extract:

1. **operation_type** — one of: ADD | REPLACE | MODIFY | REPEAL
   - ADD     : a new article is inserted  (FR: "il est ajouté/inséré", AR: "يُضاف/يُدرج")
   - REPLACE : entire article replaced    (FR: "modifié et rédigé comme suit:", AR: "يُعدَّل على النحو التالي:")
   - MODIFY  : partial modification       (FR: "l'alinéa X est remplacé par:", AR: "تُستبدل الفقرة")
   - REPEAL  : article abrogated          (FR: "est abrogé/supprimé", AR: "يُلغى/يُحذف")

2. **target_article_number** — article number (use Western digits: "95", "15 bis", not "٩٥")
3. **new_text** — full replacement/addition text for ADD/REPLACE/MODIFY; null for REPEAL
4. **proof_extract** — the exact verbatim sentence from the document proving this operation
5. **legal_reference** — citation of the amending law (e.g. "Loi n° 2023-45 du 12 mars 2023")
6. **confidence** — 0.0 to 1.0

Rules:
- Only extract operations explicitly stated in the text
- Do NOT infer or guess operations not mentioned
- Include the complete new_text without truncation
- Only include operations affecting {loi_code}

**Response — JSON array ONLY, no markdown:**
[
  {{
    "operation_type": "REPLACE",
    "target_article_number": "95",
    "new_text": "L'employeur est tenu de remettre au salarié, avant la prise de poste...",
    "proof_extract": "L'article 95 du Code du Travail est modifié et rédigé comme suit :",
    "legal_reference": "Loi n° 2023-45 du 12 mars 2023",
    "confidence": 0.94
  }}
]

If no operations are found for {loi_code}, return [].
"""

# Arabic numerals normalisation
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def _norm_article_num(s: str) -> str:
    return s.translate(_ARABIC_DIGITS).strip()


# ─────────────────────────────────────────────────────────────
# Serialiser
# ─────────────────────────────────────────────────────────────

def _op_to_dict(op: dict) -> dict:
    return {
        "id": op.get("id"),
        "amendment_doc_id": op.get("amendment_doc_id"),
        "loi_id": op.get("loi_id"),
        "operation_type": op.get("operation_type"),
        "target_article_key": op.get("target_article_key"),
        "target_article_number": op.get("target_article_number"),
        "new_text": op.get("new_text"),
        "proof_extract": op.get("proof_extract"),
        "legal_reference": op.get("legal_reference"),
        "confidence": op.get("confidence"),
        "status": op.get("status"),
        "applied_at": op.get("applied_at"),
        "old_version_id": op.get("old_version_id"),
        "new_version_id": op.get("new_version_id"),
        "created_at": op.get("created_at"),
    }


# ─────────────────────────────────────────────────────────────
# Step 10 — Document classification
# ─────────────────────────────────────────────────────────────

async def classify_document(
    db,
    document_id: str,
    document_type: str,
    loi_id: Optional[str] = None,
) -> dict:
    """
    Mark a document as 'loi_principale', 'modificatif', or 'autre'.
    Optionally link to a Loi.

    Returns the updated document dict.
    """
    doc = await get_collection("documents").find_one({"id": document_id})
    if not doc:
        raise ValueError(f"Document '{document_id}' not found")

    valid_types = {"loi_principale", "modificatif", "autre"}
    if document_type not in valid_types:
        raise ValueError(f"document_type must be one of {valid_types}")

    if document_type == "modificatif" and not loi_id:
        raise ValueError("loi_id is required when document_type is 'modificatif'")

    if loi_id:
        loi = await get_collection("lois").find_one({"id": loi_id})
        if not loi:
            raise ValueError(f"Loi '{loi_id}' not found")

    updates = {"document_type": document_type, "updated_at": datetime.now(timezone.utc)}
    if loi_id:
        updates["loi_id"] = loi_id
    await get_collection("documents").update_one({"id": document_id}, {"$set": updates})

    # Audit
    await audit_service.log_event(
        db,
        "document_classified",
        loi_id=loi_id,
        details={"document_id": document_id, "document_type": document_type},
    )

    logger.info(f"Document {document_id} classified as '{document_type}' (loi={loi_id})")
    return {
        "id": doc["id"],
        "filename": doc["filename"],
        "document_type": document_type,
        "loi_id": loi_id or doc.get("loi_id"),
        "status": doc.get("status"),
    }


# ─────────────────────────────────────────────────────────────
# Step 11 — LLM extraction
# ─────────────────────────────────────────────────────────────

async def extract_amendment_operations(
    db,
    document_id: str,
    loi_id: str,
    language_override: Optional[str] = None,
) -> dict:
    """
    Extract ADD/REPLACE/MODIFY/REPEAL operations from an amendment document via LLM.

    Requires the document to have been processed (status=ready) and have cleaned pages.

    Returns: {document_id, loi_id, operations_extracted, by_type, message}
    """
    doc = await get_collection("documents").find_one({"id": document_id})
    if not doc:
        raise ValueError(f"Document '{document_id}' not found")

    loi = await get_collection("lois").find_one({"id": loi_id})
    if not loi:
        raise ValueError(f"Loi '{loi_id}' not found")

    # Load cleaned pages
    cleaned_pages = await get_collection("document_cleaned_texts").find({"document_id": document_id}).sort("page_number", 1).to_list(length=None)

    if not cleaned_pages:
        raise ValueError(
            f"No cleaned text for document '{document_id}'. Process the document first."
        )

    full_text = "\n\n".join(p.get("cleaned_text", "") for p in cleaned_pages)

    # Build LLM prompt
    prompt = _EXTRACTION_PROMPT.format(
        loi_name=loi.name,
        loi_code=loi["code"],
        text=full_text[:12000],  # Limit to model context
    )

    try:
        response = await llm_service.call_ollama(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Tunisian legal expert. "
                        "Extract amendment operations as a JSON array only. "
                        "No markdown, no extra text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.05,
            base_url=settings.llm_base_url,
        )

        response = response.strip()
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        if not response.strip().startswith("["):
            match = re.search(r"\[.*\]", response, re.DOTALL)
            response = match.group(0) if match else "[]"

        raw_ops = json.loads(response.strip())
        if not isinstance(raw_ops, list):
            raw_ops = []

    except Exception as e:
        logger.error("LLM extraction failed for document %s: %s", document_id, e)
        raw_ops = []

    # Persist operations
    valid_types = {"ADD", "REPLACE", "MODIFY", "REPEAL"}
    now = datetime.now(timezone.utc)
    op_docs = []
    by_type: dict[str, int] = {}

    for raw in raw_ops:
        if not isinstance(raw, dict):
            continue
        op_type = str(raw.get("operation_type", "")).strip().upper()
        if op_type not in valid_types:
            continue
        article_num = _norm_article_num(str(raw.get("target_article_number", "")).strip())
        if not article_num:
            continue
        article_num_clean = re.sub(r"\s+", "", article_num)
        article_key = f"{loi.code}-Art-{article_num_clean}"
        proof = str(raw.get("proof_extract", "")).strip()
        if not proof:
            continue

        op_docs.append({
            "id": str(uuid.uuid4()),
            "amendment_doc_id": document_id,
            "loi_id": loi_id,
            "operation_type": op_type,
            "target_article_key": article_key,
            "target_article_number": article_num,
            "new_text": str(raw.get("new_text", "")).strip() or None,
            "proof_extract": proof[:2000],
            "legal_reference": str(raw.get("legal_reference", "")).strip()[:512] or None,
            "confidence": max(0.0, min(1.0, float(raw.get("confidence", 0.7)))),
            "status": "pending",
            "created_at": now,
        })
        by_type[op_type] = by_type.get(op_type, 0) + 1

    if op_docs:
        await get_collection("amendment_operations").insert_many(op_docs)

    # Audit
    await audit_service.log_event(
        db,
        "amendment_extracted",
        loi_id=loi_id,
        details={
            "document_id": document_id,
            "operations_found": len(op_docs),
            "by_type": by_type,
        },
    )

    logger.info(
        f"Extracted {len(op_docs)} amendment operations from doc={document_id} loi={loi['code']}"
    )
    return {
        "document_id": document_id,
        "loi_id": loi_id,
        "operations_extracted": len(op_docs),
        "by_type": by_type,
        "message": (
            f"Extracted {len(op_docs)} operations: {by_type}. "
            f"Use POST /amendment-operations/{{id}}/apply to apply them."
        ),
    }


# ─────────────────────────────────────────────────────────────
# Step 12 — Apply operations (immutable versioning)
# ─────────────────────────────────────────────────────────────

async def apply_amendment_operation(
    db,
    operation_id: str,
    actor: str = "system",
) -> dict:
    """
    Apply one pending AmendmentOperation.

    REPLACE / MODIFY:
      1. Find Article by target_article_key in the loi.
      2. Get current active ArticleVersion.
      3. Create new ArticleVersion(version_num+1, status='active').
      4. Mark old version as 'superseded'.
      5. Write audit log.

    REPEAL:
      1. Find Article by target_article_key.
      2. Mark active ArticleVersion as 'repealed'.
      3. Write audit log.

    ADD:
      1. Check if Article already exists (idempotent).
      2. Create Article (if new) + ArticleVersion(v1, status='active').
      3. Write audit log.
    """
    op = await get_collection("amendment_operations").find_one({"id": operation_id})
    if not op:
        raise ValueError(f"AmendmentOperation '{operation_id}' not found")
    if op.get("status") == "applied":
        raise ValueError(f"Operation '{operation_id}' is already applied")
    if op.get("status") == "rejected":
        raise ValueError(f"Operation '{operation_id}' has been rejected")

    now = datetime.now(timezone.utc)
    loi = await get_collection("lois").find_one({"id": op["loi_id"]})

    # ── Find target article ──
    existing_article = await get_collection("articles").find_one({
        "loi_id": op["loi_id"],
        "article_key": op["target_article_key"],
    })

    old_version_id: Optional[str] = None
    new_version_id: Optional[str] = None
    event_type: str = "amendment_applied"

    # ── ADD ──────────────────────────────────────────────────
    if op["operation_type"] == "ADD":
        if existing_article:
            # Article already exists — treat ADD as a new version (idempotent)
            logger.warning(
                f"ADD operation target {op.target_article_key} already exists — "
                "creating new version instead"
            )
            active_v = await get_collection("article_versions").find_one(
                {"article_id": existing_article["id"], "status": "active"},
                sort=[("version_num", -1)],
            )
            if active_v:
                old_version_id = active_v["id"]
                await get_collection("article_versions").update_one(
                    {"id": active_v["id"]},
                    {"$set": {"status": "superseded", "updated_at": now}},
                )
            versions = await get_collection("article_versions").find({"article_id": existing_article["id"]}, {"version_num": 1}).to_list(length=None)
            max_v = max((int(v.get("version_num", 0)) for v in versions), default=0)
            article = existing_article
            version_num = max_v + 1
        else:
            article = {
                "id": str(uuid.uuid4()),
                "loi_id": op["loi_id"],
                "article_key": op["target_article_key"],
                "article_number": op["target_article_number"],
                "article_heading": f"Article {op['target_article_number']}",
                "created_at": now,
            }
            await get_collection("articles").insert_one(article)
            version_num = 1

        new_v = {
            "id": str(uuid.uuid4()),
            "article_id": article["id"],
            "version_num": version_num,
            "text": op.get("new_text") or "",
            "status": "active",
            "language": loi["language"] if loi else "fr",
            "source_document_id": op["amendment_doc_id"],
            "source_pages": [],
            "created_at": now,
        }
        await get_collection("article_versions").insert_one(new_v)
        new_version_id = new_v["id"]

    # ── REPLACE / MODIFY ─────────────────────────────────────
    elif op["operation_type"] in ("REPLACE", "MODIFY"):
        if not existing_article:
            # Article not found — create it as if ADD
            article = {
                "id": str(uuid.uuid4()),
                "loi_id": op["loi_id"],
                "article_key": op["target_article_key"],
                "article_number": op["target_article_number"],
                "article_heading": f"Article {op['target_article_number']}",
                "created_at": now,
            }
            await get_collection("articles").insert_one(article)
            version_num = 1
        else:
            article = existing_article
            # Supersede current active version
            active_v = await get_collection("article_versions").find_one(
                {"article_id": article["id"], "status": "active"},
                sort=[("version_num", -1)],
            )
            if active_v:
                old_version_id = active_v["id"]
                await get_collection("article_versions").update_one(
                    {"id": active_v["id"]},
                    {"$set": {"status": "superseded", "updated_at": now}},
                )
                # Audit supersession
                await audit_service.log_event(
                    db,
                    "version_superseded",
                    loi_id=op["loi_id"],
                    article_id=article["id"],
                    old_version_id=active_v["id"],
                    amendment_op_id=op["id"],
                    proof_extract=op.get("proof_extract"),
                    legal_reference=op.get("legal_reference"),
                    confidence=op.get("confidence", 1.0),
                    actor=actor,
                )
            versions = await get_collection("article_versions").find({"article_id": article["id"]}, {"version_num": 1}).to_list(length=None)
            max_v = max((int(v.get("version_num", 0)) for v in versions), default=0)
            version_num = max_v + 1

        new_v = {
            "id": str(uuid.uuid4()),
            "article_id": article["id"],
            "version_num": version_num,
            "text": op.get("new_text") or "",
            "status": "active",
            "language": loi["language"] if loi else "fr",
            "source_document_id": op["amendment_doc_id"],
            "source_pages": [],
            "created_at": now,
        }
        await get_collection("article_versions").insert_one(new_v)
        new_version_id = new_v["id"]

    # ── REPEAL ───────────────────────────────────────────────
    elif op["operation_type"] == "REPEAL":
        if not existing_article:
            await get_collection("amendment_operations").update_one({"id": op["id"]}, {"$set": {"status": "rejected", "updated_at": now}})
            raise ValueError(
                f"Cannot repeal: article '{op['target_article_key']}' not found in loi '{op['loi_id']}'"
            )
        active_v = await get_collection("article_versions").find_one(
            {"article_id": existing_article["id"], "status": "active"},
            sort=[("version_num", -1)],
        )
        if active_v:
            old_version_id = active_v["id"]
            await get_collection("article_versions").update_one(
                {"id": active_v["id"]},
                {"$set": {"status": "repealed", "updated_at": now}},
            )
            event_type = "article_repealed"

    # ── Update operation record ──────────────────────────────
    await get_collection("amendment_operations").update_one(
        {"id": op["id"]},
        {"$set": {
            "status": "applied",
            "applied_at": now,
            "old_version_id": old_version_id,
            "new_version_id": new_version_id,
        }},
    )

    # Main audit entry
    await audit_service.log_event(
        db,
        event_type,
        loi_id=op["loi_id"],
        article_id=existing_article["id"] if existing_article else None,
        old_version_id=old_version_id,
        new_version_id=new_version_id,
        amendment_op_id=op["id"],
        proof_extract=op.get("proof_extract"),
        legal_reference=op.get("legal_reference"),
        confidence=op.get("confidence", 1.0),
        actor=actor,
        details={
            "operation_type": op["operation_type"],
            "target_article_key": op["target_article_key"],
        },
    )

    logger.info(
        f"Applied {op['operation_type']} on {op['target_article_key']}: "
        f"old={old_version_id} new={new_version_id}"
    )

    return {
        "operation_id": op["id"],
        "loi_id": op["loi_id"],
        "operation_type": op["operation_type"],
        "target_article_key": op["target_article_key"],
        "old_version_id": old_version_id,
        "new_version_id": new_version_id,
        "status": "applied",
        "message": (
            f"{op['operation_type']} applied to {op['target_article_key']}. "
            + (f"New version: {new_version_id}." if new_version_id else "Article repealed.")
        ),
    }


async def apply_all_pending(
    db,
    document_id: str,
    actor: str = "system",
) -> dict:
    """Apply all pending AmendmentOperations for a document, in creation order."""
    pending = await get_collection("amendment_operations").find({
        "amendment_doc_id": document_id,
        "status": "pending",
    }).sort("created_at", 1).to_list(length=None)

    total_pending = len(pending)
    results = []
    applied = 0
    failed = 0
    loi_ids_affected = set()

    for op in pending:
        try:
            result = await apply_amendment_operation(db, op["id"], actor=actor)
            results.append(result)
            applied += 1
            if result.get("loi_id"):
                loi_ids_affected.add(result["loi_id"])
        except Exception as e:
            logger.error("Failed to apply operation %s: %s", op['id'], e)
            await get_collection("amendment_operations").update_one({"id": op["id"]}, {"$set": {"status": "rejected", "updated_at": datetime.now(timezone.utc)}})
            results.append({
                "operation_id": op["id"],
                "loi_id": op.get("loi_id"),
                "operation_type": op["operation_type"],
                "target_article_key": op["target_article_key"],
                "old_version_id": None,
                "new_version_id": None,
                "status": "rejected",
                "message": str(e),
            })
            failed += 1

    logger.info(
        f"apply_all_pending: doc={document_id} total={total_pending} "
        f"applied={applied} failed={failed}"
    )
    return {
        "document_id": document_id,
        "loi_ids_affected": list(loi_ids_affected),
        "total_pending": total_pending,
        "applied": applied,
        "failed": failed,
        "results": results,
        "message": (
            f"Applied {applied}/{total_pending} operations. "
            + (f"{failed} failed." if failed else "All successful.")
        ),
    }


# ─────────────────────────────────────────────────────────────
# Queries
# ─────────────────────────────────────────────────────────────

async def list_operations(
    db,
    document_id: str,
    status: Optional[str] = None,
) -> tuple[list[dict], int, dict, dict]:
    """List all AmendmentOperations for a document."""
    query: dict = {"amendment_doc_id": document_id}
    if status:
        query["status"] = status

    total = await get_collection("amendment_operations").count_documents(query)
    ops = await get_collection("amendment_operations").find(query).sort("created_at", 1).to_list(length=None)

    by_type_rows = await get_collection("amendment_operations").aggregate([
        {"$match": {"amendment_doc_id": document_id}},
        {"$group": {"_id": "$operation_type", "count": {"$sum": 1}}},
    ]).to_list(length=None)
    by_type = {row["_id"]: row["count"] for row in by_type_rows}

    by_status_rows = await get_collection("amendment_operations").aggregate([
        {"$match": {"amendment_doc_id": document_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]).to_list(length=None)
    by_status = {row["_id"]: row["count"] for row in by_status_rows}

    return [_op_to_dict(op) for op in ops], int(total), by_type, by_status
