from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "KOMP Competitor Intelligence Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"

    # LLM configuration
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "http://127.0.0.1:31415"
    CLAUDE_MODEL: str = "nemotron-3.5-lightning"

    # Web research
    TAVILY_API_KEY: str = ""

    # Application configuration
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "../data/uploads"
    EXPORT_DIR: str = "../data/exports"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()