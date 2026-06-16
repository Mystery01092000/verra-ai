"""ingestion microservice (FastAPI). Document OCR/parse/extract, embed into pgvector, retrieval (ADR-0013)."""
from fastapi import FastAPI

app = FastAPI(title="verra-ingestion")


@app.get("/health")
def health() -> dict:
    return {"service": "ingestion", "status": "ok"}


@app.post("/v1/ingest")
def handle(payload: dict) -> dict:
    # TODO: implement Document OCR/parse/extract, embed into pgvector, retrieval (ADR-0013).
    return {"service": "ingestion", "received": payload, "todo": True}
