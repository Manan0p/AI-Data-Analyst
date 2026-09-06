from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "AI Data Analyst"
    cors_origins: str = "*"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    upload_dir: Path = Path("data/uploads")
    max_upload_mb: int = 25
    max_row_count: int = 500_000
    database_url: str = "sqlite:///./insightforge.db"
    jwt_secret: str = "insightforge-insecure-dev-secret-replace-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    log_format: str = "json"  # "json" or "text"
    sentry_dsn: str | None = None

settings = Settings()

