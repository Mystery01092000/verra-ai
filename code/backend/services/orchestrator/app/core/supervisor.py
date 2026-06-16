"""Run lifecycle state machine (ADR-0005). Backed by a durable workflow engine (Temporal)."""
from __future__ import annotations

import uuid

from verra_shared import RunRequest

from .critic import Critic
from .executor import Executor
from .planner import Planner
from .router import Router


class Supervisor:
    def __init__(self) -> None:
        self.planner = Planner()
        self.router = Router()
        self.executor = Executor()
        self.critic = Critic()

    async def start(self, req: RunRequest) -> dict:
        run_id = str(uuid.uuid4())
        # TODO: guardrails.check_input(req); cost.open(run_id, req.budget)
        plan = await self.planner.plan(req)              # L1
        # L2->L3->L4 execute inside the durable workflow; gate consequential/low-confidence to a human.
        for step in plan["steps"]:
            route = await self.router.route(step)        # L2
            out = await self.executor.execute(step, route)  # L3 (-> model_gateway, tools)
            verdict = await self.critic.verify(out)      # L4
            # TODO: guardrails.check_output(out); audit.write(...)
            if verdict["needs_approval"]:
                break
        return {"id": run_id, "status": "planned"}

    async def status(self, run_id: str) -> dict:
        return {"run_id": run_id, "status": "executing"}  # TODO load state
