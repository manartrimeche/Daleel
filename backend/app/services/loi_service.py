"""
Loi Service — CRUD for Loi / Article / ArticleVersion + document segmentation.

Workflow (Sprint 3, Step 4):
  1. Administrator creates a Loi record (code, name, language…)
  2. A document is uploaded (existing Sprint 1 pipeline)
  3. POST /lois/{loi_id}/segment-document triggers this service:
       • Fetches all cleaned pages for that document
       • Calls article_segmenter.segment_text_into_articles()
       • Upserts Article records (create or reuse existing)
       • Creates ArticleVersion records (always new, never overwrite)
       • Links the document to the Loi
"""

import logging
import uuid
from datetime import datetime, timezone

from app.database import get_collection
from app.processing.article_segmenter import build_page_map, segment_text_into_articles

logger = logging.getLogger(__name__)



# ─────────────────────────────────────────────────────────────
# Serialisers
# ─────────────────────────────────────────────────────────────

def _loi_to_dict(loi: dict, total_articles: int | None = None) -> dict:
    return {
        "id": loi.get("id"),
        "code": loi.get("code"),
        "name": loi.get("name"),
        "jurisdiction": loi.get("jurisdiction"),
        "language": loi.get("language"),
        "description": loi.get("description"),
        "version_label": loi.get("version_label"),
        "total_articles": total_articles,
        "created_at": loi.get("created_at"),
        "updated_at": loi.get("updated_at"),
    }


def _article_to_dict(
    article: dict,
    active_version_id: str | None = None,
    total_versions: int | None = None,
) -> dict:
    return {
        "id": article.get("id"),
        "loi_id": article.get("loi_id"),
        "article_key": article.get("article_key"),
        "article_number": article.get("article_number"),
        "article_heading": article.get("article_heading"),
        "hierarchy": {
            "titre": article.get("hierarchy_titre"),
            "chapitre": article.get("hierarchy_chapitre"),
            "section": article.get("hierarchy_section"),
        },
        "active_version_id": active_version_id,
        "total_versions": total_versions,
        "created_at": article.get("created_at"),
    }


def _version_to_dict(
    version: dict,
    article_key: str | None = None,
    total_exigences: int | None = None,
    total_actions: int | None = None,
) -> dict:
    return {
        "id": version.get("id"),
        "article_id": version.get("article_id"),
        "article_key": article_key,
        "version_num": version.get("version_num"),
        "text": version.get("text"),
        "status": version.get("status"),
        "language": version.get("language"),
        "source_document_id": version.get("source_document_id"),
        "source_pages": version.get("source_pages") or [],
        "effective_date": version.get("effective_date"),
        "total_exigences": total_exigences,
        "total_actions": total_actions,
        "created_at": version.get("created_at"),
    }


# ─────────────────────────────────────────────────────────────
# Loi CRUD
# ─────────────────────────────────────────────────────────────

async def create_loi(
    db,
    code: str,
    name: str,
    jurisdiction: str = "tunisia",
    language: str = "fr",
    description: str | None = None,
    version_label: str | None = None,
) -> dict:
    """Create a new Loi. Raises ValueError if code already exists."""
    # Check uniqueness
    existing = await get_collection("lois").find_one({"code": code.upper()})
    if existing:
        raise ValueError(f"Loi with code '{code}' already exists (id={existing['id']})")

    now = datetime.now(timezone.utc)
    loi = {
        "id": str(uuid.uuid4()),
        "code": code.upper(),
        "name": name,
        "jurisdiction": jurisdiction,
        "language": language,
        "description": description,
        "version_label": version_label,
        "created_at": now,
        "updated_at": now,
    }
    await get_collection("lois").insert_one(loi)
    logger.info("Created Loi: %s — %s (%s)", loi["code"], loi["name"], loi["id"])
    return _loi_to_dict(loi, total_articles=0)


async def get_loi(db, loi_id: str) -> dict | None:
    """Get a Loi by ID with article count."""
    loi = await get_collection("lois").find_one({"id": loi_id})
    if not loi:
        return None
    total = await get_collection("articles").count_documents({"loi_id": loi_id})
    return _loi_to_dict(loi, total_articles=total)


async def get_loi_by_code(db, code: str) -> dict | None:
    """Get a Loi by its short code (case-insensitive)."""
    loi = await get_collection("lois").find_one({"code": code.upper()})
    if not loi:
        return None
    total = await get_collection("articles").count_documents({"loi_id": loi["id"]})
    return _loi_to_dict(loi, total_articles=total)


async def list_lois(
    db,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    """Return paginated list of all Lois with article counts."""
    total = await get_collection("lois").count_documents({})
    cursor = get_collection("lois").find({}).sort("code", 1).skip(skip).limit(limit)
    lois = []
    async for loi in cursor:
        cnt = await get_collection("articles").count_documents({"loi_id": loi["id"]})
        lois.append(_loi_to_dict(loi, total_articles=cnt))
    return lois, int(total)


async def update_loi(db, loi_id: str, **kwargs) -> dict | None:
    """Partial update of a Loi's metadata fields."""
    loi = await get_collection("lois").find_one({"id": loi_id})
    if not loi:
        return None
    allowed = {"name", "jurisdiction", "language", "description", "version_label"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        await get_collection("lois").update_one({"id": loi_id}, {"$set": updates})
        loi.update(updates)
    total = await get_collection("articles").count_documents({"loi_id": loi_id})
    return _loi_to_dict(loi, total_articles=total)


async def delete_loi(db, loi_id: str) -> bool:
    """Delete a Loi and cascade to its articles/versions."""
    loi = await get_collection("lois").find_one({"id": loi_id})
    if not loi:
        return False
    article_ids = [article["id"] async for article in get_collection("articles").find({"loi_id": loi_id}, {"id": 1})]
    version_ids = [version["id"] async for version in get_collection("article_versions").find({"article_id": {"$in": article_ids}}, {"id": 1})]

    for collection_name, query in [
        ("action_criticalities", {"action_id": {"$in": [action["id"] async for action in get_collection("actions").find({"article_version_id": {"$in": version_ids}}, {"id": 1})]}}),
        ("action_dependencies", {"action_id": {"$in": [action["id"] async for action in get_collection("actions").find({"article_version_id": {"$in": version_ids}}, {"id": 1})]}}),
        ("actions", {"article_version_id": {"$in": version_ids}}),
        ("exigences", {"article_version_id": {"$in": version_ids}}),
        ("article_versions", {"article_id": {"$in": article_ids}}),
        ("articles", {"loi_id": loi_id}),
        ("audit_logs", {"loi_id": loi_id}),
        ("amendment_operations", {"loi_id": loi_id}),
        ("documents", {"loi_id": loi_id}),
    ]:
        await get_collection(collection_name).delete_many(query)

    await get_collection("lois").delete_one({"id": loi_id})
    logger.info("Deleted Loi %s", loi_id)
    return True


# ─────────────────────────────────────────────────────────────
# Article queries
# ─────────────────────────────────────────────────────────────

async def list_articles(
    db,
    loi_id: str,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> tuple[list[dict], int]:
    """List articles for a Loi, optionally filtered by keyword."""
    query: dict = {"loi_id": loi_id}
    if search:
        regex = {"$regex": search, "$options": "i"}
        query["$or"] = [{"article_heading": regex}, {"article_number": regex}, {"article_key": regex}]

    total = await get_collection("articles").count_documents(query)
    cursor = get_collection("articles").find(query).sort("article_number", 1).skip(skip).limit(limit)

    result = []
    async for art in cursor:
        active_v = await get_collection("article_versions").find_one(
            {"article_id": art["id"], "status": "active"},
            sort=[("version_num", -1)],
            projection={"id": 1},
        )
        total_v = await get_collection("article_versions").count_documents({"article_id": art["id"]})
        result.append(_article_to_dict(art, active_version_id=active_v["id"] if active_v else None, total_versions=total_v))

    return result, int(total)


async def get_article(db, article_id: str) -> dict | None:
    """Get an Article by UUID."""
    art = await get_collection("articles").find_one({"id": article_id})
    if not art:
        return None
    active_v = await get_collection("article_versions").find_one(
        {"article_id": art["id"], "status": "active"},
        sort=[("version_num", -1)],
        projection={"id": 1},
    )
    total_v = await get_collection("article_versions").count_documents({"article_id": art["id"]})
    return _article_to_dict(art, active_version_id=active_v["id"] if active_v else None, total_versions=total_v)


async def get_article_by_key(
    db, loi_id: str, article_key: str
) -> dict | None:
    """Get an Article by its unique key within a Loi (e.g. 'CT-Art-95')."""
    art = await get_collection("articles").find_one({"loi_id": loi_id, "article_key": article_key})
    if not art:
        return None
    return await get_article(db, art.id)


async def list_article_versions(
    db,
    article_id: str,
) -> tuple[list[dict], int]:
    """List all versions of an Article (active + history)."""
    art = await get_collection("articles").find_one({"id": article_id})
    cursor = get_collection("article_versions").find({"article_id": article_id}).sort("version_num", 1)

    result = []
    async for version in cursor:
        exig_count = await get_collection("exigences").count_documents({"article_version_id": version["id"]})
        action_count = await get_collection("actions").count_documents({"article_version_id": version["id"]})
        result.append(_version_to_dict(
            version,
            article_key=art["article_key"] if art else None,
            total_exigences=exig_count,
            total_actions=action_count,
        ))

    return result, len(result)


async def get_article_version(db, version_id: str) -> dict | None:
    """Get a specific ArticleVersion by UUID."""
    v = await get_collection("article_versions").find_one({"id": version_id})
    if not v:
        return None
    art = await get_collection("articles").find_one({"id": v["article_id"]})
    exig_count = await get_collection("exigences").count_documents({"article_version_id": v["id"]})
    action_count = await get_collection("actions").count_documents({"article_version_id": v["id"]})
    return _version_to_dict(
        v,
        article_key=art["article_key"] if art else None,
        total_exigences=exig_count,
        total_actions=action_count,
    )


# ─────────────────────────────────────────────────────────────
# Document → Article segmentation
# ─────────────────────────────────────────────────────────────

async def segment_document(
    db,
    loi_id: str,
    document_id: str,
    language_override: str | None = None,
    auto_extract_exigences: bool = True,
    auto_extract_actions: bool = True,
) -> dict:
    """
    Segment an uploaded document into articles and store them under the given Loi.

    Algorithm:
      1. Verify Loi and Document exist.
      2. Load all cleaned pages ordered by page_number.
      3. Build full_text + page_map.
      4. Call segment_text_into_articles().
      5. For each extracted article:
           - If article_key already exists for this Loi → create new ArticleVersion
             (mark old active → superseded).
           - Otherwise → create new Article + ArticleVersion(v1).
      6. Link Document.loi_id → loi_id.

        Returns:
            {
                articles_created,
                articles_updated,
                total_articles,
                exigences_extracted,
                actions_extracted,
                loi_id,
                document_id,
                message,
            }
    """
    # ── 1. Verify entities ──
    loi = await get_collection("lois").find_one({"id": loi_id})
    if not loi:
        raise ValueError(f"Loi '{loi_id}' not found")

    doc = await get_collection("documents").find_one({"id": document_id})
    if not doc:
        raise ValueError(f"Document '{document_id}' not found")

    # ── 2. Load cleaned pages ──
    cleaned_pages = await get_collection("document_cleaned_texts").find({"document_id": document_id}).sort("page_number", 1).to_list(length=None)

    if not cleaned_pages:
        raise ValueError(
            f"No cleaned text found for document '{document_id}'. "
            "Make sure the document has been processed (status=ready)."
        )

    # ── 3. Build full text + page map ──
    full_text, page_map = build_page_map(cleaned_pages)

    # ── 4. Segment ──
    language = language_override or loi.get("language")
    extracted = segment_text_into_articles(full_text, loi["code"], page_map, language=language)

    if not extracted:
        raise ValueError(
            f"No articles detected in document '{document_id}'. "
            "Check the document language and format."
        )

    logger.info("Segmentation: %s articles found in doc=%s", len(extracted), document_id)

    # ── 5. Upsert articles & versions ──
    now = datetime.now(timezone.utc)
    articles_created = 0
    articles_updated = 0
    exigences_extracted = 0
    actions_extracted = 0
    versions_to_extract: list[tuple[str, str, str, str]] = []

    for art_data in extracted:
        article_key = art_data["article_key"]

        # Does this article already exist in this Loi?
        existing_article = await get_collection("articles").find_one({
            "loi_id": loi_id,
            "article_key": article_key,
        })

        if existing_article:
            article = existing_article
            await get_collection("article_versions").update_many(
                {"article_id": article["id"], "status": "active"},
                {"$set": {"status": "superseded", "updated_at": now}},
            )
            versions_cursor = get_collection("article_versions").find({"article_id": article["id"]}, {"version_num": 1})
            max_version = 0
            async for version_doc in versions_cursor:
                max_version = max(max_version, int(version_doc.get("version_num", 0)))
            version_num = max_version + 1
            articles_updated += 1
        else:
            # Create new Article
            article = {
                "id": str(uuid.uuid4()),
                "loi_id": loi_id,
                "article_key": article_key,
                "article_number": art_data["article_number"],
                "article_heading": art_data["article_heading"],
                "hierarchy_titre": art_data["hierarchy"].get("titre"),
                "hierarchy_chapitre": art_data["hierarchy"].get("chapitre"),
                "hierarchy_section": art_data["hierarchy"].get("section"),
                "created_at": now,
            }
            await get_collection("articles").insert_one(article)
            version_num = 1
            articles_created += 1

        # Create new ArticleVersion (always immutable)
        version = {
            "id": str(uuid.uuid4()),
            "article_id": article["id"],
            "version_num": version_num,
            "text": art_data["text"],
            "status": "active",
            "language": art_data.get("language", language),
            "source_document_id": document_id,
            "source_pages": art_data.get("pages", []),
            "created_at": now,
        }
        await get_collection("article_versions").insert_one(version)

        if auto_extract_exigences:
            versions_to_extract.append(
                (
                    version["id"],
                    version["text"],
                    art_data["article_key"],
                    art_data.get("language", language),
                )
            )

    # ── 6. Link Document → Loi ──
    await get_collection("documents").update_one({"id": document_id}, {"$set": {"loi_id": loi_id, "updated_at": now}})

    # ── 7. Optional phase-6 auto extraction (article-level) ──
    if auto_extract_exigences and versions_to_extract:
        from app.services.document_service import ExigenceExtractor
        from app.services import action_service

        for version_id, version_text, article_key, version_language in versions_to_extract:
            extracted = await ExigenceExtractor.extract_exigences(
                cleaned_text=version_text,
                page_number=1,
                language=version_language,
            )

            if not extracted:
                continue

            extracted_at = datetime.now(timezone.utc)
            exigence_docs = []
            for exig in extracted:
                exigence_docs.append({
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "cleaned_text_id": None,
                    "page_number": 1,
                    "article_reference": article_key,
                    "exigence_type": exig.get("type", "obligation"),
                    "text": exig.get("text", ""),
                    "confidence_score": float(exig.get("confidence", 0.0)),
                    "source_citation": exig.get("citation"),
                    "article_version_id": version_id,
                    "extracted_at": extracted_at,
                })

            if not exigence_docs:
                continue

            await get_collection("exigences").insert_many(exigence_docs)
            exigences_extracted += len(exigence_docs)

            if auto_extract_actions:
                result = await action_service.extract_and_store_actions(
                    db,
                    article_version_id=version_id,
                    exigence_ids=None,
                )
                actions_extracted += int(result.get("actions_created", 0))

    total = articles_created + articles_updated
    logger.info(
        f"Segmentation complete: loi={loi['code']}, doc={document_id} "
        f"→ {articles_created} created, {articles_updated} updated"
    )
    return {
        "loi_id": loi_id,
        "document_id": document_id,
        "articles_created": articles_created,
        "articles_updated": articles_updated,
        "total_articles": total,
        "exigences_extracted": exigences_extracted,
        "actions_extracted": actions_extracted,
        "message": (
            f"Segmentation successful: {articles_created} new articles, "
            f"{articles_updated} articles updated with a new version, "
            f"{exigences_extracted} exigences extracted, "
            f"{actions_extracted} actions extracted."
        ),
    }
