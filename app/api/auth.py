"""
Authentication dependencies for FastAPI routes.

Two levels:
  • require_api_key  — for mutating endpoints (upload, delete, POST …)
  • require_admin    — for /admin/* endpoints (stats, vector-index, clear …)

Auth is **disabled** when the corresponding key is empty in Settings
(i.e. no DALEEL_API_KEY env var set), so dev mode works without config.
"""

from __future__ import annotations

import hmac
import logging

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

logger = logging.getLogger(__name__)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


async def require_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str | None:
    """Validate X-API-Key header for mutating endpoints.

    Returns the validated key, or None if auth is disabled.
    Raises 401 if auth is enabled and key is missing/wrong.
    """
    settings = get_settings()
    expected = settings.api_key
    if not expected:
        return None  # auth disabled
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    if not _constant_time_compare(api_key, expected):
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return api_key


async def require_admin(
    api_key: str | None = Security(_api_key_header),
) -> str | None:
    """Validate X-API-Key header for admin endpoints.

    Uses DALEEL_ADMIN_API_KEY if set, otherwise falls back to DALEEL_API_KEY.
    """
    settings = get_settings()
    expected = settings.admin_api_key or settings.api_key
    if not expected:
        return None  # auth disabled
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header (admin)",
        )
    if not _constant_time_compare(api_key, expected):
        logger.warning("Invalid admin API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API key",
        )
    return api_key
