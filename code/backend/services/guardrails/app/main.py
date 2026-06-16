"""guardrails microservice (FastAPI). Input/output validation, PII/DLP, prompt-injection detection, policy (OPA/Cedar)."""
from fastapi import FastAPI

app = FastAPI(title="verra-guardrails")


@app.get("/health")
def health() -> dict:
    return {"service": "guardrails", "status": "ok"}


@app.post("/v1/check")
def handle(payload: dict) -> dict:
    # TODO: implement Input/output validation, PII/DLP, prompt-injection detection, policy (OPA/Cedar).
    return {"service": "guardrails", "received": payload, "todo": True}
