"""End-to-end supervisor loop tests with stubbed downstream services."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi.testclient import TestClient
from tests.conftest import FakeDownstream

TAX_ANALYSIS_INPUT: dict[str, Any] = {
    "assessmentYear": "2025-26",
    "taxpayerType": "resident_ordinarily",
    "regime": "new",
    "age": 35,
    "income": {"salary": 1_500_000.0},
    "deductions": {"standardDeduction": 75_000.0, "section80c": 150_000.0},
}


def _create_run(client: TestClient, capability: str, run_input: dict[str, Any]) -> str:
    resp = client.post(
        "/internal/runs",
        json={
            "tenantId": "tenant-1",
            "module": "tax",
            "capability": capability,
            "input": run_input,
        },
    )
    assert resp.status_code == 200, resp.text
    return str(resp.json()["runId"])


def test_tax_analysis_run_executes_deterministic_and_llm_steps(
    client: TestClient, fake: FakeDownstream
) -> None:
    run_id = _create_run(client, "tax_analysis", TAX_ANALYSIS_INPUT)
    body = client.get(f"/internal/runs/{run_id}").json()

    steps = {step["id"]: step for step in body["output"]["steps"]}
    assert steps["p3"]["error"] is None
    assert steps["p3"]["result"]["totalTax"] > 0  # deterministic calculator ran
    assert steps["p4"]["result"]["recommendedRegime"] in ("old", "new")

    # LLM steps (p5 opportunities, p6 draft) went through the mocked model gateway.
    assert len(fake.model_calls) == 2
    assert all(call["messages"] for call in fake.model_calls)
    assert all("cite" in call["system"].lower() for call in fake.model_calls)
    assert steps["p5"]["result"]["content"].startswith("DRAFT")
    assert steps["p6"]["result"]["provider"] == "stub"

    # Model tiers came from the router decision (opportunities=medium, draft=large).
    assert [call["model_tier"] for call in fake.model_calls] == ["medium", "large"]

    # Citations from calculators + LLM output are aggregated on the run.
    assert any(c["rule"] for c in body["citations"])


def test_run_status_endpoint_returns_real_state(client: TestClient, fake: FakeDownstream) -> None:
    run_id = _create_run(client, "tax_qa", {"question": "Can I claim Section 80C in new regime?"})
    body = client.get(f"/internal/runs/{run_id}").json()

    assert body["runId"] == run_id
    assert body["status"] == "done"  # approval not required, confidence high
    assert body["output"]["final"]["content"].startswith("DRAFT")
    # Cost accumulated from mocked model usage (one LLM step).
    assert body["cost"]["tokensIn"] == 120
    assert body["cost"]["tokensOut"] == 80
    assert body["cost"]["usd"] > 0

    assert client.get("/internal/runs/does-not-exist").status_code == 404


def test_guardrails_deny_blocks_step(client: TestClient, fake: FakeDownstream) -> None:
    fake.deny_when = "opportunities"
    run_id = _create_run(client, "tax_analysis", TAX_ANALYSIS_INPUT)
    body = client.get(f"/internal/runs/{run_id}").json()

    steps = {step["id"]: step for step in body["output"]["steps"]}
    assert steps["p5"]["error"] == "blocked_by_guardrails"
    assert steps["p5"]["result"] is None
    # Only the draft step reached the model gateway; the blocked step never did.
    assert len(fake.model_calls) == 1
    # Guardrails were consulted for every step.
    assert len(fake.guardrail_calls) == 6


def test_audit_events_written_per_step_and_on_completion(
    client: TestClient, fake: FakeDownstream
) -> None:
    run_id = _create_run(client, "tax_qa", {"question": "What is Section 80D?"})

    types = fake.audit_event_types()
    assert types == ["run_started", "run_step_completed", "run_step_completed", "run_completed"]
    assert all(event["agent"] == "orchestrator" for event in fake.audit_events)
    assert all(event["tenant_id"] == "tenant-1" for event in fake.audit_events)
    assert fake.audit_events[-1]["data"]["run_id"] == run_id
    assert fake.audit_events[-1]["data"]["status"] == "done"


def test_needs_approval_when_capability_requires_it(
    client: TestClient, fake: FakeDownstream
) -> None:
    run_id = _create_run(client, "tax_analysis", TAX_ANALYSIS_INPUT)
    body = client.get(f"/internal/runs/{run_id}").json()
    # All steps succeeded with citations, but tax_analysis is approval_required.
    assert body["status"] == "awaiting_approval"


def test_model_gateway_failure_degrades_step_not_run(
    client: TestClient, fake: FakeDownstream
) -> None:
    fake.model_error = httpx.ConnectError("boom")
    run_id = _create_run(client, "tax_qa", {"question": "What is Section 80D?"})
    body = client.get(f"/internal/runs/{run_id}").json()

    steps = {step["id"]: step for step in body["output"]["steps"]}
    assert "model_gateway unavailable" in steps["q2"]["error"]
    # The run itself did not crash; low confidence gates it to a human.
    assert body["status"] == "awaiting_approval"
