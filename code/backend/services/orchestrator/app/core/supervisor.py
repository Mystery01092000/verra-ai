"""Run lifecycle state machine (ADR-0005). In-memory today; Temporal-backed later."""

from __future__ import annotations

import json
import uuid
from typing import Any

from verra_shared import RunRequest, RunStatus
from verra_shared.infra.logging import get_logger

from .. import clients
from .critic import Critic
from .executor import Executor
from .planner import Planner
from .router import Router
from .run_store import RunState, RunStore

logger = get_logger(__name__)


class RunNotFoundError(KeyError):
    """Raised when a run_id is not present in the run store."""


class InvalidRunStateError(Exception):
    """Raised when an approval/rejection is attempted from the wrong state."""

    def __init__(self, current_status: RunStatus) -> None:
        self.current_status = current_status
        super().__init__(f"run is in state '{current_status}'")


def _build_output(step_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    entries = [
        {
            "id": out.get("step", {}).get("id"),
            "kind": out.get("step", {}).get("kind"),
            "tool": out.get("step", {}).get("tool"),
            "result": out.get("result"),
            "error": out.get("error"),
        }
        for out in step_outputs
    ]
    final = next(
        (out.get("result") for out in reversed(step_outputs) if out.get("result") is not None),
        None,
    )
    return {"steps": entries, "final": final}


def _final_status(step_outputs: list[dict[str, Any]], verdict: dict[str, Any]) -> RunStatus:
    if not step_outputs or all(out.get("error") is not None for out in step_outputs):
        return RunStatus.failed
    if verdict["needs_approval"]:
        return RunStatus.awaiting_approval
    return RunStatus.done


class Supervisor:
    def __init__(self, store: RunStore | None = None) -> None:
        self.planner = Planner()
        self.router = Router()
        self.executor = Executor()
        self.critic = Critic()
        self.store = store or RunStore()

    # ── Run execution ─────────────────────────────────────────────────────────

    async def start(self, req: RunRequest) -> dict[str, Any]:
        run_id = str(uuid.uuid4())
        state = self.store.put(
            RunState(
                run_id=run_id,
                tenant_id=req.tenant_id,
                module=str(req.module),
                capability=req.capability,
            )
        )
        await self._audit(
            "run_started",
            req.tenant_id,
            {"run_id": run_id, "module": str(req.module), "capability": req.capability},
        )

        capability = await self._resolve_capability(req)
        plan = await self.planner.plan(req)  # L1
        state = self.store.put(state.with_status(RunStatus.executing))

        step_outputs: list[dict[str, Any]] = []
        for step in plan["steps"]:
            out = await self._run_step(step, req, step_outputs)
            step_outputs.append(out)
            state = self.store.put(state.with_step(out))
            await self._audit(
                "run_step_completed",
                req.tenant_id,
                {
                    "run_id": run_id,
                    "step_id": step.get("id"),
                    "kind": step.get("kind"),
                    "tool": step.get("tool"),
                    "error": out.get("error"),
                    "citations": len(out.get("citations", [])),
                },
            )

        verdict = await self.critic.verify(step_outputs, capability)  # L4
        if capability is None:
            # Unknown approval policy (registry down/miss): gate to a human, fail safe.
            verdict = {**verdict, "needs_approval": True}
        status = _final_status(step_outputs, verdict)
        state = self.store.put(
            state.with_result(status, _build_output(step_outputs), verdict["confidence"])
        )
        await self._audit(
            "run_completed",
            req.tenant_id,
            {
                "run_id": run_id,
                "status": str(status),
                "confidence": verdict["confidence"],
                "cost_usd": state.cost_usd,
                "tokens_in": state.tokens_in,
                "tokens_out": state.tokens_out,
            },
        )
        return {"id": run_id, **state.to_status_payload()}

    async def _run_step(
        self, step: dict[str, Any], req: RunRequest, prior: list[dict[str, Any]]
    ) -> dict[str, Any]:
        guard = await self._check_guardrails(step, req.tenant_id)
        if not guard.get("allowed", True):
            logger.warning(
                "step_blocked_by_guardrails",
                step_id=step.get("id"),
                flagged=guard.get("flagged"),
            )
            return {
                "step": step,
                "result": None,
                "citations": [],
                "error": "blocked_by_guardrails",
                "flagged": guard.get("flagged", []),
            }
        route = await self.router.route(step)  # L2
        return await self.executor.execute(step, route, prior)  # L3

    # ── Run queries + approvals ───────────────────────────────────────────────

    async def status(self, run_id: str) -> dict[str, Any]:
        return self._get_or_raise(run_id).to_status_payload()

    def list_runs(self, status: RunStatus | None = None, limit: int = 50) -> list[dict[str, Any]]:
        return [state.to_summary() for state in self.store.list(status=status, limit=limit)]

    async def approve(self, run_id: str, approver: str, note: str | None = None) -> dict[str, Any]:
        state = self._resolve_approval(run_id, RunStatus.done, approver, note)
        await self._audit(
            "run_approved",
            state.tenant_id,
            {"run_id": run_id, "approver": approver, "note": note},
        )
        return state.to_status_payload()

    async def reject(self, run_id: str, approver: str, note: str | None = None) -> dict[str, Any]:
        state = self._resolve_approval(run_id, RunStatus.failed, approver, note)
        await self._audit(
            "run_rejected",
            state.tenant_id,
            {"run_id": run_id, "approver": approver, "note": note},
        )
        return state.to_status_payload()

    def _resolve_approval(
        self, run_id: str, new_status: RunStatus, approver: str, note: str | None
    ) -> RunState:
        state = self._get_or_raise(run_id)
        if state.status is not RunStatus.awaiting_approval:
            raise InvalidRunStateError(state.status)
        return self.store.put(state.with_resolution(new_status, approver, note))

    def _get_or_raise(self, run_id: str) -> RunState:
        state = self.store.get(run_id)
        if state is None:
            raise RunNotFoundError(run_id)
        return state

    # ── Tolerant downstream calls (outages must not crash a run) ─────────────

    async def _check_guardrails(self, step: dict[str, Any], tenant_id: str) -> dict[str, Any]:
        text = (
            f"{step.get('kind', '')}: {step.get('description', '')} "
            f"inputs={json.dumps(step.get('input', {}), default=str)}"
        )
        try:
            return await clients.check_guardrails(text, tenant_id)
        except Exception as exc:  # noqa: BLE001 — degrade open, never kill the run
            logger.warning("guardrails_check_failed_allowing_degraded", error=str(exc))
            return {"allowed": True, "flagged": [], "degraded": True}

    async def _audit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        try:
            await clients.write_audit_event(
                {"type": event_type, "data": data, "tenant_id": tenant_id, "agent": "orchestrator"}
            )
        except Exception as exc:  # noqa: BLE001 — audit outage must not kill the run
            logger.warning("audit_write_failed", event_type=event_type, error=str(exc))

    async def _resolve_capability(self, req: RunRequest) -> dict[str, Any] | None:
        try:
            data = await clients.lookup_capability(str(req.module), req.capability)
        except Exception as exc:  # noqa: BLE001 — registry outage: fall back to gating
            logger.warning("capability_lookup_failed", capability=req.capability, error=str(exc))
            return None
        if "error" in data:
            return None
        return data
