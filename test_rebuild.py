import asyncio
import os
os.environ['FAISS_SKIP_DIM_VALIDATION'] = 'true'
from app.services.faiss_index import faiss_manager
import logging
logging.basicConfig(level=logging.DEBUG)

async def test():
    print('Debut rebuild...')
    await faiss_manager.rebuild()
    print('Fin rebuild')
    print('is_ready:', faiss_manager.is_ready)
    print('ntotal:', faiss_manager.size)

asyncio.run(test())
