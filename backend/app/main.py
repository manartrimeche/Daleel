"""
FastAPI application entry point.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from contextlib import suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.api.auth_router import router as auth_router
from app.api.router import router
from app.api.case_router import router as case_router
from app.api.case_conversation_router import router as case_conversation_router
from app.api.case_orchestrator_router import router as case_orchestrator_router
from app.api.compliance_router import router as compliance_router
from app.api.voice_router import router as voice_router
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


def _find_interface_dir() -> Path:
    current_file = Path(__file__).resolve()
    candidates = [
        current_file.parents[2] / "interface-daleel",
        current_file.parents[1] / "interface-daleel",
        current_file.parent / "static",
    ]
    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate
    return candidates[0]


STATIC_DIR = _find_interface_dir()
ASSETS_DIR = STATIC_DIR / "assets"
INDEX_FILE = STATIC_DIR / "index.html"


async def _build_faiss_index() -> None:
    logger.info("Building FAISS vector index …")
    await faiss_manager.rebuild()
    if faiss_manager.blocked_reason is None:
        logger.info("FAISS index ready (%d vectors)", faiss_manager.size)
    else:
        logger.error("FAISS index unavailable — re-embedding required")

    # Lightweight safety check: does the index match the configured model?
    try:
        from app.services.index_consistency_service import log_consistency_warning_if_needed
        await log_consistency_warning_if_needed()
    except Exception:
        logger.warning("Index consistency check failed (non-fatal)", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database …")
    await init_db()
    logger.info("Database ready")
    settings = get_settings()
    faiss_task: asyncio.Task | None = None
    should_build_faiss = FAISS_AVAILABLE and settings.faiss_build_on_startup

    # Cleanup orphaned upload files on startup
    try:
        from app.services.document_service import cleanup_orphaned_uploads
        from app.database import mongo_db
        removed = await cleanup_orphaned_uploads(mongo_db)
        if removed:
            logger.info("Startup cleanup: removed %d orphaned upload(s)", removed)
    except Exception:
        logger.warning("Upload cleanup failed (non-fatal)", exc_info=True)

    if should_build_faiss:
        if settings.faiss_build_in_background:
            logger.info("Scheduling FAISS vector index build in background …")
            faiss_task = asyncio.create_task(_build_faiss_index())
            app.state.faiss_build_task = faiss_task
        else:
            await _build_faiss_index()

    yield
    if faiss_task and not faiss_task.done():
        faiss_task.cancel()
        with suppress(asyncio.CancelledError):
            await faiss_task
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


@app.get("/api/v1/health", tags=["meta"], summary="Health check")
async def health_check():
    """Vérifie que le serveur et MongoDB sont opérationnels."""
    from app.database import mongo_db
    try:
        await mongo_db.command("ping")
        db_ok = True
    except Exception:
        db_ok = False
    status_val = "healthy" if db_ok else "degraded"
    faiss_ok = FAISS_READY and faiss_manager.size > 0 if FAISS_AVAILABLE else False
    return {
        "status": status_val,
        "database": "connected" if db_ok else "disconnected",
        "faiss_index": faiss_manager.size if faiss_ok else 0,
    }


app.include_router(auth_router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1")
app.include_router(case_conversation_router, prefix="/api/v1")
app.include_router(case_router, prefix="/api/v1")
app.include_router(case_orchestrator_router, prefix="/api/v1")
app.include_router(compliance_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")

# ── Serve chatbot frontend ──
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


def _serve_spa_index(*, no_cache: bool = False) -> FileResponse:
    headers = None
    if no_cache:
        headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    return FileResponse(INDEX_FILE, headers=headers)


def _serve_existing_frontend_file(full_path: str) -> FileResponse | None:
    try:
        target = (STATIC_DIR / full_path).resolve()
        target.relative_to(STATIC_DIR.resolve())
    except ValueError:
        return None
    if target.is_file():
        return FileResponse(target)
    return None


@app.get("/")
async def serve_frontend():
    """Serve the React app at the root URL."""
    return _serve_spa_index()


@app.get("/login")
async def serve_login():
    """Serve the React auth route."""
    return _serve_spa_index()


@app.get("/auth")
async def serve_auth():
    """Serve the legacy React auth route."""
    return _serve_spa_index()


@app.get("/register")
async def serve_register():
    """Serve the React register route."""
    return _serve_spa_index()


@app.get("/invite")
async def serve_invite():
    """Serve the React invitation route."""
    return _serve_spa_index()


@app.get("/admin")
async def serve_admin():
    """Serve the React admin route."""
    return _serve_spa_index(no_cache=True)


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend_route(full_path: str):
    """Serve built frontend files and let React handle browser routes."""
    api_or_internal = (
        "api/",
        "assets/",
        "static/",
        "docs",
        "redoc",
        "openapi.json",
    )
    if full_path.startswith(api_or_internal):
        raise HTTPException(status_code=404, detail="Not found")

    existing_file = _serve_existing_frontend_file(full_path)
    if existing_file is not None:
        return existing_file

    return _serve_spa_index(no_cache=full_path.startswith("admin"))
