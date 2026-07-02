"""L1 — decompose request into a typed task graph (DAG); deterministic templates for known flows."""

from typing import Any

from verra_shared import RunRequest

TEMPLATES: dict[str, dict[str, Any]] = {
    "tax_analysis": {
        "template": "tax_analysis",
        "description": "End-to-end Indian tax analysis for residents and NRIs.",
        "steps": [
            {
                "id": "p1",
                "kind": "retrieve_context",
                "tool": "tax:retrieve_client_docs",
                "description": "Fetch uploaded tax documents for the client/AY.",
            },
            {
                "id": "p2",
                "kind": "retrieve_rules",
                "tool": "tax:retrieve_tax_rules",
                "description": "Fetch versioned tax rules for AY 2025-26.",
            },
            {
                "id": "p3",
                "kind": "compute",
                "tool": "tax:compute_tax_liability",
                "description": "Compute tax liability deterministically.",
            },
            {
                "id": "p4",
                "kind": "compare",
                "tool": "tax:compare_regimes",
                "description": "Compare old vs new regime.",
            },
            {
                "id": "p5",
                "kind": "opportunities",
                "tool": None,
                "description": (
                    "Identify deductions, credits, and timing opportunities (agent reasoning)."
                ),
            },
            {
                "id": "p6",
                "kind": "draft",
                "tool": None,
                "description": "Generate draft computation report (awaiting approval).",
            },
        ],
    },
    "tax_qa": {
        "template": "tax_qa",
        "description": "Answer Indian tax rules and planning questions with citations.",
        "steps": [
            {
                "id": "q1",
                "kind": "retrieve_rules",
                "tool": "tax:retrieve_tax_rules",
                "description": "Retrieve relevant tax rules.",
            },
            {
                "id": "q2",
                "kind": "answer",
                "tool": None,
                "description": "Generate cited answer with guardrails.",
            },
        ],
    },
    "portfolio_analysis": {
        "template": "portfolio_analysis",
        "description": "Portfolio review: consolidate holdings, ground on rules, draft insights.",
        "steps": [
            {
                "id": "pf1",
                "kind": "retrieve_context",
                "tool": "holdings:fetch",
                "description": "Fetch client holdings across accounts.",
            },
            {
                "id": "pf2",
                "kind": "consolidate",
                "tool": "holdings:consolidate",
                "description": "Consolidate holdings into a portfolio view (deterministic).",
            },
            {
                "id": "pf3",
                "kind": "retrieve_rules",
                "tool": "tax:retrieve_tax_rules",
                "input": {"tags": ["portfolio", "sebi"]},
                "description": "Retrieve portfolio/SEBI rules grounding the insights.",
            },
            {
                "id": "pf4",
                "kind": "opportunities",
                "tool": None,
                "instruction": "portfolio_insights",
                "description": (
                    "Allocation observations, tax-efficiency opportunities, and coverage "
                    "gaps — each tied to a retrieved rule (agent reasoning)."
                ),
            },
        ],
    },
    "financial_planning": {
        "template": "financial_planning",
        "description": "Goal-based financial plan draft grounded on holdings + rules.",
        "steps": [
            {
                "id": "fp1",
                "kind": "retrieve_context",
                "tool": "holdings:fetch",
                "description": "Fetch client holdings across accounts.",
            },
            {
                "id": "fp2",
                "kind": "consolidate",
                "tool": "holdings:consolidate",
                "description": "Consolidate holdings into a portfolio view (deterministic).",
            },
            {
                "id": "fp3",
                "kind": "compute",
                "tool": "tax:compute_tax_liability",
                "description": "Compute tax liability deterministically (income data provided).",
            },
            {
                "id": "fp4",
                "kind": "retrieve_rules",
                "tool": "tax:retrieve_tax_rules",
                "description": "Retrieve regulatory rules grounding the plan.",
            },
            {
                "id": "fp5",
                "kind": "draft",
                "tool": None,
                "instruction": "financial_plan",
                "description": "Draft a goal-based financial plan (awaiting approval).",
            },
        ],
    },
    "general_qa": {
        "template": "general_qa",
        "description": "Answer general finance/regulatory questions grounded on the rules corpus.",
        "steps": [
            {
                "id": "g1",
                "kind": "retrieve_rules",
                "tool": "tax:retrieve_tax_rules",
                "description": "Retrieve relevant regulatory rules.",
            },
            {
                "id": "g2",
                "kind": "answer",
                "tool": None,
                "description": "Generate cited answer with guardrails.",
            },
        ],
    },
    "tax_scenario": {
        "template": "tax_scenario",
        "description": "Compare tax outcomes under changed assumptions.",
        "steps": [
            {
                "id": "s1",
                "kind": "clone_profile",
                "tool": "tax:build_scenario",
                "description": "Clone base profile and apply assumption overrides.",
            },
            {
                "id": "s2",
                "kind": "compute",
                "tool": "tax:compute_tax_liability",
                "description": "Recompute tax under scenario.",
            },
            {
                "id": "s3",
                "kind": "compare",
                "tool": "tax:compare_regimes",
                "description": "Compare scenario vs baseline.",
            },
        ],
    },
}


def _bind_inputs(template: dict[str, Any], req: RunRequest) -> dict[str, Any]:
    """Return a new plan with the request input bound to each step (templates untouched)."""
    steps = [
        {**step, "input": {"tenantId": req.tenant_id, **req.input, **step.get("input", {})}}
        for step in template["steps"]
    ]
    return {**template, "steps": steps}


def _has_income_data(run_input: dict[str, object]) -> bool:
    """True when the request carries usable income heads for the tax calculator."""
    income = run_input.get("income")
    if not isinstance(income, dict):
        return False
    return any(
        isinstance(v, int | float) and not isinstance(v, bool) and v > 0 for v in income.values()
    )


def _select_template(req: RunRequest) -> dict[str, Any] | None:
    template = TEMPLATES.get(req.capability)
    if template is None:
        return None
    if req.capability == "financial_planning" and not _has_income_data(req.input):
        # No income data: skip the deterministic tax computation step.
        steps = [s for s in template["steps"] if s.get("tool") != "tax:compute_tax_liability"]
        return {**template, "steps": steps}
    return template


class Planner:
    async def plan(self, req: RunRequest) -> dict[str, Any]:
        template = _select_template(req)
        if template is not None:
            return _bind_inputs(template, req)
        # Fallback: single-step generic plan.
        return {
            "template": req.capability,
            "steps": [{"id": "s1", "kind": req.capability, "input": dict(req.input)}],
        }
