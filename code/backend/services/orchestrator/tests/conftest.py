"""Shared fixtures — all downstream HTTP traffic is stubbed behind app.clients._post."""

from __future__ import annotations

from typing import Any

import pytest
from app import clients
from app.core.executor import _DETERMINISTIC_TOOLS
from app.core.run_store import RunStore
from fastapi.testclient import TestClient

_CAPABILITIES: dict[tuple[str, str], dict[str, Any]] = {
    ("tax", "tax_analysis"): {
        "module": "tax",
        "capability": "tax_analysis",
        "model_tier": "large",
        "approval_required": True,
    },
    ("tax", "tax_qa"): {
        "module": "tax",
        "capability": "tax_qa",
        "model_tier": "small",
        "approval_required": False,
    },
    ("tax", "tax_scenario"): {
        "module": "tax",
        "capability": "tax_scenario",
        "model_tier": "large",
        "approval_required": False,
    },
    ("assistant", "portfolio_analysis"): {
        "module": "assistant",
        "capability": "portfolio_analysis",
        "model_tier": "medium",
        "approval_required": False,
    },
    ("assistant", "financial_planning"): {
        "module": "assistant",
        "capability": "financial_planning",
        "model_tier": "large",
        "approval_required": True,
    },
    ("assistant", "general_qa"): {
        "module": "assistant",
        "capability": "general_qa",
        "model_tier": "medium",
        "approval_required": False,
    },
}


class FakeDownstream:
    """In-memory stand-ins for registry, model_gateway, guardrails, audit + holdings."""

    def __init__(self) -> None:
        self.audit_events: list[dict[str, Any]] = []
        self.model_calls: list[dict[str, Any]] = []
        self.guardrail_calls: list[dict[str, Any]] = []
        self.holdings_calls: list[dict[str, Any]] = []
        self.deny_when: str | None = None
        self.model_error: Exception | None = None
        self.holdings_error: Exception | None = None
        self.model_response: dict[str, Any] = {
            "content": (
                "DRAFT for review: based on the calculator figures provided, consider "
                "Section 80C investments and Section 80CCD(1B) NPS contributions."
            ),
            "provider": "stub",
            "model": "stub-large",
            "usage": {"inputTokens": 120, "outputTokens": 80},
        }
        self.holdings_response: dict[str, Any] = {
            "holdings": [
                {
                    "instrumentType": "equity_mutual_fund",
                    "category": "flexi_cap",
                    "units": 1200.0,
                    "currentValue": 950_000.0,
                },
                {"instrumentType": "fixed_deposit", "currentValue": 400_000.0},
            ],
            "citations": [{"docId": "holdings-stmt-1", "page": 1}],
        }
        self.consolidation_response: dict[str, Any] = {
            "totalValue": 1_350_000.0,
            "allocation": {"equity": 0.70, "debt": 0.30},
            "unrealizedLtcgEquity": 90_000.0,
            "citations": [{"docId": "holdings-stmt-1", "page": 1}],
        }

    async def post(self, url: str, payload: dict[str, Any], dependency: str) -> dict[str, Any]:
        if url.endswith("/v1/resolve"):
            return self._resolve(payload)
        if url.endswith("/internal/complete"):
            self.model_calls.append(payload)
            if self.model_error is not None:
                raise self.model_error
            return dict(self.model_response)
        if url.endswith("/internal/check"):
            self.guardrail_calls.append(payload)
            denied = self.deny_when is not None and self.deny_when in payload["text"]
            return {"allowed": not denied, "flagged": ["policy_block"] if denied else []}
        if url.endswith("/internal/events"):
            self.audit_events.append(payload)
            return {"event_id": f"evt-{len(self.audit_events)}", "logged": True}
        raise AssertionError(f"unexpected downstream URL: {url}")

    async def get(self, url: str, params: dict[str, Any], dependency: str) -> Any:
        self.holdings_calls.append({"url": url, "params": params, "dependency": dependency})
        if self.holdings_error is not None:
            raise self.holdings_error
        if url.endswith("/internal/holdings/consolidation"):
            return dict(self.consolidation_response)
        if url.endswith("/internal/holdings"):
            return dict(self.holdings_response)
        raise AssertionError(f"unexpected downstream GET URL: {url}")

    def _resolve(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("kind") == "capability":
            key = (str(payload.get("module")), str(payload.get("capability")))
            capability = _CAPABILITIES.get(key)
            return dict(capability) if capability else {"error": "capability not found"}
        name = str(payload.get("name"))
        return {"name": name, "deterministic": name in _DETERMINISTIC_TOOLS}

    def audit_event_types(self) -> list[str]:
        return [event["type"] for event in self.audit_events]


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeDownstream:
    stub = FakeDownstream()
    monkeypatch.setattr(clients, "_post", stub.post)
    monkeypatch.setattr(clients, "_get", stub.get)
    return stub


@pytest.fixture
def client(fake: FakeDownstream) -> TestClient:
    from app.main import app, supervisor

    supervisor.store = RunStore()  # isolate run state per test
    return TestClient(app)
