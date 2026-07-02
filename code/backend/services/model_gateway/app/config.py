"""Model gateway configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # AWS Bedrock (primary provider)
    # Auth: bearer token (IAM Identity Center) takes priority over key/secret
    AWS_REGION: str = "us-east-1"
    AWS_BEARER_TOKEN_BEDROCK: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # OpenAI (fallback provider)
    OPENAI_API_KEY: str = ""

    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus_multiproc"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
