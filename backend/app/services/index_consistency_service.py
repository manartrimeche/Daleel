"""
Index–model consistency checker.

Compares the embedding model used to build the active FAISS index with the
model currently configured in settings.  Mismatches are logged as warnings
so administrators know to rebuild the index — the app is never blocked.

Metadata about the last index build is persisted in the MongoDB collection
``index_metadata`` (a single document with ``_id = "faiss_latest"``).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.database import mongo_db

logger = logging.getLogger(__name__)

_INDEX_META_COLLECTION = "index_metadata"
_META_DOC_ID = "faiss_latest"


# ── Result dataclass ─────────────────────────────────────────────────────────


@dataclass
class ConsistencyResult:
    """Outcome of a model-vs-index consistency check."""

    ok: bool
    current_model: str
    current_dimension: int
    index_model: Optional[str]
    index_dimension: Optional[int]
    index_built_at: Optional[str]
    reason: str

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "current_model": self.current_model,
            "current_dimension": self.current_dimension,
            "index_model": self.index_model,
            "index_dimension": self.index_dimension,
            "index_built_at": self.index_built_at,
            "reason": self.reason,
        }


# ── Fingerprint helper ───────────────────────────────────────────────────────


def _model_fingerprint(model_name: str, dimension: int) -> str:
    """Deterministic hash of model name + dimension (lightweight identity)."""
    raw = f"{model_name}:{dimension}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Persist / read index metadata ────────────────────────────────────────────


async def save_index_metadata(
    *,
    model_name: str,
    dimension: int,
    vector_count: int,
) -> None:
    """Write (upsert) the metadata record after a successful FAISS build."""
    coll = mongo_db[_INDEX_META_COLLECTION]
    fp = _model_fingerprint(model_name, dimension)
    now = datetime.now(timezone.utc)
    await coll.update_one(
        {"_id": _META_DOC_ID},
        {
            "$set": {
                "embedding_model": model_name,
                "embedding_dimension": dimension,
                "model_fingerprint": fp,
                "vector_count": vector_count,
                "built_at": now,
                "updated_at": now,
            }
        },
        upsert=True,
    )
    logger.debug(
        "Index metadata saved: model=%s dim=%d fp=%s vectors=%d",
        model_name,
        dimension,
        fp,
        vector_count,
    )


async def load_index_metadata() -> dict | None:
    """Read the stored metadata document, or None if never built."""
    coll = mongo_db[_INDEX_META_COLLECTION]
    doc = await coll.find_one({"_id": _META_DOC_ID})
    return doc


# ── Core consistency check ───────────────────────────────────────────────────


async def check_index_model_consistency() -> ConsistencyResult:
    """
    Compare the configured embedding model with the metadata recorded at
    the last FAISS index build.

    Returns a :class:`ConsistencyResult` — the caller decides what to do
    with it (log, expose via API, etc.).
    """
    settings = get_settings()
    current_model = settings.embedding_model
    current_dim = settings.embedding_dimension

    meta = await load_index_metadata()

    if meta is None:
        return ConsistencyResult(
            ok=True,
            current_model=current_model,
            current_dimension=current_dim,
            index_model=None,
            index_dimension=None,
            index_built_at=None,
            reason="No index metadata found — index has not been built yet.",
        )

    index_model = meta.get("embedding_model", "unknown")
    index_dim = meta.get("embedding_dimension")
    built_at = meta.get("built_at")
    built_at_str = built_at.isoformat() if isinstance(built_at, datetime) else str(built_at) if built_at else None

    # Compare fingerprints (model name + dimension)
    current_fp = _model_fingerprint(current_model, current_dim)
    index_fp = meta.get("model_fingerprint", "")

    if current_fp == index_fp:
        return ConsistencyResult(
            ok=True,
            current_model=current_model,
            current_dimension=current_dim,
            index_model=index_model,
            index_dimension=index_dim,
            index_built_at=built_at_str,
            reason="Configured model matches the index.",
        )

    # Build a human-readable mismatch reason
    reasons: list[str] = []
    if current_model != index_model:
        reasons.append(f"model name differs (config='{current_model}', index='{index_model}')")
    if index_dim is not None and current_dim != index_dim:
        reasons.append(f"embedding dimension differs (config={current_dim}, index={index_dim})")

    reason_text = "Index–model MISMATCH: " + "; ".join(reasons) + "."

    return ConsistencyResult(
        ok=False,
        current_model=current_model,
        current_dimension=current_dim,
        index_model=index_model,
        index_dimension=index_dim,
        index_built_at=built_at_str,
        reason=reason_text,
    )


async def log_consistency_warning_if_needed() -> ConsistencyResult:
    """
    Run the consistency check and log a WARNING when there is a mismatch.

    Designed to be called at startup — never raises.
    """
    try:
        result = await check_index_model_consistency()
        if not result.ok:
            logger.warning(
                "⚠️  FAISS INDEX / MODEL MISMATCH ⚠️  %s  "
                "The index was built with '%s' (%s-dim) but the configured model is '%s' (%s-dim). "
                "Search results may be incorrect. "
                "Call POST /api/v1/admin/rebuild-faiss-index to rebuild with the current model.",
                result.reason,
                result.index_model,
                result.index_dimension,
                result.current_model,
                result.current_dimension,
            )
        else:
            logger.info("Index consistency check passed: %s", result.reason)
        return result
    except Exception:
        logger.exception("Index consistency check failed (non-fatal)")
        return ConsistencyResult(
            ok=True,  # assume OK to avoid blocking startup
            current_model=get_settings().embedding_model,
            current_dimension=get_settings().embedding_dimension,
            index_model=None,
            index_dimension=None,
            index_built_at=None,
            reason="Consistency check raised an exception — skipped.",
        )
