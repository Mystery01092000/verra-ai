"""Tests for registry service."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json()["status"] == "ok"


def test_resolve_capability() -> None:
    r = client.post(
        "/v1/resolve", json={"kind": "capability", "module": "tax", "capability": "tax_analysis"}
    )
    assert r.status_code == 200
    assert r.json()["capability"] == "tax_analysis"


def test_resolve_tool() -> None:
    r = client.post("/v1/resolve", json={"kind": "tool", "name": "tax:compute_tax_liability"})
    assert r.status_code == 200
    assert r.json()["name"] == "compute_tax_liability"
    assert r.json()["deterministic"] is True


def test_list_capabilities() -> None:
    r = client.get("/v1/capabilities?module=tax")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_resolve_portfolio_analysis_capability() -> None:
    r = client.post(
        "/v1/resolve",
        json={"kind": "capability", "module": "assistant", "capability": "portfolio_analysis"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["approval_required"] is False
    assert body["model_tier"] == "medium"
    assert body["required_tools"] == [
        "holdings:fetch",
        "holdings:consolidate",
        "tax:retrieve_tax_rules",
    ]


def test_resolve_financial_planning_requires_approval() -> None:
    r = client.post(
        "/v1/resolve",
        json={"kind": "capability", "module": "assistant", "capability": "financial_planning"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["approval_required"] is True  # advice-like output
    assert body["model_tier"] == "large"


def test_resolve_general_qa_capability() -> None:
    r = client.post(
        "/v1/resolve",
        json={"kind": "capability", "module": "assistant", "capability": "general_qa"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["approval_required"] is False
    assert body["model_tier"] == "medium"
    assert "tax:retrieve_tax_rules" in body["required_tools"]


def test_resolve_holdings_tools() -> None:
    fetch = client.post("/v1/resolve", json={"kind": "tool", "name": "holdings:fetch"}).json()
    assert fetch["deterministic"] is True
    assert set(fetch["input_schema"]["required"]) == {"tenantId", "clientId"}

    consolidate = client.post(
        "/v1/resolve", json={"kind": "tool", "name": "holdings:consolidate"}
    ).json()
    assert consolidate["deterministic"] is True
    assert "annualIncome" in consolidate["input_schema"]["properties"]


def test_list_assistant_capabilities() -> None:
    r = client.get("/v1/capabilities?module=assistant")
    assert r.status_code == 200
    names = {c["capability"] for c in r.json()}
    assert {"portfolio_analysis", "financial_planning", "general_qa"} <= names
