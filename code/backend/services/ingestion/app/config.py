"""Ingestion service configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgresql://verra:verra@postgres:5432/verra"
    MINIO_URL: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "verra"
    MINIO_SECRET_KEY: str = "verra-secret"
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus_multiproc"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
