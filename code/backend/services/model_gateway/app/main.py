"""Model gateway service. Routing is tier/cost/latency-aware; centralizes fallbacks + token metering."""
from fastapi import FastAPI

from .providers import FallbackChain

app = FastAPI(title="verra-model_gateway")
chain = FallbackChain(providers=[])  # TODO register anthropic, secondary, self-hosted


@app.get("/health")
def health() -> dict:
    return {"service": "model_gateway", "status": "ok"}


@app.post("/v1/complete")
async def complete(req: dict) -> dict:
    return await chain.complete(req)
