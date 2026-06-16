"""HTTP clients to the other microservices (ADR-0017)."""
import os

GUARDRAILS_URL = os.getenv("GUARDRAILS_URL", "http://guardrails:8084")
MODEL_GATEWAY_URL = os.getenv("MODEL_GATEWAY_URL", "http://model_gateway:8082")
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8085")
AUDIT_URL = os.getenv("AUDIT_URL", "http://audit:8086")
INGESTION_URL = os.getenv("INGESTION_URL", "http://ingestion:8087")
# TODO: thin async httpx wrappers with retries/timeouts + mTLS.
