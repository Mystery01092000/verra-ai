"""registry microservice (FastAPI). Agent + tool registries (versioned manifests, capabilities, permissions)."""
from fastapi import FastAPI

app = FastAPI(title="verra-registry")


@app.get("/health")
def health() -> dict:
    return {"service": "registry", "status": "ok"}


@app.post("/v1/resolve")
def handle(payload: dict) -> dict:
    # TODO: implement Agent + tool registries (versioned manifests, capabilities, permissions).
    return {"service": "registry", "received": payload, "todo": True}
