"""
FAISS index manager — in-memory vector index synced from MongoDB chunks.

The index is built once at startup (or on first query) and incrementally
updated on document ingest / deletion.  Falls back to brute-force Python
cosine similarity if FAISS is unavailable.

Usage:
    from app.services.faiss_index import faiss_manager
    await faiss_manager.ensure_ready()
    results = await faiss_manager.search(query_vec, top_k, filters)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

from app.database import get_collection

logger = logging.getLogger(__name__)

HNSW_M = int(os.getenv("FAISS_HNSW_M", "32"))
HNSW_EF_CONSTRUCTION = int(os.getenv("FAISS_HNSW_EF_CONSTRUCTION", "200"))
HNSW_EF_SEARCH = int(os.getenv("FAISS_HNSW_EF_SEARCH", "64"))
FAISS_SKIP_DIM_VALIDATION = (
    os.getenv("FAISS_SKIP_DIM_VALIDATION", "false").lower() == "true"
)

# Try to import FAISS; gracefully degrade if absent, disabled, or incompatible.
_CONFIGURED_VECTOR_BACKEND = os.getenv("DALEEL_VECTOR_SEARCH_BACKEND", "faiss").lower()
if _CONFIGURED_VECTOR_BACKEND != "faiss":
    faiss = None  # type: ignore[assignment]
    FAISS_AVAILABLE = False
    logger.info("FAISS disabled by configuration - vector search uses Python cosine")
else:
    try:
        import faiss  # type: ignore[import-untyped]

        FAISS_AVAILABLE = True
    except Exception as exc:
        faiss = None  # type: ignore[assignment]
        FAISS_AVAILABLE = False
        logger.warning(
            "FAISS unavailable (%s) - vector search falls back to Python cosine",
            exc.__class__.__name__,
        )

FAISS_READY = True



@dataclass
class _ChunkMeta:
    """Lightweight metadata kept alongside the FAISS vector."""

    chunk_id: str
    document_id: str
    language: Optional[str]
    page_number: Optional[int]
    section: Optional[str]
    chunk_index: Optional[int]
    text: str


class FaissIndexManager:
    """Singleton managing a FAISS HNSW index backed by MongoDB chunks."""

    def __init__(self) -> None:
        self._index: "faiss.Index | None" = None
        self._meta: list[_ChunkMeta] = []
        self._dim: int = 0
        self._ready: bool = False
        self._building: bool = False
        self._chunk_count: int = 0
        self._blocked_reason: str | None = None

    # ── public API ──────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._ready and self._index is not None

    @property
    def blocked_reason(self) -> str | None:
        return self._blocked_reason

    @property
    def size(self) -> int:
        return self._chunk_count

    async def ensure_ready(self) -> None:
        """Build the index if not yet built."""
        if self._ready or self._building:
            return
        await self.rebuild()

    async def rebuild(self) -> None:
        """(Re)build the full FAISS index from MongoDB chunks."""
        if not FAISS_AVAILABLE:
            logger.info("FAISS unavailable — skipping index build")
            return
        if self._building:
            return

        self._building = True
        t0 = time.perf_counter()
        try:
            if FAISS_SKIP_DIM_VALIDATION:
                logger.warning(
                    "Dimension validation skipped (FAISS_SKIP_DIM_VALIDATION=true) — "
                    "call /admin/reindex to fix embedding dimensions"
                )
            else:
                ok, stored_dim, current_dim = await self._validate_embedding_dimensions()
                if not ok:
                    logger.error(
                        "Dimension mismatch: stored=%sd current=%sd. Re-embedding required.",
                        stored_dim,
                        current_dim,
                    )
                    self._mark_unavailable("dimension_mismatch")
                    return

            cursor = get_collection("chunks").find(
                {"embedding": {"$ne": None}},
                {
                    "id": 1,
                    "document_id": 1,
                    "language": 1,
                    "page_number": 1,
                    "section": 1,
                    "chunk_index": 1,
                    "text": 1,
                    "embedding": 1,
                },
            )

            vectors: list[np.ndarray] = []
            meta: list[_ChunkMeta] = []
            expected_dim: int | None = None

            async for doc in cursor:
                emb = doc.get("embedding")
                if not emb:
                    continue
                vec = np.array(emb, dtype=np.float32)
                if vec.ndim != 1 or vec.shape[0] == 0:
                    continue
                if len(vectors) == 0:
                    expected_dim = vec.shape[0]
                elif expected_dim is not None and vec.shape[0] != expected_dim:
                    continue

                vectors.append(vec)
                meta.append(
                    _ChunkMeta(
                        chunk_id=doc.get("id", ""),
                        document_id=doc.get("document_id", ""),
                        language=doc.get("language"),
                        page_number=doc.get("page_number"),
                        section=doc.get("section"),
                        chunk_index=doc.get("chunk_index"),
                        text=doc.get("text", ""),
                    )
                )

            if not vectors:
                logger.info("No embeddings found — FAISS index is empty")
                self._index = None
                self._meta = []
                self._dim = 0
                self._chunk_count = 0
                self._mark_ready()
                return

            # HNSW uses L2 distance; normalize vectors to preserve cosine geometry.
            matrix = np.vstack(vectors).astype(np.float32)
            faiss.normalize_L2(matrix)

            dim = matrix.shape[1]
            index = faiss.IndexHNSWFlat(dim, HNSW_M)
            index.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
            index.hnsw.efSearch = HNSW_EF_SEARCH
            index.add(matrix)

            self._index = index
            self._meta = meta
            self._dim = dim
            self._chunk_count = index.ntotal
            self._mark_ready()

            elapsed = time.perf_counter() - t0
            logger.info(
                "FAISS HNSW index built: %d vectors × %d dims in %.2fs (M=%d, efC=%d, efS=%d)",
                self._chunk_count,
                dim,
                elapsed,
                HNSW_M,
                HNSW_EF_CONSTRUCTION,
                HNSW_EF_SEARCH,
            )

            # Persist build metadata for consistency checks
            try:
                from app.config import get_settings
                from app.services.index_consistency_service import save_index_metadata

                settings = get_settings()
                await save_index_metadata(
                    model_name=settings.embedding_model,
                    dimension=dim,
                    vector_count=self._chunk_count,
                )
            except Exception:
                logger.debug("Could not save index metadata (non-fatal)", exc_info=True)
        except Exception:
            logger.exception("Failed to build FAISS index")
            self._mark_unavailable("build_failed")
        finally:
            self._building = False

    def mark_unavailable(self, reason: str) -> None:
        self._mark_unavailable(reason)

    async def _validate_embedding_dimensions(self) -> tuple[bool, int | None, int]:
        from app.services.embedding_service import get_primary_embedding_dimension

        # Model initialization can be slow; keep background rebuilds from blocking
        # the event loop while resolving the active embedding dimension.
        current_dim = int(await asyncio.to_thread(get_primary_embedding_dimension))
        dims: set[int] = set()

        cursor = get_collection("chunks").find(
            {"embedding.0": {"$exists": True}},
            {"embedding": 1},
        ).limit(500)

        async for doc in cursor:
            emb = doc.get("embedding") or []
            if not emb:
                continue
            dims.add(len(emb))
            if len(dims) > 1:
                break

        if not dims:
            return True, None, current_dim

        if dims != {current_dim}:
            mismatch_dims = [d for d in dims if d != current_dim]
            stored_dim = mismatch_dims[0] if mismatch_dims else next(iter(dims))
            return False, stored_dim, current_dim

        return True, current_dim, current_dim

    def _mark_unavailable(self, reason: str) -> None:
        global FAISS_READY
        FAISS_READY = False
        self._blocked_reason = reason
        self._index = None
        self._meta = []
        self._dim = 0
        self._chunk_count = 0
        self._ready = False

    def _mark_ready(self) -> None:
        global FAISS_READY
        FAISS_READY = True
        self._blocked_reason = None
        self._ready = True

    async def add_vectors(
        self, chunk_docs: list[dict]
    ) -> int:
        """Incrementally add new chunk documents (with 'embedding' key) to the live index."""
        if not FAISS_AVAILABLE or self._index is None:
            # Will be picked up on next rebuild
            return 0

        vectors: list[np.ndarray] = []
        new_meta: list[_ChunkMeta] = []

        for doc in chunk_docs:
            emb = doc.get("embedding")
            if not emb:
                continue
            vec = np.array(emb, dtype=np.float32)
            if vec.ndim != 1 or vec.shape[0] != self._dim:
                continue
            vectors.append(vec)
            new_meta.append(
                _ChunkMeta(
                    chunk_id=doc.get("id", ""),
                    document_id=doc.get("document_id", ""),
                    language=doc.get("language"),
                    page_number=doc.get("page_number"),
                    section=doc.get("section"),
                    chunk_index=doc.get("chunk_index"),
                    text=doc.get("text", ""),
                )
            )

        if not vectors:
            return 0

        matrix = np.vstack(vectors).astype(np.float32)
        faiss.normalize_L2(matrix)
        self._index.add(matrix)
        self._meta.extend(new_meta)
        self._chunk_count = self._index.ntotal
        logger.debug("FAISS: added %d vectors (total=%d)", len(vectors), self._chunk_count)
        return len(vectors)

    async def remove_by_document_id(self, document_id: str) -> None:
        """HNSW does not support selective remove_ids — trigger a full rebuild."""
        if not FAISS_AVAILABLE:
            return
        await self.rebuild()

    async def search(
        self,
        query_vec: list[float],
        top_k: int = 10,
        language_filter: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> list[dict]:
        """Search the FAISS index and return top-k results with metadata."""
        if not self.is_ready or self._index is None or self._chunk_count == 0:
            return []

        q = np.array(query_vec, dtype=np.float32).reshape(1, -1)
        if q.shape[1] != self._dim:
            logger.warning(
                "Query dim %d ≠ index dim %d — cannot search",
                q.shape[1],
                self._dim,
            )
            return []

        faiss.normalize_L2(q)

        # Retrieve more candidates when filtering will discard some
        fetch_k = min(top_k * 4, self._chunk_count)
        distances, indices = self._index.search(q, fetch_k)

        # Resolve filenames in bulk
        doc_ids_needed = set()
        for idx in indices[0]:
            if 0 <= idx < len(self._meta):
                doc_ids_needed.add(self._meta[idx].document_id)
        filename_map: dict[str, str | None] = {}
        if doc_ids_needed:
            async for doc in get_collection("documents").find(
                {"id": {"$in": list(doc_ids_needed)}}, {"id": 1, "filename": 1}
            ):
                filename_map[doc["id"]] = doc.get("filename")

        # Parse language filter
        lang_values = _parse_lang_filter(language_filter)

        results: list[dict] = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._meta):
                continue
            m = self._meta[idx]

            # Apply filters
            if document_id and m.document_id != document_id:
                continue
            if lang_values and m.language not in lang_values:
                continue

            # For normalized vectors: squared L2 distance ~= 2 - 2*cosine.
            # Convert back to a cosine-like similarity score for compatibility.
            similarity = 1.0 - (float(distance) / 2.0)
            similarity = max(-1.0, min(1.0, similarity))

            results.append(
                {
                    "chunk_id": m.chunk_id,
                    "document_id": m.document_id,
                    "filename": filename_map.get(m.document_id),
                    "text": m.text,
                    "page_number": m.page_number,
                    "section": m.section,
                    "language": m.language,
                    "chunk_index": m.chunk_index,
                    "score": similarity,
                }
            )
            if len(results) >= top_k:
                break

        return results


def _parse_lang_filter(language_filter: Optional[str]) -> list[str]:
    if not language_filter:
        return []
    parts = [p.strip() for p in str(language_filter).split("+") if p.strip()]
    return list(dict.fromkeys(parts))


# Module-level singleton
faiss_manager = FaissIndexManager()
