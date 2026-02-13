"""Configuration and settings module."""

from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    driver: str = "postgresql"
    user: str = "copilot_user"
    password: str = "copilot_password"
    host: str = "localhost"
    port: int = 5432
    name: str = "copilot_db"
    echo: bool = False

    @property
    def url(self) -> str:
        """Build database URL."""
        return f"{self.driver}+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        """Build synchronous database URL for migrations."""
        return f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Redis configuration."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

    @property
    def url(self) -> str:
        """Build Redis URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = "REDIS_"


class Settings(BaseSettings):
    """Application settings."""

    # Service configuration
    service_name: str = "unknown-service"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Database
    database: DatabaseSettings = DatabaseSettings()

    # Redis
    redis: RedisSettings = RedisSettings()

    # API
    api_title: str = "Manufacturing AI Copilot API"
    api_version: str = "1.0.0"
    api_docs_url: Optional[str] = "/docs"
    api_redoc_url: Optional[str] = "/redoc"

    # Service mesh
    enable_service_mesh: bool = False

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
