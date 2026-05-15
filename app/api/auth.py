"""
Authentication dependencies for FastAPI routes.

Three layers:
  1. get_current_user     — decode JWT, return user dict
  2. require_role(...)    — check user role against allowed roles
  3. require_org_access   — ensure user belongs to the target organization

Legacy API-key auth is kept for backward compatibility with existing
non-authenticated endpoints during migration.
"""

from __future__ import annotations

import hmac
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.services import auth_service

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


# ── JWT-based auth ──

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = auth_service.decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    user = await auth_service.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated",
        )
    return user


def require_role(*allowed_roles: str):
    async def _check(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user['role']}' not authorized. Required: {', '.join(allowed_roles)}",
            )
        return user
    return _check


async def require_org_access(
    org_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    if user["role"] == "super_admin":
        return user
    if user.get("organization_id") != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you don't belong to this organization",
        )
    return user


def get_user_org_id(user: dict = Depends(get_current_user)) -> Optional[str]:
    return user.get("organization_id")


# ── Legacy API-key auth (backward compat) ──

async def require_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str | None:
    settings = get_settings()
    expected = settings.api_key
    if not expected:
        return None
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
    settings = get_settings()
    expected = settings.admin_api_key or settings.api_key
    if not expected:
        return None
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
