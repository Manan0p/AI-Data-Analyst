from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "AI Data Analyst"
    cors_origins: str = "http://localhost:3000"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    upload_dir: Path = Path("data/uploads")
    max_upload_mb: int = 25
settings = Settings()
