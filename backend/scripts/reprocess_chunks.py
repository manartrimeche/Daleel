"""
Re-process all documents: delete old chunks, re-chunk from raw pages
with improved ETL pipeline (Arabic OCR cleaning, quality filter, dedup,
page noise stripping), re-embed, and rebuild FAISS index.
"""
import asyncio
import sys
import io
import os
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("ENVIRONMENT", "development")

from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
from app.processing.chunker import build_records
from app.services.embedding_service import embed_texts_async, get_primary_embedding_dimension
from app.database import get_collection


async def reprocess():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    docs = await get_collection("documents").find(
        {"status": "ready"},
        {"id": 1, "filename": 1, "_id": 0},
    ).to_list(length=10_000)

    print(f"Found {len(docs)} documents to reprocess\n")

    # Warm up embedding model
    print("Loading embedding model...")
    get_primary_embedding_dimension()
    print("Embedding model ready\n")

    total_old = 0
    total_new = 0

    for doc in docs:
        doc_id = doc["id"]
        filename = doc["filename"]

        raw_pages = await get_collection("document_raw_pages").find(
            {"document_id": doc_id},
            {"page_number": 1, "raw_text": 1, "ocr_used": 1, "_id": 0},
        ).sort("page_number", 1).to_list(length=5_000)

        if not raw_pages:
            print(f"  SKIP {filename}: no raw pages stored")
            continue

        pages = [
            {"text": p["raw_text"], "page": p["page_number"], "ocr_used": p.get("ocr_used", False)}
            for p in raw_pages
        ]

        old_count = await get_collection("chunks").count_documents({"document_id": doc_id})
        total_old += old_count

        records = build_records(pages, filename)
        print(f"  {filename}: {old_count} old -> {len(records)} new chunks ({len(pages)} pages)")

        if not records:
            print(f"    WARNING: no chunks produced, keeping old data")
            continue

        # Delete old chunks
        await get_collection("chunks").delete_many({"document_id": doc_id})

        # Embed new chunks
        texts = [r["text"] for r in records]
        embeddings = await embed_texts_async(texts)

        # Store new chunks
        chunk_docs = []
        import uuid
        languages_seen = set()
        max_page = 0
        any_ocr = False

        for rec, emb in zip(records, embeddings):
            meta = rec["metadata"]
            chunk_docs.append({
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
            })
            if meta["ocr_used"]:
                any_ocr = True
            languages_seen.add(meta["language"])
            max_page = max(max_page, meta["page"])

        if chunk_docs:
            await get_collection("chunks").insert_many(chunk_docs)

        language = "+".join(sorted(languages_seen)) if languages_seen else "unknown"
        await get_collection("documents").update_one(
            {"id": doc_id},
            {"$set": {
                "total_pages": max_page,
                "total_chunks": len(records),
                "ocr_used": any_ocr,
                "language": language,
                "updated_at": datetime.now(timezone.utc),
            }},
        )

        total_new += len(records)

    print(f"\n=== DONE: {total_old} old chunks -> {total_new} new chunks ===")
    print("Restart the server to rebuild the FAISS index.")


if __name__ == "__main__":
    asyncio.run(reprocess())
