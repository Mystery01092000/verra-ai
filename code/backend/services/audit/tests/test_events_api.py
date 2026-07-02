"""Endpoint tests for the audit service (hash-chained event log)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from app import main as audit_main
from app.config import settings
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(settings, "AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    with TestClient(audit_main.app) as test_client:
        yield test_client


def _post_event(client: TestClient, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "type": "run.completed",
        "data": {"run_id": "r1"},
        "tenant_id": "t1",
        "agent": "executor",
    }
    payload.update(overrides)
    response = client.post("/internal/events", json=payload)
    assert response.status_code == 200
    return dict(response.json())


def test_post_event_returns_full_receipt(client: TestClient) -> None:
    receipt = _post_event(client)
    assert receipt["logged"] is True
    assert receipt["prev_hash"] == "0" * 64
    assert isinstance(receipt["event_id"], str) and receipt["event_id"]
    assert isinstance(receipt["hash"], str) and len(receipt["hash"]) == 64
    assert isinstance(receipt["ts"], str) and receipt["ts"]


def test_receipts_chain_across_requests(client: TestClient) -> None:
    first = _post_event(client)
    second = _post_event(client, type="run.failed")
    assert second["prev_hash"] == first["hash"]


def test_list_events_limit_and_tenant_filter(client: TestClient) -> None:
    for n in range(5):
        _post_event(client, data={"n": n}, tenant_id="t1" if n % 2 == 0 else "t2")

    response = client.get("/internal/events", params={"tenant_id": "t1"})
    body = response.json()
    assert response.status_code == 200
    assert body["count"] == 3
    assert all(event["tenant_id"] == "t1" for event in body["events"])

    limited = client.get("/internal/events", params={"limit": 2}).json()
    assert limited["count"] == 2
    assert [event["data"]["n"] for event in limited["events"]] == [3, 4]


def test_verify_endpoint_ok_and_after_tamper(client: TestClient, tmp_path: Path) -> None:
    _post_event(client)
    _post_event(client)
    assert client.get("/internal/verify").json() == {
        "ok": True,
        "first_bad_index": None,
        "length": 2,
    }

    log_path = tmp_path / "audit.jsonl"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    log_path.write_text(
        lines[0].replace("run.completed", "run.tampered") + "\n" + lines[1] + "\n",
        encoding="utf-8",
    )
    body = client.get("/internal/verify").json()
    assert body["ok"] is False
    assert body["first_bad_index"] == 0


def test_v1_events_appends_to_chain(client: TestClient) -> None:
    internal = _post_event(client)
    response = client.post(
        "/v1/events", json={"type": "approval.granted", "data": {}, "tenant_id": "t1"}
    )
    assert response.status_code == 200
    receipt = response.json()
    assert receipt["logged"] is True
    assert receipt["prev_hash"] == internal["hash"]


def test_invalid_event_rejected(client: TestClient) -> None:
    response = client.post("/internal/events", json={"type": "", "data": {}})
    assert response.status_code == 422


def test_no_update_or_delete_endpoints(client: TestClient) -> None:
    assert client.put("/internal/events", json={}).status_code == 405
    assert client.delete("/internal/events").status_code == 405
