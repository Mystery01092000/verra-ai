"""audit microservice (FastAPI). Append-only, hash-chained audit log + action receipts (ADR-0015)."""
from fastapi import FastAPI

app = FastAPI(title="verra-audit")


@app.get("/health")
def health() -> dict:
    return {"service": "audit", "status": "ok"}


@app.post("/v1/events")
def handle(payload: dict) -> dict:
    # TODO: implement Append-only, hash-chained audit log + action receipts (ADR-0015).
    return {"service": "audit", "received": payload, "todo": True}
