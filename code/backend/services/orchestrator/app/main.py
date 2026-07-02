"""Orchestrator service — internal API used by the gateway; runs the layered Supervisor core."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from verra_shared import RunAccepted, RunRequest, RunResult, RunStatus
from verra_shared.infra.logging import configure_logging, get_logger
from verra_shared.infra.metrics import prepare_multiproc_dir
from verra_shared.infra.middleware import HTTPMetricsMiddleware, RequestIDMiddleware

from .config import settings
from .core.supervisor import InvalidRunStateError, RunNotFoundError, Supervisor
from .schemas import ApprovalRequest, RunSummary
from .tools import router as tools_router

# Friendly wire aliases accepted on top of the canonical RunStatus values.
_STATUS_ALIASES: dict[str, str] = {
    "needs_approval": "awaiting_approval",
    "completed": "done",
    "rejected": "failed",
}

configure_logging(environment=settings.ENVIRONMENT)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    prepare_multiproc_dir(settings.PROMETHEUS_MULTIPROC_DIR)
    logger.info("orchestrator_started", environment=settings.ENVIRONMENT)
    yield


app = FastAPI(title="verra-orchestrator", version="1.0.0", lifespan=lifespan)

# Middleware — outermost first (FastAPI processes add_middleware in LIFO)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(HTTPMetricsMiddleware, service="orchestrator")
app.add_middleware(RequestIDMiddleware)

app.include_router(tools_router)
supervisor = Supervisor()


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    from verra_shared.infra.metrics import get_metrics

    content, ct = get_metrics()
    return Response(content=content, media_type=ct)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"service": "orchestrator", "status": "ok"}


def _to_run_result(status: dict[str, Any]) -> RunResult:
    return RunResult(
        run_id=status["run_id"],
        status=status["status"],
        output=status.get("output"),
        citations=status.get("citations", []),
        cost=status.get("cost", {}),
        receipt_id=status.get("receipt_id"),
    )


def _parse_status_filter(status: str | None) -> RunStatus | None:
    if status is None:
        return None
    canonical = _STATUS_ALIASES.get(status, status)
    try:
        return RunStatus(canonical)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"unknown status '{status}'") from exc


@app.post("/internal/runs", response_model=RunAccepted)
async def create_run(req: RunRequest) -> RunAccepted:
    run = await supervisor.start(req)
    return RunAccepted(run_id=run["id"], stream=f"/v1/runs/{run['id']}/events")


@app.get("/internal/runs", response_model=list[RunSummary])
async def list_runs(
    status: str | None = None, limit: int = Query(default=50, ge=1, le=500)
) -> list[RunSummary]:
    summaries = supervisor.list_runs(status=_parse_status_filter(status), limit=limit)
    return [RunSummary(**summary) for summary in summaries]


@app.get("/internal/runs/{run_id}", response_model=RunResult)
async def get_run(run_id: str) -> RunResult:
    try:
        status = await supervisor.status(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found") from exc
    return _to_run_result(status)


@app.post("/internal/runs/{run_id}/approve", response_model=RunResult)
async def approve_run(run_id: str, body: ApprovalRequest) -> RunResult:
    try:
        status = await supervisor.approve(run_id, body.approver, body.note)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found") from exc
    except InvalidRunStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"run not awaiting approval (status={exc.current_status})",
        ) from exc
    return _to_run_result(status)


@app.post("/internal/runs/{run_id}/reject", response_model=RunResult)
async def reject_run(run_id: str, body: ApprovalRequest) -> RunResult:
    try:
        status = await supervisor.reject(run_id, body.approver, body.note)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found") from exc
    except InvalidRunStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"run not awaiting approval (status={exc.current_status})",
        ) from exc
    return _to_run_result(status)
