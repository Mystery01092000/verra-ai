"""Holdings microservice (FastAPI).

Stores per-client holdings and serves the deterministic consolidation engine
(`verra_shared.holdings.consolidate` — no LLM; flags carry guideline citations).
Account/folio numbers are masked before storage, so full numbers are never
persisted nor echoed in any response.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from verra_shared.holdings import ConsolidationResult, Holding, HoldingCreate, consolidate
from verra_shared.infra.logging import configure_logging, get_logger
from verra_shared.infra.metrics import prepare_multiproc_dir
from verra_shared.infra.middleware import HTTPMetricsMiddleware, RequestIDMiddleware

from .config import settings
from .store import HoldingsStore

configure_logging(environment=settings.ENVIRONMENT)
logger = get_logger(__name__)

app = FastAPI(title="verra-holdings", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HTTPMetricsMiddleware, service="holdings")
app.add_middleware(RequestIDMiddleware)

_store: HoldingsStore | None = None


def get_store() -> HoldingsStore:
    """Return the process-wide store, rebuilding it if the store path changed."""
    global _store
    store_path = Path(settings.HOLDINGS_STORE_PATH)
    if _store is None or _store.store_path != store_path:
        _store = HoldingsStore(store_path)
    return _store


@app.on_event("startup")
async def startup() -> None:
    prepare_multiproc_dir(settings.PROMETHEUS_MULTIPROC_DIR)
    store = get_store()
    logger.info(
        "holdings_started",
        environment=settings.ENVIRONMENT,
        store_path=str(store.store_path),
    )


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    from verra_shared.infra.metrics import get_metrics

    content, ct = get_metrics()
    return Response(content=content, media_type=ct)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "holdings", "status": "ok"}


# NOTE: /internal/holdings/consolidation is registered BEFORE the
# /internal/holdings/{holding_id} pattern so "consolidation" is never
# captured as a path parameter.


@app.get("/internal/holdings/consolidation", response_model=ConsolidationResult)
def get_consolidation(
    tenant_id: str = Query(alias="tenantId", min_length=1),
    client_id: str = Query(alias="clientId", min_length=1),
    annual_income: float | None = Query(default=None, alias="annualIncome", ge=0),
) -> ConsolidationResult:
    """Run the deterministic consolidation over the client's stored holdings."""
    holdings = get_store().list_for(tenant_id, client_id)
    return consolidate(holdings, annual_income=annual_income)


@app.post("/internal/holdings", response_model=Holding)
def create_holding(req: HoldingCreate) -> Holding:
    """Validate, assign a uuid, mask the account number and store the holding."""
    holding = Holding(id=str(uuid.uuid4()), **req.model_dump()).masked()
    stored = get_store().add(holding)
    logger.info(
        "holding_created",
        holding_id=stored.id,
        tenant_id=stored.tenant_id,
        client_id=stored.client_id,
        type=str(stored.type),
    )
    return stored


@app.get("/internal/holdings")
def list_holdings(
    tenant_id: str = Query(alias="tenantId", min_length=1),
    client_id: str = Query(alias="clientId", min_length=1),
) -> dict[str, Any]:
    """List the client's holdings (account numbers masked)."""
    holdings = get_store().list_for(tenant_id, client_id)
    return {
        "holdings": [h.masked().model_dump(by_alias=True, mode="json") for h in holdings],
        "count": len(holdings),
    }


@app.delete("/internal/holdings/{holding_id}")
def delete_holding(
    holding_id: str,
    tenant_id: str = Query(alias="tenantId", min_length=1),
    client_id: str = Query(alias="clientId", min_length=1),
) -> dict[str, Any]:
    """Delete one holding; 404 when it does not exist for this tenant/client."""
    if not get_store().delete(tenant_id, client_id, holding_id):
        raise HTTPException(status_code=404, detail="holding not found")
    logger.info("holding_deleted", holding_id=holding_id, tenant_id=tenant_id, client_id=client_id)
    return {"deleted": True, "holdingId": holding_id}
