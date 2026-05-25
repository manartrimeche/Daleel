"""Full data quality audit for Daleel RAG pipeline."""
import asyncio
import re
import sys
import os
import statistics
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("ENVIRONMENT", "development")

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings


async def full_audit():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    # 1. Overview
    total_docs = await db["documents"].count_documents({})
    total_chunks = await db["chunks"].count_documents({})
    total_sources = await db["document_sources"].count_documents({})
    total_raw = await db["document_raw_pages"].count_documents({})
    total_exigences = await db["exigences"].count_documents({})

    print("=" * 65)
    print("            AUDIT COMPLET DES DONNEES DALEEL")
    print("=" * 65)
    print(f"\n  Documents:     {total_docs}")
    print(f"  Sources:       {total_sources}")
    print(f"  Raw pages:     {total_raw}")
    print(f"  Chunks:        {total_chunks}")
    print(f"  Exigences:     {total_exigences}")

    # 2. Per-document breakdown
    print("\n" + "=" * 65)
    print("  DETAILS PAR DOCUMENT")
    print("=" * 65)

    docs_list = await db["documents"].find(
        {}, {"id": 1, "filename": 1, "language": 1, "total_pages": 1,
             "total_chunks": 1, "ocr_used": 1, "status": 1, "_id": 0}
    ).to_list(length=10_000)

    for d in docs_list:
        doc_id = d["id"]
        fn = d.get("filename", "?")
        chunk_count = await db["chunks"].count_documents({"document_id": doc_id})
        raw_count = await db["document_raw_pages"].count_documents({"document_id": doc_id})
        exig_count = await db["exigences"].count_documents({"document_id": doc_id})
        print(f"\n  [{fn}]")
        print(f"    Status: {d.get('status')} | Lang: {d.get('language')} | OCR: {d.get('ocr_used')}")
        print(f"    Pages: {d.get('total_pages')} | Raw pages stored: {raw_count}")
        print(f"    Chunks: {chunk_count} (doc record says {d.get('total_chunks')}) | Exigences: {exig_count}")

    # 3. Chunk quality
    print("\n" + "=" * 65)
    print("  QUALITE DES CHUNKS")
    print("=" * 65)

    lengths = []
    lang_counts = Counter()
    issues = {
        "page_num_prefix": 0,
        "page_num_standalone": 0,
        "publisher_lines": 0,
        "cover_page_content": 0,
        "very_short_lt50": 0,
        "short_lt100": 0,
        "long_gt3000": 0,
        "low_alnum_ratio_lt30": 0,
        "broken_arabic_ocr": 0,
        "duplicates": 0,
        "empty_or_whitespace": 0,
        "repeated_header_only": 0,
        "sommaire_index": 0,
        "imprimerie_officielle": 0,
    }
    dup_texts = {}
    issue_samples = defaultdict(list)

    all_chunks = await db["chunks"].find(
        {}, {"text": 1, "language": 1, "page_number": 1, "document_id": 1, "_id": 0}
    ).to_list(length=200_000)

    for c in all_chunks:
        text = c.get("text", "")
        stripped = text.strip()
        lang = c.get("language", "?")
        page = c.get("page_number", "?")
        doc_id = (c.get("document_id") or "?")[:8]
        tag = f"doc={doc_id} p={page}"

        lengths.append(len(stripped))
        lang_counts[lang] += 1

        if not stripped:
            issues["empty_or_whitespace"] += 1
            continue

        # Page number prefix
        if re.match(r"^\d{1,3}\s*\n", text):
            issues["page_num_prefix"] += 1
            if len(issue_samples["page_num_prefix"]) < 2:
                issue_samples["page_num_prefix"].append((tag, stripped[:80]))

        # Standalone page numbers
        if re.match(r"^\s*\d{1,3}\s*$", stripped):
            issues["page_num_standalone"] += 1

        # Publisher
        if re.search(
            r"[Ii]mprimerie\s+[Oo]fficielle|"
            r"[Pp]ublications?\s+de\s+l.?[Ii]mprimerie|"
            r"منشورات\s+المطبعة\s+الرسمية|"
            r"المطبعة\s+الرسمية\s+للجمهورية",
            text,
        ):
            issues["imprimerie_officielle"] += 1
            if len(issue_samples["publisher"]) < 2:
                issue_samples["publisher"].append((tag, stripped[:120]))

        # Repeated header only
        if re.match(
            r"^(?:REPUBLIQUE\s+TUNISIENNE|الجمهورية\s+التونسية)\s*$",
            stripped,
            re.IGNORECASE,
        ):
            issues["repeated_header_only"] += 1

        # Cover page pattern
        if len(stripped) < 500 and re.search(
            r"(?:REPUBLIQUE\s+TUNISIENNE|الجمهورية\s+التونسية)", stripped, re.IGNORECASE
        ):
            words = stripped.split()
            if len(words) < 20:
                issues["cover_page_content"] += 1
                if len(issue_samples["cover_page"]) < 2:
                    issue_samples["cover_page"].append((tag, stripped[:150]))

        # Sommaire/index
        if re.search(r"SOMMAIRE|TABLE\s+DES\s+MATI|فهرس|الفهرس", stripped, re.IGNORECASE):
            issues["sommaire_index"] += 1
            if len(issue_samples["sommaire"]) < 2:
                issue_samples["sommaire"].append((tag, stripped[:150]))
        else:
            lines = stripped.split("\n")
            dotted = sum(1 for ln in lines if re.match(r"^.*\.{3,}\s*\d+\s*$", ln))
            if len(lines) > 3 and dotted / len(lines) > 0.4:
                issues["sommaire_index"] += 1

        # Length issues
        if len(stripped) < 50:
            issues["very_short_lt50"] += 1
            if len(issue_samples["very_short"]) < 3:
                issue_samples["very_short"].append((tag, repr(stripped[:100])))
        elif len(stripped) < 100:
            issues["short_lt100"] += 1
            if len(issue_samples["short"]) < 3:
                issue_samples["short"].append((tag, repr(stripped[:100])))
        if len(stripped) > 3000:
            issues["long_gt3000"] += 1

        # Low alnum ratio
        alnum = sum(1 for ch in stripped if ch.isalnum())
        if len(stripped) > 0 and alnum / len(stripped) < 0.3:
            issues["low_alnum_ratio_lt30"] += 1
            if len(issue_samples["low_alnum"]) < 2:
                issue_samples["low_alnum"].append((tag, repr(stripped[:120])))

        # Broken Arabic OCR
        if lang == "ar":
            single = len(re.findall(r"(?<!\w)\w(?!\w)", stripped))
            words = stripped.split()
            if words and single / max(len(words), 1) > 0.3:
                issues["broken_arabic_ocr"] += 1
                if len(issue_samples["broken_arabic"]) < 2:
                    issue_samples["broken_arabic"].append((tag, stripped[:150]))

        # Duplicates
        norm = re.sub(r"\s+", " ", stripped.lower())
        dup_texts[norm] = dup_texts.get(norm, 0) + 1

    dup_count = sum(v - 1 for v in dup_texts.values() if v > 1)
    issues["duplicates"] = dup_count

    print(f"\n  Langues: {dict(lang_counts)}")

    if lengths:
        print(f"\n  Longueur des chunks:")
        print(f"    Min:     {min(lengths)}")
        print(f"    Max:     {max(lengths)}")
        print(f"    Median:  {statistics.median(lengths):.0f}")
        print(f"    Mean:    {statistics.mean(lengths):.0f}")
        print(f"    Stdev:   {statistics.stdev(lengths):.0f}")

    brackets = [
        (0, 50), (50, 100), (100, 300), (300, 500),
        (500, 1000), (1000, 2000), (2000, 3000), (3000, 99999),
    ]
    print(f"\n  Distribution des longueurs:")
    for lo, hi in brackets:
        count = sum(1 for l in lengths if lo <= l < hi)
        pct = count / len(lengths) * 100 if lengths else 0
        bar = "#" * int(pct / 2)
        label = f"{lo}-{hi}" if hi < 99999 else f"{lo}+"
        print(f"    {label:>10}: {count:>4} ({pct:5.1f}%)  {bar}")

    print(f"\n  Problemes detectes:")
    any_issue = False
    for k, v in issues.items():
        status = "OK" if v == 0 else f"ISSUE ({v})"
        icon = "+" if v == 0 else "!"
        print(f"    [{icon}] {k:.<35} {status}")
        if v > 0:
            any_issue = True

    if issue_samples:
        print(f"\n  Echantillons:")
        for issue_type, samples in issue_samples.items():
            if samples:
                print(f"\n    --- {issue_type} ---")
                for tag, txt in samples:
                    print(f"      {tag}: {txt}")

    # Top duplicates
    top_dups = sorted(
        ((k, v) for k, v in dup_texts.items() if v > 1),
        key=lambda x: -x[1],
    )[:5]
    if top_dups:
        print(f"\n  Top doublons:")
        for txt, count in top_dups:
            print(f"    x{count}: {txt[:80]}")

    # 4. Embeddings
    print("\n" + "=" * 65)
    print("  EMBEDDINGS")
    print("=" * 65)

    missing_emb = await db["chunks"].count_documents({"embedding": None})
    empty_emb = await db["chunks"].count_documents({"embedding": []})

    sample = await db["chunks"].find_one(
        {"embedding": {"$exists": True, "$ne": None, "$not": {"$size": 0}}},
        {"embedding": 1, "_id": 0},
    )
    dim = len(sample["embedding"]) if sample and sample.get("embedding") else 0

    print(f"  Dimension: {dim}")
    print(f"  Missing embeddings: {missing_emb}")
    print(f"  Empty embeddings: {empty_emb}")
    print(f"  Valid embeddings: {total_chunks - missing_emb - empty_emb}")

    # 5. Consistency
    print("\n" + "=" * 65)
    print("  COHERENCE & INTEGRITE")
    print("=" * 65)

    doc_ids = set()
    async for d in db["documents"].find({}, {"id": 1, "_id": 0}):
        doc_ids.add(d["id"])

    orphan_chunks = 0
    chunk_doc_ids = set()
    async for c in db["chunks"].find({}, {"document_id": 1, "_id": 0}):
        did = c.get("document_id")
        chunk_doc_ids.add(did)
        if did not in doc_ids:
            orphan_chunks += 1

    docs_without_chunks = doc_ids - chunk_doc_ids

    # Orphan sources
    orphan_sources = 0
    async for s in db["document_sources"].find({}, {"document_id": 1, "_id": 0}):
        if s.get("document_id") not in doc_ids:
            orphan_sources += 1

    # Orphan exigences
    orphan_exigences = 0
    async for e in db["exigences"].find({}, {"document_id": 1, "_id": 0}):
        if e.get("document_id") not in doc_ids:
            orphan_exigences += 1

    print(f"  Orphan chunks (no parent doc):    {orphan_chunks}")
    print(f"  Orphan sources (no parent doc):   {orphan_sources}")
    print(f"  Orphan exigences (no parent doc): {orphan_exigences}")
    print(f"  Docs without chunks:              {len(docs_without_chunks)}")
    if docs_without_chunks:
        for did in docs_without_chunks:
            print(f"    - {did}")

    # FAISS consistency
    print(f"\n  FAISS index: 2160 vectors expected (from startup log)")

    # Summary
    print("\n" + "=" * 65)
    total_issues = sum(issues.values()) + orphan_chunks + orphan_sources + orphan_exigences
    if total_issues == 0:
        print("  RESULTAT: DONNEES PROPRES - AUCUN PROBLEME DETECTE")
    else:
        print(f"  RESULTAT: {total_issues} PROBLEME(S) DETECTE(S)")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(full_audit())
