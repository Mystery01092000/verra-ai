"""Audit microservice (FastAPI).

Append-only, hash-chained audit log + action receipts (ADR-0015).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from verra_shared.infra.logging import configure_logging, get_logger
from verra_shared.infra.metrics import prepare_multiproc_dir
from verra_shared.infra.middleware import HTTPMetricsMiddleware, RequestIDMiddleware

from .chain import AuditChain, AuditRecord
from .config import settings

configure_logging(environment=settings.ENVIRONMENT)
logger = get_logger(__name__)

app = FastAPI(title="verra-audit", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HTTPMetricsMiddleware, service="audit")
app.add_middleware(RequestIDMiddleware)

_chain: AuditChain | None = None


def get_chain() -> AuditChain:
    """Return the process-wide chain, rebuilding it if the log path changed."""
    global _chain
    log_path = Path(settings.AUDIT_LOG_PATH)
    if _chain is None or _chain.log_path != log_path:
        _chain = AuditChain(log_path)
    return _chain


class AuditEventRequest(BaseModel):
    type: str = Field(min_length=1, max_length=200)
    data: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = ""
    agent: str = "system"


def _receipt(record: AuditRecord) -> dict[str, Any]:
    return {
        "event_id": record.event_id,
        "hash": record.hash,
        "prev_hash": record.prev_hash,
        "ts": record.ts,
        "logged": True,
    }


@app.on_event("startup")
async def startup() -> None:
    prepare_multiproc_dir(settings.PROMETHEUS_MULTIPROC_DIR)
    chain = get_chain()
    logger.info(
        "audit_started",
        environment=settings.ENVIRONMENT,
        chain_length=len(chain),
        log_path=str(chain.log_path),
    )


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    from verra_shared.infra.metrics import get_metrics

    content, ct = get_metrics()
    return Response(content=content, media_type=ct)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "audit", "status": "ok"}


@app.post("/internal/events")
def append_event(req: AuditEventRequest) -> dict[str, Any]:
    """Append an immutable audit event and return its chain receipt."""
    record = get_chain().append(
        event_type=req.type,
        data=req.data,
        tenant_id=req.tenant_id,
        agent=req.agent,
    )
    logger.info(
        "audit_event_appended",
        event_id=record.event_id,
        type=record.type,
        tenant_id=record.tenant_id,
        hash=record.hash,
    )
    return _receipt(record)


@app.get("/internal/events")
def list_events(
    limit: int = Query(default=50, ge=1, le=1000),
    tenant_id: str | None = Query(default=None),
) -> dict[str, Any]:
    """Return the most recent events, optionally filtered by tenant."""
    records = get_chain().recent(limit=limit, tenant_id=tenant_id)
    return {"events": [r.to_dict() for r in records], "count": len(records)}


@app.get("/internal/verify")
def verify_chain() -> dict[str, Any]:
    """Re-walk the persisted chain and report integrity."""
    chain = get_chain()
    ok, first_bad_index = chain.verify()
    if not ok:
        logger.error("audit_chain_verification_failed", first_bad_index=first_bad_index)
    return {"ok": ok, "first_bad_index": first_bad_index, "length": len(chain)}


@app.post("/v1/events")
def append_event_public(req: AuditEventRequest) -> dict[str, Any]:
    """Public shape (via gateway) — same append-only, hash-chained semantics."""
    return append_event(req)
