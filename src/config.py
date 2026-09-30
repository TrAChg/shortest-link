"""
Reads settings from environment variables or .env file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for ShortestLink."""

    APP_NAME: str = "ShortestLink"  # Default, can change in .env
    ENVIRONMENT: str = "development"  # Default
    DEBUG: bool = True  # Default
    BASE_URL: str = "http://localhost:8000"  # Default

    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"  # Default
    REDIS_URL: str = "redis://localhost:6379/0"  # Default
    REDIS_TTL_SECONDS: int = 86400  # Default

    DEFAULT_CODE_LENGTH: int = 6  # Default
    MAX_CUSTOM_ALIAS_LENGTH: int = 30  # Default

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
