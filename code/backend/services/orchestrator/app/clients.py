"""Async HTTP clients to downstream services, protected by circuit breakers (ADR-0017)."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from verra_shared.infra.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from verra_shared.infra.logging import get_logger

from .config import settings

logger = get_logger(__name__)

_breakers: dict[str, CircuitBreaker] = {}


def _get_breaker(dependency: str) -> CircuitBreaker:
    if dependency not in _breakers:
        _breakers[dependency] = CircuitBreaker(
            service_name="orchestrator",
            dependency_name=dependency,
            redis_url=settings.REDIS_URL,
            failure_threshold=settings.CB_FAILURE_THRESHOLD,
            timeout_seconds=settings.CB_TIMEOUT_SECONDS,
            success_threshold=settings.CB_SUCCESS_THRESHOLD,
        )
    return _breakers[dependency]


async def _post(url: str, payload: dict[str, Any], dependency: str) -> dict[str, Any]:
    """POST JSON with circuit-breaker protection; runs sync httpx in a thread pool."""
    breaker = _get_breaker(dependency)
    loop = asyncio.get_running_loop()

    def _sync() -> dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, dict) else {"result": data}

    return await loop.run_in_executor(None, lambda: breaker.call(_sync))


async def _get(url: str, params: dict[str, Any], dependency: str) -> Any:
    """GET JSON with circuit-breaker protection; runs sync httpx in a thread pool."""
    breaker = _get_breaker(dependency)
    loop = asyncio.get_running_loop()

    def _sync() -> Any:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    return await loop.run_in_executor(None, lambda: breaker.call(_sync))


# ── Public client functions ───────────────────────────────────────────────────


async def check_guardrails(text: str, tenant_id: str) -> dict[str, Any]:
    """Screen text through the guardrails service (PII/DLP + policy checks)."""
    try:
        return await _post(
            f"{settings.GUARDRAILS_URL}/internal/check",
            {"text": text, "tenant_id": tenant_id},
            "guardrails",
        )
    except CircuitBreakerOpenError:
        logger.warning("guardrails_circuit_open_allowing_degraded")
        return {"allowed": True, "flagged": [], "degraded": True}


async def call_model_gateway(
    messages: list[dict[str, str]],
    system: str | None,
    model_tier: str,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Send a completion request to the model gateway (Bedrock → OpenAI fallback)."""
    return await _post(
        f"{settings.MODEL_GATEWAY_URL}/internal/complete",
        {
            "messages": messages,
            "system": system,
            "model_tier": model_tier,
            "max_tokens": max_tokens,
        },
        "model_gateway",
    )


async def write_audit_event(event: dict[str, Any]) -> dict[str, Any]:
    """Append an immutable audit event to the audit service."""
    try:
        return await _post(f"{settings.AUDIT_URL}/internal/events", event, "audit")
    except CircuitBreakerOpenError:
        logger.error("audit_circuit_open_event_lost", event_type=event.get("type"))
        return {"logged": False, "degraded": True}


async def fetch_holdings(tenant_id: str, client_id: str) -> dict[str, Any]:
    """Fetch client holdings from the holdings service (shape-tolerant).

    The holdings service returns camelCase ``{"holdings": [...]}``; a bare list
    is also accepted. Transport errors propagate so the executor can degrade the
    step instead of crashing the run.
    """
    data = await _get(
        f"{settings.HOLDINGS_URL}/internal/holdings",
        {"tenantId": tenant_id, "clientId": client_id},
        "holdings",
    )
    if isinstance(data, list):
        return {"holdings": data}
    if isinstance(data, dict):
        return data
    logger.warning("holdings_unexpected_shape", shape=type(data).__name__)
    return {"holdings": []}


async def fetch_consolidation(
    tenant_id: str,
    client_id: str,
    annual_income: float | None = None,
) -> dict[str, Any]:
    """Fetch the deterministic consolidated portfolio view from the holdings service."""
    params: dict[str, Any] = {"tenantId": tenant_id, "clientId": client_id}
    if annual_income is not None:
        params["annualIncome"] = annual_income
    data = await _get(
        f"{settings.HOLDINGS_URL}/internal/holdings/consolidation",
        params,
        "holdings",
    )
    if isinstance(data, dict):
        return data
    logger.warning("consolidation_unexpected_shape", shape=type(data).__name__)
    return {"result": data}


async def lookup_registry(tool_name: str) -> dict[str, Any]:
    """Resolve a tool manifest from the registry service (POST /v1/resolve)."""
    return await _post(
        f"{settings.REGISTRY_URL}/v1/resolve",
        {"kind": "tool", "name": tool_name},
        "registry",
    )


async def lookup_capability(module: str, capability: str) -> dict[str, Any]:
    """Resolve a capability manifest (approval policy, required tools) from the registry."""
    return await _post(
        f"{settings.REGISTRY_URL}/v1/resolve",
        {"kind": "capability", "module": module, "capability": capability},
        "registry",
    )
