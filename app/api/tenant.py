"""
Multi-tenant middleware and dependency.

When DALEEL_MULTI_TENANT_ENABLED=true, every request must include an
X-Org-Id header. The org_id is injected into the request state and
used by services to scope all database queries.

When disabled (default), org_id is None and all data is shared.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import get_settings

logger = logging.getLogger(__name__)

_ORG_HEADER = "X-Org-Id"


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Inject org_id from header into request.state for downstream use.

    Skips enforcement for docs, openapi, and static routes.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings = get_settings()
        if not settings.multi_tenant_enabled:
            request.state.org_id = None
            return await call_next(request)

        # Skip for docs / static
        path = request.url.path
        if path in ("/docs", "/redoc", "/openapi.json", "/", "/admin") or path.startswith("/static"):
            request.state.org_id = None
            return await call_next(request)

        org_id = request.headers.get(_ORG_HEADER)
        if not org_id or not org_id.strip():
            return Response(
                content='{"detail":"Missing X-Org-Id header"}',
                status_code=status.HTTP_400_BAD_REQUEST,
                media_type="application/json",
            )

        request.state.org_id = org_id.strip()
        return await call_next(request)


def get_org_id(request: Request) -> Optional[str]:
    """FastAPI dependency: returns the current tenant org_id (or None)."""
    return getattr(request.state, "org_id", None)
