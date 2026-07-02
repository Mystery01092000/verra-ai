"""Run listing + approve/reject endpoint tests (approvals inbox contract)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from tests.conftest import FakeDownstream
from tests.test_run_flow import TAX_ANALYSIS_INPUT, _create_run


def _seed_runs(client: TestClient) -> tuple[str, str]:
    """Create one gated run (tax_analysis) and one completed run (tax_qa)."""
    gated = _create_run(client, "tax_analysis", TAX_ANALYSIS_INPUT)
    done = _create_run(client, "tax_qa", {"question": "What is Section 80D?"})
    return gated, done


def test_list_runs_newest_first_with_summary_fields(
    client: TestClient, fake: FakeDownstream
) -> None:
    gated, done = _seed_runs(client)

    items: list[dict[str, Any]] = client.get("/internal/runs").json()
    assert [item["runId"] for item in items] == [done, gated]  # newest first
    first = items[0]
    assert set(first) >= {"runId", "status", "capability", "createdAt", "citationsCount"}
    assert first["capability"] == "tax_qa"
    assert first["citationsCount"] > 0
    assert first["summary"].startswith("DRAFT")

    limited = client.get("/internal/runs", params={"limit": 1}).json()
    assert len(limited) == 1


def test_list_runs_status_filter_accepts_needs_approval_alias(
    client: TestClient, fake: FakeDownstream
) -> None:
    gated, _done = _seed_runs(client)

    items = client.get("/internal/runs", params={"status": "needs_approval"}).json()
    assert [item["runId"] for item in items] == [gated]
    assert items[0]["status"] == "awaiting_approval"

    # Canonical enum value works too; unknown values are rejected.
    canonical = client.get("/internal/runs", params={"status": "awaiting_approval"}).json()
    assert [item["runId"] for item in canonical] == [gated]
    assert client.get("/internal/runs", params={"status": "bogus"}).status_code == 422


def test_approve_transitions_run_and_writes_audit_event(
    client: TestClient, fake: FakeDownstream
) -> None:
    gated, _done = _seed_runs(client)

    resp = client.post(
        f"/internal/runs/{gated}/approve",
        json={"approver": "ca@firm.example", "note": "figures verified"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
    assert client.get(f"/internal/runs/{gated}").json()["status"] == "done"

    approved = [e for e in fake.audit_events if e["type"] == "run_approved"]
    assert len(approved) == 1
    assert approved[0]["data"]["approver"] == "ca@firm.example"
    assert approved[0]["data"]["run_id"] == gated

    # Approving twice is a state conflict; unknown runs are 404.
    second = client.post(f"/internal/runs/{gated}/approve", json={"approver": "ca@firm.example"})
    assert second.status_code == 409
    missing = client.post("/internal/runs/nope/approve", json={"approver": "ca@firm.example"})
    assert missing.status_code == 404


def test_reject_transitions_run_and_writes_audit_event(
    client: TestClient, fake: FakeDownstream
) -> None:
    gated, done = _seed_runs(client)

    resp = client.post(
        f"/internal/runs/{gated}/reject",
        json={"approver": "ca@firm.example", "note": "missing Form 26AS"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"

    rejected = [e for e in fake.audit_events if e["type"] == "run_rejected"]
    assert len(rejected) == 1
    assert rejected[0]["data"]["approver"] == "ca@firm.example"

    # A run that is not awaiting approval cannot be rejected.
    conflict = client.post(f"/internal/runs/{done}/reject", json={"approver": "ca@firm.example"})
    assert conflict.status_code == 409
    missing = client.post("/internal/runs/nope/reject", json={"approver": "ca@firm.example"})
    assert missing.status_code == 404
