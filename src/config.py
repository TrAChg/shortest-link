"""Application configuration using Pydantic Settings.

Reads settings from environment variables or .env file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for ShortestLink."""

    APP_NAME: str = "ShortestLink"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    BASE_URL: str = "http://localhost:8000"

    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL_SECONDS: int = 86400

    DEFAULT_CODE_LENGTH: int = 6
    MAX_CUSTOM_ALIAS_LENGTH: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
