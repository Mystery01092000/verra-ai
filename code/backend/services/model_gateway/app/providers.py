"""Provider abstraction + health/budget-aware fallback chain (ADR-0006)."""
from __future__ import annotations

from typing import Protocol


class Provider(Protocol):
    name: str
    async def complete(self, req: dict) -> dict: ...


class FallbackChain:
    """primary frontier -> secondary -> self-hosted -> degraded (cache/rules/human)."""

    def __init__(self, providers: list[Provider]):
        self._providers = providers

    async def complete(self, req: dict) -> dict:
        for p in self._providers:
            try:
                return await self._with_breaker(p, req)  # TODO retries/backoff + circuit breaker
            except Exception:
                continue  # TODO record fallback hop (provider, reason, cost) to trace + audit
        return {"text": "", "tokens_in": 0, "tokens_out": 0, "degraded": True}

    async def _with_breaker(self, p: Provider, req: dict) -> dict:
        return await p.complete(req)
