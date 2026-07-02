"""Orchestrator service configuration via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Service mesh
    REDIS_URL: str = "redis://redis:6379"
    DATABASE_URL: str = "postgresql://verra:verra@postgres:5432/verra"
    TEMPORAL_HOST: str = "temporal:7233"

    # Downstream service URLs
    GUARDRAILS_URL: str = "http://guardrails:8084"
    MODEL_GATEWAY_URL: str = "http://model_gateway:8082"
    REGISTRY_URL: str = "http://registry:8085"
    AUDIT_URL: str = "http://audit:8086"
    INGESTION_URL: str = "http://ingestion:8087"
    HOLDINGS_URL: str = "http://holdings:8083"

    # Circuit breaker defaults
    CB_FAILURE_THRESHOLD: int = 5
    CB_TIMEOUT_SECONDS: int = 60
    CB_SUCCESS_THRESHOLD: int = 2

    # Observability
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus_multiproc"


settings = Settings()
