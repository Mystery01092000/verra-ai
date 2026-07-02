"""Gateway service configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    ORCHESTRATOR_URL: str = "http://orchestrator:8081"
    INGESTION_URL: str = "http://ingestion:8087"
    AUDIT_URL: str = "http://audit:8086"
    HOLDINGS_URL: str = "http://holdings:8083"
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus_multiproc"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
