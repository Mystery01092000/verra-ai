"""L2 — select agent + model tier + tools by capability and cost/latency/quality policy."""

from __future__ import annotations

from typing import Any

from ..clients import lookup_registry


def _pick_model_tier(step_kind: str, tool_name: str | None) -> str:
    """Choose cheapest sufficient model tier for this step."""
    if tool_name and "compute_" in tool_name:
        return "small"  # deterministic calculators need no model
    if step_kind in ("answer", "draft"):
        return "large"
    if step_kind == "opportunities":
        return "medium"
    return "small"


async def _resolve_tool(tool_name: str) -> dict[str, Any] | None:
    """Fetch tool manifest from registry service via circuit-breaker client."""
    try:
        data = await lookup_registry(tool_name)
        if "error" in data:
            return None
        return data
    except Exception:
        return None


class Router:
    async def route(self, step: dict[str, Any]) -> dict[str, Any]:
        """Resolve a plan step to an agent + model tier + tool manifest."""
        tool_name: str | None = step.get("tool")
        kind: str = step.get("kind", "unknown")

        tool_manifest: dict[str, Any] | None = None
        if tool_name:
            tool_manifest = await _resolve_tool(tool_name)

        model_tier = _pick_model_tier(kind, tool_name)

        return {
            "agent": f"{kind}-agent@latest",
            "model_tier": model_tier,
            "tool": tool_manifest,
            "reason": "policy:cheapest-sufficient",
        }
