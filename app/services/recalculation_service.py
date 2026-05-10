"""
Recalculation Service — Sprint 5 (Step 14 of the workflow).

Triggered automatically after amendment operations are applied.

Pipeline for each impacted ArticleVersion:
  1. Re-extract Exigences from the new article text
  2. Re-extract Actions from the new Exigences
  3. Re-compute Criticality for the new Actions
  4. Roadmap re-generates dynamically on next GET (no explicit step needed)

All steps write to the AuditLog for traceability.
"""

import logging
import uuid
from datetime import datetime, timezone

from app.database import get_collection
from app.services import audit_service, criticality_service

logger = logging.getLogger(__name__)



async def recalculate_after_amendment(
    db,
    loi_id: str,
    new_version_ids: list[str],
    actor: str = "system",
) -> dict:
    """Run the full recalculation pipeline for new ArticleVersions."""
    if not new_version_ids:
        return {
            "loi_id": loi_id,
            "versions_processed": 0,
            "exigences_extracted": 0,
            "actions_extracted": 0,
            "criticalities_computed": 0,
            "message": "No versions to recalculate.",
        }

    from app.services.document_service import ExigenceExtractor
    from app.services.action_service import extract_and_store_actions

    loi = await _collection("lois").find_one({"id": loi_id})
    language = loi.get("language") if loi else "fr"

    total_exigences = 0
    total_actions = 0
    total_criticalities = 0
    versions_processed = 0

    for version_id in new_version_ids:
        version = await _collection("article_versions").find_one({"id": version_id})
        if not version or version.get("status") != "active":
            continue

        article = await _collection("articles").find_one({"id": version.get("article_id")})
        article_ref = article.get("article_key") if article else "unknown"
        logger.info("Recalculation: processing %s (version=%s)", article_ref, version_id)

        try:
            extracted = await ExigenceExtractor.extract_exigences(
                cleaned_text=version.get("text", ""),
                page_number=1,
                language=language,
            )

            now = datetime.now(timezone.utc)
            exigence_docs = []
            for exig in extracted:
                exigence_docs.append({
                    "id": str(uuid.uuid4()),
                    "document_id": version.get("source_document_id") or "",
                    "cleaned_text_id": None,
                    "page_number": 1,
                    "article_reference": article_ref,
                    "exigence_type": exig.get("type", "obligation"),
                    "text": exig.get("text", ""),
                    "confidence_score": float(exig.get("confidence", 0.5)),
                    "source_citation": exig.get("citation"),
                    "article_version_id": version_id,
                    "extracted_at": now,
                })

            if exigence_docs:
                await _collection("exigences").insert_many(exigence_docs)
                total_exigences += len(exigence_docs)
                logger.info("  Re-extracted %s exigences for %s", len(exigence_docs), article_ref)
        except Exception as exc:
            logger.error("Exigence re-extraction failed for version %s: %s", version_id, exc)

        try:
            result = await extract_and_store_actions(
                db,
                article_version_id=version_id,
                exigence_ids=None,
            )
            total_actions += result.get("actions_created", 0)
        except Exception as exc:
            logger.error("Action re-extraction failed for version %s: %s", version_id, exc)

        try:
            crit_result = await criticality_service.compute_for_article_version(
                db,
                article_version_id=version_id,
                recompute=True,
            )
            total_criticalities += crit_result.get("computed", 0)
        except Exception as exc:
            logger.error("Criticality recomputation failed for version %s: %s", version_id, exc)

        versions_processed += 1

    await audit_service.log_event(
        db,
        "recalculation_done",
        loi_id=loi_id,
        actor=actor,
        details={
            "versions_processed": versions_processed,
            "exigences_extracted": total_exigences,
            "actions_extracted": total_actions,
            "criticalities_computed": total_criticalities,
        },
    )

    logger.info(
        "Recalculation complete: loi=%s versions=%s exigences=%s actions=%s criticalities=%s",
        loi_id,
        versions_processed,
        total_exigences,
        total_actions,
        total_criticalities,
    )
    return {
        "loi_id": loi_id,
        "versions_processed": versions_processed,
        "exigences_extracted": total_exigences,
        "actions_extracted": total_actions,
        "criticalities_computed": total_criticalities,
        "message": (
            f"Recalculation done: {versions_processed} versions processed, "
            f"{total_exigences} exigences, {total_actions} actions, "
            f"{total_criticalities} criticalities recomputed. "
            f"Roadmap will reflect changes on next GET."
        ),
    }


async def recalculate_for_loi(
    db,
    loi_id: str,
    actor: str = "system",
) -> dict:
    """Recalculate all active ArticleVersions for a Loi."""
    versions = await _collection("article_versions").find({
        "status": "active",
        "article_id": {
            "$in": [article["id"] async for article in _collection("articles").find({"loi_id": loi_id}, {"id": 1})],
        },
    }).to_list(length=None)

    active_version_ids = [version["id"] for version in versions]
    return await recalculate_after_amendment(
        db,
        loi_id,
        active_version_ids,
        actor=actor,
    )
