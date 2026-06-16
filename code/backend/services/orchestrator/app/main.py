"""Orchestrator service. Internal API used by the gateway; runs the layered core."""
from fastapi import FastAPI

from verra_shared import RunRequest

from .core.supervisor import Supervisor

app = FastAPI(title="verra-orchestrator")
supervisor = Supervisor()


@app.get("/health")
def health() -> dict:
    return {"service": "orchestrator", "status": "ok"}


@app.post("/internal/runs")
async def create_run(req: RunRequest) -> dict:
    run = await supervisor.start(req)
    return {"run_id": run["id"], "stream": f"/v1/runs/{run['id']}/events"}


@app.get("/internal/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    return await supervisor.status(run_id)
