"""L1 — decompose request into a typed task graph (DAG); deterministic templates for known flows."""
from verra_shared import RunRequest


class Planner:
    async def plan(self, req: RunRequest) -> dict:
        # TODO: template lookup (tax_analysis, month_end_close, audit_tie_out) else LLM planner.
        return {"template": req.capability, "steps": [{"id": "s1", "kind": req.capability}]}
