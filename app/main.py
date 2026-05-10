"""
FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import router
from app.api.case_router import router as case_router
from app.api.case_conversation_router import router as case_conversation_router
from app.api.case_orchestrator_router import router as case_orchestrator_router
from app.api.compliance_router import router as compliance_router
from app.api.tenant import TenantMiddleware
from app.config import get_settings
from app.database import init_db, close_db
from app.limiter import limiter
from app.services.faiss_index import FAISS_AVAILABLE, FAISS_READY, faiss_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database …")
    await init_db()
    logger.info("Database ready")
    if FAISS_AVAILABLE:
        logger.info("Building FAISS vector index …")
        await faiss_manager.rebuild()
        if FAISS_READY:
            logger.info("FAISS index ready (%d vectors)", faiss_manager.size)
        else:
            logger.error("FAISS index unavailable — re-embedding required")

        # Lightweight safety check: does the index match the configured model?
        try:
            from app.services.index_consistency_service import log_consistency_warning_if_needed
            await log_consistency_warning_if_needed()
        except Exception:
            logger.warning("Index consistency check failed (non-fatal)", exc_info=True)
    yield
    logger.info("Shutting down")
    await close_db()


app = FastAPI(
    title="Daleel — Legal Document Search API",
    description="Upload Tunisian legal documents, chunk them, and search with semantic similarity.",
    version="1.0.0",
    lifespan=lifespan,
)


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    retry_after = None
    if exc.headers:
        retry_after = exc.headers.get("Retry-After")

    if retry_after:
        message = f"Rate limit exceeded. Retry after {retry_after} seconds."
    else:
        message = "Rate limit exceeded. Please retry later."

    payload = {"detail": message}
    if retry_after:
        payload["retry_after"] = retry_after

    return JSONResponse(
        status_code=429,
        content=payload,
        headers=exc.headers,
    )

_settings = get_settings()
_cors_origins = [o.strip() for o in _settings.cors_origins.split(",") if o.strip()]

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "X-Org-Id", "Authorization"],
)
app.add_middleware(TenantMiddleware)


@app.get("/api/v1", tags=["meta"], summary="API v1")
@app.get("/api/v1/", tags=["meta"], include_in_schema=False)
async def api_v1_entrypoint():
    """Métadonnées sur la racine de l’API (avec ou sans slash final)."""
    return {
        "name": app.title,
        "version": app.version,
        "documentation": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "note": "Routes concrètes : POST /api/v1/ask, GET /api/v1/documents, …",
    }


app.include_router(router, prefix="/api/v1")
app.include_router(case_conversation_router, prefix="/api/v1")
app.include_router(case_router, prefix="/api/v1")
app.include_router(case_orchestrator_router, prefix="/api/v1")
app.include_router(compliance_router, prefix="/api/v1")

# ── Serve chatbot frontend ──
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the chatbot UI at the root URL."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin")
async def serve_admin():
    """Serve the admin panel UI."""
    return FileResponse(STATIC_DIR / "admin.html")
