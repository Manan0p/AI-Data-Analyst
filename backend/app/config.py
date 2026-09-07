from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "AI Data Analyst"
    cors_origins: str = "*"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    upload_dir: Path = Path("data/uploads")
    max_upload_mb: int = 25
    max_row_count: int = 500_000
    database_url: str = "sqlite:///./insightforge.db"
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

