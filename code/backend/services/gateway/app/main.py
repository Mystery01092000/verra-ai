"""Gateway — sole public-facing entry point; proxies to the orchestrator (ADR-0001)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from verra_shared.infra.logging import configure_logging, get_logger
from verra_shared.infra.metrics import prepare_multiproc_dir
from verra_shared.infra.middleware import HTTPMetricsMiddleware, RequestIDMiddleware

from .config import settings

configure_logging(environment=settings.ENVIRONMENT)
logger = get_logger(__name__)

app = FastAPI(title="verra-gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HTTPMetricsMiddleware, service="gateway")
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
async def startup() -> None:
    prepare_multiproc_dir(settings.PROMETHEUS_MULTIPROC_DIR)
    logger.info("gateway_started", environment=settings.ENVIRONMENT)


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    from verra_shared.infra.metrics import get_metrics

    content, ct = get_metrics()
    return Response(content=content, media_type=ct)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "gateway", "status": "ok"}


# Path-prefix routing: everything defaults to the orchestrator (ADR-0001);
# ingestion, audit and holdings are the only services with their own public surface.
@dataclass(frozen=True)
class _Upstream:
    prefix: str
    setting_name: str
    # When True the whole original path (prefix included) is preserved, so
    # /v1/holdings/consolidation → {base}/internal/holdings/consolidation.
    # When False the prefix is stripped: /v1/audit/events → {base}/internal/events.
    keep_prefix: bool = False


_UPSTREAMS: list[_Upstream] = [
    _Upstream("ingest", "INGESTION_URL"),
    _Upstream("audit", "AUDIT_URL"),
    _Upstream("holdings", "HOLDINGS_URL", keep_prefix=True),
]


def _resolve_upstream(path: str) -> str:
    for upstream in _UPSTREAMS:
        prefix = upstream.prefix
        if path == prefix or path.startswith(f"{prefix}/"):
            base = getattr(settings, upstream.setting_name)
            if upstream.keep_prefix:
                return f"{base}/internal/{path}"
            suffix = path[len(prefix) :].lstrip("/")
            return f"{base}/internal/{suffix}" if suffix else f"{base}/internal/{prefix}"
    return f"{settings.ORCHESTRATOR_URL}/internal/{path}"


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request) -> Response:
    """Forward all /v1/* requests to the owning backend service."""
    url = _resolve_upstream(path)
    body = await request.body()
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.request(
                method=request.method,
                url=url,
                content=body,
                params=dict(request.query_params),
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            )
    except httpx.HTTPError as exc:
        logger.error("gateway_proxy_error", path=path, error=str(exc))
        raise HTTPException(status_code=502, detail="Upstream unavailable") from exc
    try:
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except ValueError:
        # Non-JSON upstream body (redirect, plain-text error page): pass it through
        # verbatim rather than crashing the proxy.
        logger.warning("gateway_non_json_upstream", path=path, status=resp.status_code)
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "text/plain"),
        )
