"""Guardrails service — PII/DLP screening and policy enforcement."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from verra_shared.infra.logging import configure_logging, get_logger
from verra_shared.infra.metrics import prepare_multiproc_dir
from verra_shared.infra.middleware import HTTPMetricsMiddleware, RequestIDMiddleware

from .checks import GuardrailResult, evaluate
from .config import settings

configure_logging(environment=settings.ENVIRONMENT)
logger = get_logger(__name__)

app = FastAPI(title="verra-guardrails", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HTTPMetricsMiddleware, service="guardrails")
app.add_middleware(RequestIDMiddleware)


class CheckContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    requires_citations: bool = Field(default=False, alias="requiresCitations")
    citations: list[Any] = Field(default_factory=list)


class CheckRequest(BaseModel):
    content: str = ""
    text: str = ""  # legacy field name used by existing orchestrator clients
    context: CheckContext | None = None
    action: str = ""
    tenant_id: str = ""

    @property
    def effective_content(self) -> str:
        return self.content or self.text


@app.on_event("startup")
async def startup() -> None:
    prepare_multiproc_dir(settings.PROMETHEUS_MULTIPROC_DIR)
    logger.info("guardrails_started", environment=settings.ENVIRONMENT)


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    from verra_shared.infra.metrics import get_metrics

    content, ct = get_metrics()
    return Response(content=content, media_type=ct)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "guardrails", "status": "ok"}


def _run_checks(req: CheckRequest) -> GuardrailResult:
    context = req.context or CheckContext()
    return evaluate(
        req.effective_content,
        citation_context={
            "requiresCitations": context.requires_citations,
            "citations": context.citations,
        },
        action=req.action,
    )


def _to_response(result: GuardrailResult, tenant_id: str) -> dict[str, Any]:
    response: dict[str, Any] = {
        "allowed": result.allowed,
        "flagged": [dict(finding) for finding in result.flagged],
        "tenant_id": tenant_id,
    }
    if result.masked_content is not None:
        response["masked_content"] = result.masked_content
    return response


@app.post("/internal/check")
def check(req: CheckRequest) -> dict[str, Any]:
    """Screen content for PII, prompt injection, and citation policy."""
    result = _run_checks(req)
    logger.info(
        "guardrails_check",
        allowed=result.allowed,
        flag_count=len(result.flagged),
        flag_types=[finding["type"] for finding in result.flagged],
        action=req.action,
        tenant_id=req.tenant_id,
    )
    return _to_response(result, req.tenant_id)


@app.post("/v1/check")
def check_public(req: CheckRequest) -> dict[str, Any]:
    """Public shape (via gateway) — same checks as /internal/check."""
    return check(req)
