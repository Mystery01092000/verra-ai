"""Registry service configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgresql://verra:verra@postgres:5432/verra"
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus_multiproc"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
