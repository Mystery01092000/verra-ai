"""Ingestion microservice (FastAPI).

Deterministic document classification + structured extraction (ADR-0013).
Input is raw text or pre-extracted JSON; no OCR dependency.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from verra_shared.infra.logging import configure_logging, get_logger
from verra_shared.infra.metrics import prepare_multiproc_dir
from verra_shared.infra.middleware import HTTPMetricsMiddleware, RequestIDMiddleware

from .config import settings
from .pipeline import ingest_document
from .schemas import IngestRequest, IngestResponse

configure_logging(environment=settings.ENVIRONMENT)
logger = get_logger(__name__)

app = FastAPI(title="verra-ingestion", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HTTPMetricsMiddleware, service="ingestion")
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
async def startup() -> None:
    prepare_multiproc_dir(settings.PROMETHEUS_MULTIPROC_DIR)
    logger.info("ingestion_started", environment=settings.ENVIRONMENT)


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    from verra_shared.infra.metrics import get_metrics

    content, ct = get_metrics()
    return Response(content=content, media_type=ct)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "ingestion", "status": "ok"}


def _process_ingest(req: IngestRequest) -> IngestResponse:
    try:
        response = ingest_document(req)
    except ValueError as exc:
        logger.warning("ingest_rejected", tenant_id=req.tenant_id, reason=str(exc))
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    logger.info(
        "ingest_processed",
        document_id=response.document_id,
        tenant_id=req.tenant_id,
        doc_type=response.doc_type,
        status=response.status,
        classification_confidence=response.classification_confidence,
        low_confidence_fields=len(response.low_confidence_fields),
        flags=len(response.flags),
    )
    return response


@app.post("/v1/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest) -> IngestResponse:
    """Classify + extract a document (public route, reached via the gateway)."""
    return _process_ingest(req)


@app.post("/internal/ingest", response_model=IngestResponse)
def ingest_internal(req: IngestRequest) -> IngestResponse:
    """Internal alias for service-to-service calls (gateway routes here)."""
    return _process_ingest(req)
