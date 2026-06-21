"""Apply all index changes declared in app/database.py to the live MongoDB."""

import asyncio
import logging

from app.database import init_db, mongo_client


async def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
    await init_db()
    mongo_client.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
