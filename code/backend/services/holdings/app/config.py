"""Holdings service configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus_multiproc"
    HOLDINGS_STORE_PATH: str = "/tmp/verra_holdings/holdings.jsonl"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
