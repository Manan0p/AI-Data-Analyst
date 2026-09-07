import os
import tempfile
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

def _is_serverless() -> bool:
    return bool(
        os.environ.get("VERCEL")
        or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("LAMBDA_TASK_ROOT")
        or os.environ.get("NOW_REGION")
    )

def _default_upload_dir() -> Path:
    if _is_serverless():
        return Path(tempfile.gettempdir()) / "insightforge" / "uploads"
    return Path("data/uploads")

def _default_db_url() -> str:
    if _is_serverless():
        return f"sqlite:///{Path(tempfile.gettempdir()) / 'insightforge.db'}"
    return "sqlite:///./insightforge.db"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "AI Data Analyst"
    cors_origins: str = "*"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    upload_dir: Path = _default_upload_dir()
    max_upload_mb: int = 25
    max_row_count: int = 500_000
    database_url: str = _default_db_url()
    jwt_secret: str = "insightforge-insecure-dev-secret-replace-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    log_format: str = "json"  # "json" or "text"
    sentry_dsn: str | None = None

    # ── Upstash Redis (L1 chat history cache) ─────────────────────────────────
    upstash_redis_rest_url: str | None = None
    upstash_redis_rest_token: str | None = None
    redis_chat_ttl_seconds: int = 86400        # 24 h per session
    chat_context_window: int = 20              # recent turns kept in Redis

    # ── Upstash Vector (L2 RAG semantic retrieval) ────────────────────────────
    upstash_vector_rest_url: str | None = None
    upstash_vector_rest_token: str | None = None
    rag_top_k: int = 4                         # semantic hits injected into LLM

    # ── Embedding model ───────────────────────────────────────────────────────
    embedding_model: str = "text-embedding-004"  # Gemini embedding model

settings = Settings()

