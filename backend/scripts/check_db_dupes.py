"""
Pre-migration check: scan for duplicates that would block the new unique indexes
declared in app/database.py (lois.code, articles.(loi_id, article_key),
article_versions.(article_id, version_number)).

Usage:
    python -m scripts.check_db_dupes
"""

import asyncio

from app.database import mongo_client, mongo_db


CHECKS = [
    ("lois", [("code", 1)]),
    ("articles", [("loi_id", 1), ("article_key", 1)]),
    ("article_versions", [("article_id", 1), ("version_number", -1)]),
    ("documents", [("organization_id", 1), ("created_at", -1)]),  # informational
]


async def find_duplicates(collection_name, fields):
    coll = mongo_db[collection_name]
    group_id = {f: f"${f}" for f, _ in fields}
    cursor = coll.aggregate(
        [
            {"$group": {"_id": group_id, "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$limit": 20},
        ]
    )
    return [doc async for doc in cursor]


async def main():
    try:
        await mongo_db.command("ping")
    except Exception as exc:
        print(f"[ERROR] Cannot reach MongoDB: {exc}")
        return 1

    blocking = 0
    for name, fields in CHECKS:
        total = await mongo_db[name].count_documents({})
        dupes = await find_duplicates(name, fields)
        key = " + ".join(f for f, _ in fields)
        if dupes:
            print(f"[DUPES] {name} ({total} docs) on ({key}) — {len(dupes)} group(s):")
            for d in dupes:
                print(f"   {d['_id']}  ×{d['count']}")
            blocking += len(dupes)
        else:
            print(f"[OK]    {name} ({total} docs) on ({key}) — no duplicates")

    mongo_client.close()
    if blocking:
        print(f"\n=> {blocking} duplicate group(s) found. Resolve before unique-index migration.")
        return 2
    print("\n=> Safe to enforce unique indexes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
