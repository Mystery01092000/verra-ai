"""Portfolio / financial-planning / general-QA flow tests with stubbed downstreams."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi.testclient import TestClient

from tests.conftest import FakeDownstream

PORTFOLIO_INPUT: dict[str, Any] = {
    "clientId": "client-42",
    "taxpayerType": "resident_ordinarily",
    "message": "Review my portfolio for allocation and tax efficiency.",
}

PLANNING_INPUT: dict[str, Any] = {
    **PORTFOLIO_INPUT,
    "assessmentYear": "2025-26",
    "regime": "new",
    "age": 35,
    "income": {"salary": 1_800_000.0},
    "deductions": {"standardDeduction": 75_000.0},
}


def _create_run(
    client: TestClient, capability: str, run_input: dict[str, Any], module: str = "assistant"
) -> str:
    resp = client.post(
        "/internal/runs",
        json={
            "tenantId": "tenant-1",
            "module": module,
            "capability": capability,
            "input": run_input,
        },
    )
    assert resp.status_code == 200, resp.text
    return str(resp.json()["runId"])


def _steps_by_id(body: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {step["id"]: step for step in body["output"]["steps"]}


# ── portfolio_analysis ───────────────────────────────────────────────────────


def test_portfolio_analysis_runs_fetch_consolidate_rules_then_llm(
    client: TestClient, fake: FakeDownstream
) -> None:
    run_id = _create_run(client, "portfolio_analysis", PORTFOLIO_INPUT)
    body = client.get(f"/internal/runs/{run_id}").json()

    steps = _steps_by_id(body)
    assert [step["id"] for step in body["output"]["steps"]] == ["pf1", "pf2", "pf3", "pf4"]

    # Holdings fetched then consolidated via the holdings service (GET, camelCase params).
    assert steps["pf1"]["error"] is None
    assert steps["pf1"]["result"]["holdings"][0]["currentValue"] == 950_000.0
    assert steps["pf2"]["result"]["totalValue"] == 1_350_000.0
    urls = [call["url"] for call in fake.holdings_calls]
    assert urls[0].endswith("/internal/holdings")
    assert urls[1].endswith("/internal/holdings/consolidation")
    assert fake.holdings_calls[0]["params"] == {"tenantId": "tenant-1", "clientId": "client-42"}

    # Rules step returned real portfolio/SEBI-tagged corpus rules with citations.
    rule_ids = [rule["id"] for rule in steps["pf3"]["result"]["rules"]]
    assert rule_ids
    assert set(rule_ids) & {"it-112a", "sebi-mf-riskometer", "sebi-ia-suitability"}

    # Exactly one LLM step ran through the mocked gateway, with the portfolio instruction.
    assert len(fake.model_calls) == 1
    prompt = fake.model_calls[0]["messages"][0]["content"]
    assert "112A" in prompt and "1.25 lakh" in prompt
    assert steps["pf4"]["result"]["content"].startswith("DRAFT")

    # Not approval-gated: capability allows auto-done and everything is cited.
    assert body["status"] == "done"


def test_financial_planning_gates_to_awaiting_approval(
    client: TestClient, fake: FakeDownstream
) -> None:
    run_id = _create_run(client, "financial_planning", PLANNING_INPUT)
    body = client.get(f"/internal/runs/{run_id}").json()

    steps = _steps_by_id(body)
    # Income data present → deterministic tax computation step was included and ran.
    assert steps["fp3"]["error"] is None
    assert steps["fp3"]["result"]["totalTax"] > 0
    assert body["status"] == "awaiting_approval"  # advice-like: approval_required=True


def test_financial_planning_without_income_skips_tax_computation(
    client: TestClient, fake: FakeDownstream
) -> None:
    run_id = _create_run(client, "financial_planning", PORTFOLIO_INPUT)
    body = client.get(f"/internal/runs/{run_id}").json()

    step_ids = [step["id"] for step in body["output"]["steps"]]
    assert "fp3" not in step_ids
    assert step_ids == ["fp1", "fp2", "fp4", "fp5"]
    assert body["status"] == "awaiting_approval"


def test_holdings_outage_degrades_steps_without_crashing_run(
    client: TestClient, fake: FakeDownstream
) -> None:
    fake.holdings_error = httpx.ConnectError("holdings down")
    run_id = _create_run(client, "portfolio_analysis", PORTFOLIO_INPUT)
    body = client.get(f"/internal/runs/{run_id}").json()

    steps = _steps_by_id(body)
    assert "holdings unavailable" in steps["pf1"]["error"]
    assert "holdings unavailable" in steps["pf2"]["error"]
    assert steps["pf1"]["result"] is None
    # Downstream steps still executed; the run completed rather than crashing.
    assert steps["pf3"]["error"] is None
    assert steps["pf4"]["error"] is None
    assert body["status"] in ("done", "awaiting_approval")


# ── general_qa grounded on the rules corpus ──────────────────────────────────


def test_general_qa_retrieves_real_rules_for_rebate_question(
    client: TestClient, fake: FakeDownstream
) -> None:
    run_id = _create_run(
        client,
        "general_qa",
        {"question": "Am I eligible for the Section 87A rebate?"},
    )
    body = client.get(f"/internal/runs/{run_id}").json()

    steps = _steps_by_id(body)
    rules = steps["g1"]["result"]["rules"]
    assert "it-87a" in [rule["id"] for rule in rules]
    # One citation per retrieved rule, carrying the official source string.
    assert len(steps["g1"]["result"]["citations"]) == len(rules)
    assert any("s.87A" in (c["rule"] or "") for c in steps["g1"]["result"]["citations"])
    assert body["status"] == "done"


def test_general_qa_nri_taxpayer_gets_only_nri_and_all_rules(
    client: TestClient, fake: FakeDownstream
) -> None:
    run_id = _create_run(
        client,
        "general_qa",
        {
            "question": "How is interest on my NRE account taxed?",
            "taxpayerType": "non_resident",
        },
    )
    body = client.get(f"/internal/runs/{run_id}").json()

    rules = _steps_by_id(body)["g1"]["result"]["rules"]
    assert rules
    assert all(rule["appliesTo"] in ("nri", "all") for rule in rules)
    assert "it-10-4-nre-interest" in [rule["id"] for rule in rules]
    assert "it-87a" not in [rule["id"] for rule in rules]  # resident-only rule filtered out
