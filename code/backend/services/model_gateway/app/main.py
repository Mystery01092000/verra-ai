"""Model gateway — LLM abstraction layer (Bedrock primary, OpenAI fallback, ADR-0006)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from verra_shared.infra.logging import configure_logging, get_logger
from verra_shared.infra.metrics import prepare_multiproc_dir
from verra_shared.infra.middleware import HTTPMetricsMiddleware, RequestIDMiddleware

from .config import settings
from .providers import BedrockProvider, FallbackChain, NovaProvider, OpenAIProvider

configure_logging(environment=settings.ENVIRONMENT)
logger = get_logger(__name__)

app = FastAPI(title="verra-model-gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HTTPMetricsMiddleware, service="model_gateway")
app.add_middleware(RequestIDMiddleware)

chain = FallbackChain(providers=[BedrockProvider(), NovaProvider(), OpenAIProvider()])


class CompleteRequest(BaseModel):
    messages: list[dict[str, str]]
    system: str | None = None
    model_tier: str = "medium"
    max_tokens: int = 2048


@app.on_event("startup")
async def startup() -> None:
    prepare_multiproc_dir(settings.PROMETHEUS_MULTIPROC_DIR)
    logger.info(
        "model_gateway_started", environment=settings.ENVIRONMENT, providers=chain.provider_names
    )


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    from verra_shared.infra.metrics import get_metrics

    content, ct = get_metrics()
    return Response(content=content, media_type=ct)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "model_gateway", "status": "ok", "providers": chain.provider_names}


@app.post("/internal/complete")
async def complete(req: CompleteRequest) -> dict[str, Any]:
    """Route a completion request through the provider chain."""
    logger.info("complete_request", model_tier=req.model_tier, max_tokens=req.max_tokens)
    result = await chain.complete(
        messages=req.messages,
        system=req.system,
        max_tokens=req.max_tokens,
        model_tier=req.model_tier,
    )
    if result.get("error"):
        logger.error("complete_all_providers_failed", error=result.get("error"))
    return result
