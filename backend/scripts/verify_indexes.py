"""Print all indexes on every declared collection — to verify migration."""

import asyncio

from app.database import _COLLECTION_INDEXES, mongo_client, mongo_db


async def main():
    for name in sorted(_COLLECTION_INDEXES):
        info = await mongo_db[name].index_information()
        print(f"\n== {name} ({len(info)} index(es)) ==")
        for iname, idata in info.items():
            key = idata.get("key")
            extras = []
            if idata.get("unique"):
                extras.append("UNIQUE")
            if "expireAfterSeconds" in idata:
                extras.append(f"TTL={idata['expireAfterSeconds']}s")
            if "partialFilterExpression" in idata:
                extras.append("partial")
            extra_str = (" [" + ",".join(extras) + "]") if extras else ""
            print(f"  - {iname}: {key}{extra_str}")
    mongo_client.close()


if __name__ == "__main__":
    asyncio.run(main())
