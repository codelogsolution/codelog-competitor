from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "KOMP Competitor Intelligence Agent"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = ""
    LOG_LEVEL: str = "INFO"

    # Provider selection: anthropic (current FreeLLMAPI proxy or Anthropic API),
    # openai, or vertex_ai. Only one provider is active per run.
    LLM_PROVIDER: str = "anthropic"
    LLM_MODEL: str = "nvidia/nemotron-3.5-super-vl-120b-a12b"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 3500

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "http://127.0.0.1:31415"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"

    TAVILY_API_KEY: str = ""

    FRONTEND_ORIGIN: str = "http://localhost:5173"
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_UPLOAD_ROWS: int = 10000
    MAX_XLSX_UNCOMPRESSED_MB: int = 100
    UPLOAD_DIR: str = "../data/uploads"
    EXPORT_DIR: str = "../data/exports"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
