"""L3 — run steps/tool calls: parallelism, timeouts, retries+backoff, breakers, idempotency."""

from __future__ import annotations

from typing import Any

import httpx
from verra_shared.infra.circuit_breaker import CircuitBreakerOpenError
from verra_shared.infra.logging import get_logger
from verra_shared.rules import search_rules
from verra_shared.tax import (
    AdvanceTaxInput,
    HRAInput,
    SalaryExemptionsInput,
    TaxInput,
    compare_regimes,
    compute_advance_tax,
    compute_hra_exemption,
    compute_salary_exemptions,
    compute_tax_liability_from_input,
    reconcile_tds,
)
from verra_shared.tax.reconcile import TDSEntry

from .. import clients
from .citations import extract_citations_from_text, normalize_citations
from .prompts import SYSTEM_PROMPT, build_messages

logger = get_logger(__name__)


def _dispatch_tax_tool(tool: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Call deterministic tax calculators directly (same process, no HTTP overhead)."""
    if tool == "tax:compute_tax_liability":
        return compute_tax_liability_from_input(TaxInput(**inputs)).model_dump(by_alias=True)

    if tool == "tax:compare_regimes":
        inp = TaxInput(**inputs)
        return compare_regimes(
            assessment_year=inp.assessment_year,
            taxpayer_type=inp.taxpayer_type,
            age=inp.age,
            income=inp.income,
            deductions=inp.deductions,
            tds_tcs_credit=inp.tds_tcs_credit,
            advance_tax_paid=inp.advance_tax_paid,
            foreign_tax_credit=inp.foreign_tax_credit,
        ).model_dump(by_alias=True)

    if tool == "tax:compute_salary_exemptions":
        return compute_salary_exemptions(SalaryExemptionsInput(**inputs)).model_dump(by_alias=True)

    if tool == "tax:compute_hra_exemption":
        return compute_hra_exemption(HRAInput(**inputs)).model_dump(by_alias=True)

    if tool == "tax:compute_advance_tax":
        return compute_advance_tax(AdvanceTaxInput(**inputs)).model_dump(by_alias=True)

    if tool == "tax:reconcile_tds":
        form16 = [TDSEntry(**e) for e in inputs.get("form16Entries", [])]
        f26as = [TDSEntry(**e) for e in inputs.get("form26asEntries", [])]
        ais = [TDSEntry(**e) for e in inputs.get("aisEntries", [])]
        return reconcile_tds(
            form16_entries=form16,
            form26as_entries=f26as,
            ais_entries=ais,
            variance_threshold=inputs.get("varianceThreshold", 1.0),
        ).model_dump(by_alias=True)

    raise ValueError(f"Unknown tax tool: {tool}")


# Tools that are pure deterministic Python functions (no LLM call needed).
_DETERMINISTIC_TOOLS: frozenset[str] = frozenset(
    {
        "tax:compute_tax_liability",
        "tax:compare_regimes",
        "tax:compute_salary_exemptions",
        "tax:compute_hra_exemption",
        "tax:compute_advance_tax",
        "tax:reconcile_tds",
    }
)

# Tools served by the holdings service over HTTP (degrade to step error on outage).
_HOLDINGS_TOOLS: frozenset[str] = frozenset({"holdings:fetch", "holdings:consolidate"})

# Rules retrieval is served in-process from the shared regulatory rules corpus.
_RULES_TOOL = "tax:retrieve_tax_rules"

# Step kinds / named tools that require model-gateway reasoning.
_LLM_STEP_KINDS: frozenset[str] = frozenset({"opportunities", "answer", "draft"})
_LLM_TOOLS: frozenset[str] = frozenset({"tax:generate_draft_output"})

_DEFAULT_MODEL_TIER = "medium"
_LLM_MAX_TOKENS = 2048


class Executor:
    async def execute(
        self,
        step: dict[str, Any],
        route: dict[str, Any],
        prior_steps: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        tool: str | None = step.get("tool")
        kind: str = str(step.get("kind", "unknown"))

        if tool == _RULES_TOOL:
            return self._execute_rules_retrieval(step)

        if tool in _HOLDINGS_TOOLS:
            return await self._execute_holdings(step, str(tool))

        if tool in _DETERMINISTIC_TOOLS:
            return self._execute_deterministic(step, str(tool))

        if tool in _LLM_TOOLS or (tool is None and kind in _LLM_STEP_KINDS):
            return await self._execute_llm(step, route, prior_steps or [])

        # Retrieval / not-yet-implemented tools: succeed with an explicit empty payload
        # so downstream steps can proceed (no fabricated data).
        return {
            "step": step,
            "result": {"note": f"tool '{tool}' not yet implemented", "documents": []},
            "citations": [],
        }

    def _execute_rules_retrieval(self, step: dict[str, Any]) -> dict[str, Any]:
        """Search the shared regulatory rules corpus (deterministic, no LLM).

        Query comes from step inputs (`query`) or the run's user message
        (`question`/`message`); the taxpayer type narrows applies_to.
        """
        inputs: dict[str, Any] = step.get("input", {})
        query = str(inputs.get("query") or inputs.get("question") or inputs.get("message") or "")
        taxpayer_type = inputs.get("taxpayerType") or inputs.get("taxpayer_type")
        regulator = inputs.get("regulator")
        raw_tags = inputs.get("tags")
        tags = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else None

        rules = search_rules(
            query,
            taxpayer_type=str(taxpayer_type) if taxpayer_type else None,
            regulator=str(regulator) if regulator else None,
            tags=tags,
        )
        citations = [{"doc_id": rule.id, "page": None, "rule": rule.source} for rule in rules]
        result = {
            "rules": [rule.model_dump(by_alias=True) for rule in rules],
            "citations": citations,
        }
        return {"step": step, "result": result, "citations": citations}

    async def _execute_holdings(self, step: dict[str, Any], tool: str) -> dict[str, Any]:
        """Call the holdings service; an outage degrades the step, never the run."""
        inputs: dict[str, Any] = step.get("input", {})
        tenant_id = str(inputs.get("tenantId") or inputs.get("tenant_id") or "")
        client_id = str(inputs.get("clientId") or inputs.get("client_id") or "")
        try:
            if tool == "holdings:fetch":
                result = await clients.fetch_holdings(tenant_id, client_id)
            else:
                raw_income = inputs.get("annualIncome")
                annual_income = float(raw_income) if isinstance(raw_income, int | float) else None
                result = await clients.fetch_consolidation(
                    tenant_id, client_id, annual_income=annual_income
                )
        except (httpx.HTTPError, CircuitBreakerOpenError) as exc:
            logger.warning(
                "holdings_call_failed", tool=tool, step_id=step.get("id"), error=str(exc)
            )
            return {
                "step": step,
                "result": None,
                "citations": [],
                "error": f"holdings unavailable: {exc}",
            }
        raw_citations = result.get("citations")
        citations = (
            normalize_citations([c for c in raw_citations if isinstance(c, dict)])
            if isinstance(raw_citations, list)
            else []
        )
        return {"step": step, "result": result, "citations": citations}

    def _execute_deterministic(self, step: dict[str, Any], tool: str) -> dict[str, Any]:
        inputs: dict[str, Any] = step.get("input", {})
        try:
            result = _dispatch_tax_tool(tool, inputs)
        except (ValueError, TypeError) as exc:
            logger.warning("tax_tool_failed", tool=tool, step_id=step.get("id"), error=str(exc))
            return {"step": step, "result": None, "citations": [], "error": str(exc)}
        citations = normalize_citations(result.get("citations", []))
        return {"step": step, "result": result, "citations": citations}

    async def _execute_llm(
        self,
        step: dict[str, Any],
        route: dict[str, Any],
        prior_steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run an agent-reasoning step through the model gateway (POST /internal/complete)."""
        messages = build_messages(step, prior_steps)
        model_tier = str(route.get("model_tier") or _DEFAULT_MODEL_TIER)
        try:
            resp = await clients.call_model_gateway(
                messages=messages,
                system=SYSTEM_PROMPT,
                model_tier=model_tier,
                max_tokens=_LLM_MAX_TOKENS,
            )
        except (httpx.HTTPError, CircuitBreakerOpenError) as exc:
            logger.warning("model_gateway_call_failed", step_id=step.get("id"), error=str(exc))
            return {
                "step": step,
                "result": None,
                "citations": [],
                "llm": True,
                "error": f"model_gateway unavailable: {exc}",
            }

        if resp.get("error"):
            logger.warning("model_gateway_error", step_id=step.get("id"), error=str(resp["error"]))
            return {
                "step": step,
                "result": None,
                "citations": [],
                "llm": True,
                "error": str(resp["error"]),
            }

        content = str(resp.get("content", ""))
        return {
            "step": step,
            "result": {
                "content": content,
                "provider": resp.get("provider"),
                "model": resp.get("model"),
            },
            "citations": extract_citations_from_text(content),
            "usage": resp.get("usage") or {},
            "llm": True,
        }
