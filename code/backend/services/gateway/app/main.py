"""API gateway (ADR-0010/0017). The only public entrypoint; modules/clients call THIS."""
import os

import httpx
from fastapi import FastAPI, Request

app = FastAPI(title="verra-gateway")
ORCH = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8081")


@app.get("/health")
def health() -> dict:
    return {"service": "gateway", "status": "ok"}


@app.middleware("http")
async def cross_cutting(request: Request, call_next):  # type: ignore[no-untyped-def]
    # TODO: verify OIDC/mTLS, resolve tenant, enforce rate limits, idempotency replay.
    return await call_next(request)


@app.post("/v1/runs")
async def create_run(payload: dict) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{ORCH}/internal/runs", json=payload, timeout=30)
        return r.json()


@app.get("/v1/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        return (await client.get(f"{ORCH}/internal/runs/{run_id}")).json()
# TODO: GET /v1/runs/{id}/events -> SSE proxy; POST approve/reject.
