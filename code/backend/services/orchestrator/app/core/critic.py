"""L4 — verify: grounding/citations, schema, numeric checks, confidence; gate if consequential."""

from __future__ import annotations

from typing import Any

APPROVAL_CONFIDENCE_THRESHOLD = 0.7

_WEIGHT_STEP_SUCCESS = 0.45
_WEIGHT_MONEY_CITED = 0.35
_WEIGHT_LLM_GROUNDED = 0.2


def _is_success(step_output: dict[str, Any]) -> bool:
    return step_output.get("error") is None and step_output.get("result") is not None


def _has_money_figures(value: Any) -> bool:
    """True if a result payload carries numeric figures (recursively)."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int | float):
        return True
    if isinstance(value, dict):
        return any(_has_money_figures(v) for v in value.values())
    if isinstance(value, list | tuple):
        return any(_has_money_figures(v) for v in value)
    return False


class Critic:
    async def verify(
        self,
        step_outputs: list[dict[str, Any]],
        capability: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Score a completed run from real signals and decide whether a human must approve."""
        total = len(step_outputs)
        successes = [s for s in step_outputs if _is_success(s)]
        success_fraction = len(successes) / total if total else 0.0

        # Money-bearing deterministic results must carry citations.
        money_steps = [
            s for s in successes if not s.get("llm") and _has_money_figures(s.get("result"))
        ]
        money_cited_fraction = (
            len([s for s in money_steps if s.get("citations")]) / len(money_steps)
            if money_steps
            else 1.0
        )

        # Every LLM step must have succeeded AND cite its sources.
        llm_steps = [s for s in step_outputs if s.get("llm")]
        llm_grounded = all(_is_success(s) and s.get("citations") for s in llm_steps)

        confidence = round(
            _WEIGHT_STEP_SUCCESS * success_fraction
            + _WEIGHT_MONEY_CITED * money_cited_fraction
            + _WEIGHT_LLM_GROUNDED * (1.0 if llm_grounded else 0.0),
            3,
        )

        approval_required = bool((capability or {}).get("approval_required"))
        # Ungrounded LLM output is a hard gate: uncited answers never ship unreviewed.
        needs_approval = (
            approval_required or not llm_grounded or confidence < APPROVAL_CONFIDENCE_THRESHOLD
        )

        return {
            "ok": success_fraction == 1.0 and llm_grounded,
            "confidence": confidence,
            "needs_approval": needs_approval,
            "approval_required": approval_required,
            "success_fraction": round(success_fraction, 3),
            "money_cited_fraction": round(money_cited_fraction, 3),
            "llm_grounded": llm_grounded,
        }
