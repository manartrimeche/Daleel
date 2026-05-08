import asyncio

import faiss
import numpy as np

from app.database import mongo_db


async def build_sample_faiss_index():
    vectors = []
    cursor = mongo_db["chunks"].find({}, {"embedding": 1}).limit(10)
    async for doc in cursor:
        emb = doc.get("embedding")
        if emb:
            vectors.append(np.array(emb, dtype="float32"))

    print("Vecteurs charges:", len(vectors))
    if vectors:
        print("Dimension:", vectors[0].shape[0])
        matrix = np.vstack(vectors).astype("float32")
        faiss.normalize_L2(matrix)
        index = faiss.IndexHNSWFlat(vectors[0].shape[0], 32)
        index.add(matrix)
        print("Index OK, ntotal:", index.ntotal)


def main():
    asyncio.run(build_sample_faiss_index())


if __name__ == "__main__":
    main()
