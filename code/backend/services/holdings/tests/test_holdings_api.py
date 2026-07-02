"""Endpoint tests for the holdings service (CRUD, masking, consolidation, errors)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from app import main as holdings_main
from app.config import settings
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(settings, "HOLDINGS_STORE_PATH", str(tmp_path / "holdings.jsonl"))
    with TestClient(holdings_main.app) as test_client:
        yield test_client


_QUERY = {"tenantId": "t1", "clientId": "c1"}


def _post_holding(client: TestClient, **overrides: object) -> dict[str, Any]:
    payload: dict[str, object] = {
        "tenantId": "t1",
        "clientId": "c1",
        "type": "mutual_fund",
        "name": "Index fund",
        "currentValue": 100000,
    }
    payload.update(overrides)
    response = client.post("/internal/holdings", json=payload)
    assert response.status_code == 200, response.text
    return dict(response.json())


def test_crud_roundtrip(client: TestClient) -> None:
    created = _post_holding(client)
    assert created["id"]
    assert created["tenantId"] == "t1"
    assert created["currentValue"] == 100000

    listed = client.get("/internal/holdings", params=_QUERY).json()
    assert listed["count"] == 1
    assert listed["holdings"][0]["id"] == created["id"]

    deleted = client.delete(f"/internal/holdings/{created['id']}", params=_QUERY)
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True, "holdingId": created["id"]}
    assert client.get("/internal/holdings", params=_QUERY).json()["count"] == 0


def test_account_number_masked_in_create_and_list(client: TestClient) -> None:
    created = _post_holding(client, folioOrAccount="FOLIO-123456789")
    assert created["folioOrAccount"] == "****6789"
    assert "123456789" not in str(created)

    listed = client.get("/internal/holdings", params=_QUERY).json()
    assert listed["holdings"][0]["folioOrAccount"] == "****6789"


def test_full_account_number_never_persisted(client: TestClient, tmp_path: Path) -> None:
    _post_holding(client, folioOrAccount="SECRET-987654321")
    raw = (tmp_path / "holdings.jsonl").read_text(encoding="utf-8")
    assert "SECRET-987654321" not in raw
    assert "****4321" in raw


def test_persistence_replay_across_restart(client: TestClient) -> None:
    created = _post_holding(client)
    _post_holding(client, name="Second", type="gold")
    client.delete(f"/internal/holdings/{created['id']}", params=_QUERY)

    holdings_main._store = None  # simulate process restart → replay from JSONL
    listed = client.get("/internal/holdings", params=_QUERY).json()
    assert listed["count"] == 1
    assert listed["holdings"][0]["name"] == "Second"


def test_consolidation_via_api(client: TestClient) -> None:
    _post_holding(client, type="stock", name="Single stock", currentValue=800000)
    _post_holding(client, type="cash", name="Savings", currentValue=200000)
    _post_holding(
        client,
        type="loan_home",
        name="Home loan",
        currentValue=0,
        outstandingAmount=300000,
    )

    response = client.get(
        "/internal/holdings/consolidation", params={**_QUERY, "annualIncome": 1000000}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["totalAssets"] == 1000000
    assert body["totalLiabilities"] == 300000
    assert body["netWorth"] == 700000
    assert sum(row["percentage"] for row in body["breakdown"]) == pytest.approx(100.0)

    codes = {flag["code"] for flag in body["flags"]}
    assert {"concentration", "underinsured_life", "no_health_cover"} <= codes
    assert all(flag["citation"]["source"] for flag in body["flags"])
    assert body["citations"]


def test_consolidation_empty_portfolio(client: TestClient) -> None:
    body = client.get("/internal/holdings/consolidation", params=_QUERY).json()
    assert body["totalAssets"] == 0
    assert body["flags"] == []


def test_delete_unknown_holding_404(client: TestClient) -> None:
    response = client.delete("/internal/holdings/nope", params=_QUERY)
    assert response.status_code == 404


def test_delete_scoped_to_tenant_and_client(client: TestClient) -> None:
    created = _post_holding(client)
    response = client.delete(
        f"/internal/holdings/{created['id']}",
        params={"tenantId": "other", "clientId": "c1"},
    )
    assert response.status_code == 404  # not visible outside its tenant


def test_negative_current_value_rejected(client: TestClient) -> None:
    response = client.post(
        "/internal/holdings",
        json={**_QUERY, "type": "stock", "name": "Bad", "currentValue": -1},
    )
    assert response.status_code == 422


def test_missing_required_fields_rejected(client: TestClient) -> None:
    assert client.post("/internal/holdings", json={"name": "No tenant"}).status_code == 422
    assert (
        client.post(
            "/internal/holdings",
            json={**_QUERY, "type": "not_a_type", "name": "Bad type", "currentValue": 1},
        ).status_code
        == 422
    )


def test_consolidation_requires_tenant_and_client(client: TestClient) -> None:
    assert client.get("/internal/holdings/consolidation").status_code == 422
    assert client.get("/internal/holdings", params={"tenantId": "t1"}).status_code == 422
