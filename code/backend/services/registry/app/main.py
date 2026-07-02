"""Registry microservice (FastAPI).

Agent + tool registries (versioned manifests, capabilities, permissions).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from verra_shared.infra.logging import configure_logging, get_logger
from verra_shared.infra.metrics import prepare_multiproc_dir
from verra_shared.infra.middleware import HTTPMetricsMiddleware, RequestIDMiddleware

from .config import settings
from .registry import list_capabilities, list_tools, resolve_capability, resolve_tool

configure_logging(environment=settings.ENVIRONMENT)
logger = get_logger(__name__)

app = FastAPI(title="verra-registry", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HTTPMetricsMiddleware, service="registry")
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
async def startup() -> None:
    prepare_multiproc_dir(settings.PROMETHEUS_MULTIPROC_DIR)
    logger.info("registry_started", environment=settings.ENVIRONMENT)


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    from verra_shared.infra.metrics import get_metrics

    content, ct = get_metrics()
    return Response(content=content, media_type=ct)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "registry", "status": "ok"}


@app.post("/v1/resolve")
def resolve(payload: dict[str, Any]) -> dict[str, Any]:
    kind = payload.get("kind")
    if kind == "capability":
        result = resolve_capability(str(payload.get("module")), str(payload.get("capability")))
    elif kind == "tool":
        result = resolve_tool(str(payload.get("name")))
    else:
        return {"error": "kind must be 'capability' or 'tool'"}
    if result is None:
        return {"error": f"{kind} not found"}
    return result


@app.get("/v1/capabilities")
def capabilities(module: str | None = None) -> list[dict[str, Any]]:
    return list_capabilities(module)


@app.get("/v1/tools")
def tools(module: str | None = None) -> list[dict[str, Any]]:
    return list_tools(module)
