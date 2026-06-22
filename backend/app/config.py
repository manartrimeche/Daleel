"""
Application settings — loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


_ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # ── MongoDB ──
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "manar"
    mongodb_max_pool_size: int = 50
    mongodb_min_pool_size: int = 0
    mongodb_server_selection_timeout_ms: int = 30000
    mongodb_connect_timeout_ms: int = 10000
    mongodb_socket_timeout_ms: int = 30000

    # ── Embedding model ──
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    embedding_dimension: int = 768  # matches the model above
    # Used for query vectors when stored chunk embeddings are 384-d (e.g. legacy MiniLM index)
    embedding_model_dim_384: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    # ── LLM provider ──
    # "ollama"  → API native Ollama (/api/chat), pour le dev local.
    # "openai"  → API compatible OpenAI (/chat/completions) : OpenRouter, Groq,
    #             Together, vLLM, etc. Permet d'héberger Daleel sans LLM local.
    # Le pipeline RAG est identique dans les deux cas : seul le transport change.
    llm_provider: str = "ollama"
    # ── LLM (Ollama native API par défaut) ──
    llm_base_url: str = "http://localhost:11434"
    llm_api_key: str = "ollama"  # Ollama doesn't require a real key
    llm_model: str = "qwen2.5:7b"  # Powerful multilingual model for legal RAG

    # ── Chunking defaults ──
    chunk_size: int = 1500
    chunk_overlap: int = 200
    min_chunk_len: int = 60

    # ── File uploads ──
    upload_dir: Path = Path("uploads")
    max_upload_mb: int = 100

    # ── Tesseract ──
    tesseract_path: str = ""

    # ── Reranking (cross-encoder) ──
    enable_cross_encoder: bool = False

    # ── Vector search ──
    # "faiss" (recommended, scalable) | "python-cosine" (legacy fallback).
    # FAISS builds an in-memory index from MongoDB embeddings and is 100×+ faster.
    vector_search_backend: str = "faiss"
    faiss_build_on_startup: bool = True
    faiss_build_in_background: bool = True
    # Kept for backward compatibility with older callers.
    vector_index_type: str = "python-cosine"

    # ── LLM resilience ──
    llm_max_retries: int = 3
    llm_timeout_connect: float = 15.0
    llm_timeout_read: float = 300.0
    llm_backoff_base: float = 1.0
    llm_backoff_max: float = 16.0
    llm_keep_alive: str = "10m"
    llm_cache_ttl_seconds: int = Field(
        default=3600,
        validation_alias=AliasChoices("DALEEL_LLM_CACHE_TTL_SECONDS", "LLM_CACHE_TTL_SECONDS"),
    )
    llm_cache_max_size: int = Field(
        default=500,
        validation_alias=AliasChoices("DALEEL_LLM_CACHE_MAX_SIZE", "LLM_CACHE_MAX_SIZE"),
    )

    # ── Auto mode routing ──
    auto_mode_enabled: bool = True
    auto_mode_length_threshold: int = 240
    auto_mode_agentic_keywords: str = (
        "conseil,conseils,advice,solution,plan,plan d'action,étapes,etapes,"
        "comment faire,priorité,priorite,exigence,exigences,conformité,conformite,"
        "applicable,obligation,obligations,risque,audit,roadmap,recommandation,"
        "نصيحة,حل,خطة,متطلبات,امتثال,قابل للتطبيق"
    )
    auto_mode_classic_keywords: str = (
        "définition,definition,what is,qu'est-ce que,c'est quoi,explique,explainer,"
        "expliquer,summary,resume,resumé,résumé"
    )
    auto_mode_default: str = "classic"  # "classic" | "agentic"

    # ── CORS ──
    # Comma-separated list of allowed origins. Use "*" only for local dev.
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )

    # ── Authentication (legacy API key — kept for backward compat) ──
    api_key: str = ""
    admin_api_key: str = ""

    # ── JWT Authentication ──
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ── Super admin bootstrap ──
    super_admin_email: str = ""
    super_admin_password: str = ""

    # ── Embedding cache ──
    embedding_cache_maxsize: int = 512

    # ── Multi-tenant ──
    # When set, all queries are scoped to this org. Empty = single-tenant (default).
    multi_tenant_enabled: bool = False

    # ── Answer grounding policy ──
    # When enabled, answers are built only from retrieved database chunks
    # through deterministic synthesis (no free-form generation path).
    strict_grounded_only: bool = False

    # ── Domain-aware RAG ──
    domain_router_enabled: bool = True
    domain_router_llm_fallback_enabled: bool = True

    # ── Partitioned retrieval orchestrator ──
    partitioned_retrieval_enabled: bool = False

    # ── Quality guard (hallucination detection) ──
    quality_guard_enabled: bool = True
    quality_guard_semantic_check_enabled: bool = False

    # ── Fine-tuning: Style model ──
    style_model: str = ""
    style_model_enabled: bool = True
    style_model_timeout: float = 30.0

    # ── Fine-tuning: Reasoning model ──
    reasoning_model_path: str = ""
    reasoning_confidence_threshold: float = 0.7

    # ── Derja (Tunisian dialect) normalization ──
    derja_normalizer_enabled: bool = True

    # ── KG light enrichment ──
    kg_light_enabled: bool = True
    kg_light_max_entities: int = 6

    # ── Email (SMTP) ──
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Daleel"
    smtp_use_tls: bool = True
    app_base_url: str = "http://localhost:8000"

    # ── SMS (OTP de vérification téléphone) ──
    # "" / "log" / "dev"  → l'OTP est seulement loggué (utile en dev).
    # À étendre pour brancher Twilio/Vonage en prod.
    sms_provider: str = "dev"

    model_config = {
        "env_prefix": "DALEEL_",
        "env_file": (_ROOT_ENV_FILE, ".env"),
        "extra": "ignore",
    }


def _validate_production_settings(s: Settings) -> None:
    import os
    env = os.getenv("DALEEL_ENV", "dev").lower()
    if env in ("production", "prod", "staging"):
        if not s.api_key:
            raise RuntimeError(
                "DALEEL_API_KEY must be set in production/staging. "
                "Set DALEEL_ENV=dev to disable this check."
            )
        if not s.admin_api_key:
            raise RuntimeError(
                "DALEEL_ADMIN_API_KEY must be set in production/staging. "
                "Set DALEEL_ENV=dev to disable this check."
            )
        if not s.jwt_secret_key or len(s.jwt_secret_key) < 32:
            raise RuntimeError(
                "DALEEL_JWT_SECRET_KEY must be set to a strong secret (>= 32 chars) in production/staging."
            )
        if s.cors_origins.strip() == "*":
            raise RuntimeError(
                "CORS wildcard '*' is not allowed in production/staging. "
                "Set DALEEL_CORS_ORIGINS to specific origins."
            )


def _load_or_create_dev_jwt_secret() -> str:
    """
    In dev, persist the JWT secret to a file so that:
      - multiple Uvicorn/Gunicorn workers share the same secret
      - restarting the backend does not invalidate existing tokens
    Production must always provide DALEEL_JWT_SECRET_KEY explicitly.
    """
    import os
    import secrets as _secrets
    from pathlib import Path

    path = Path(os.getenv("DALEEL_JWT_SECRET_FILE", ".daleel_jwt_secret"))
    try:
        if path.exists():
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value
        value = _secrets.token_urlsafe(64)
        path.write_text(value, encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass  # best-effort on Windows
        return value
    except OSError:
        # Filesystem unavailable — fall back to ephemeral secret (single worker only).
        return _secrets.token_urlsafe(64)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.jwt_secret_key:
        s.jwt_secret_key = _load_or_create_dev_jwt_secret()
    _validate_production_settings(s)
    return s
