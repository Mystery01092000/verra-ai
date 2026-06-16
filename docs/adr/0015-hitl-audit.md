# ADR-0015: Human-in-the-loop gates + immutable audit log
**Status:** Accepted
## Context
Verra outputs are analysis/drafts in a regulated domain; nothing consequential may be autonomous.
## Decision
Consequential actions (send/file/post) and low-confidence results require **explicit human approval**.
Every action writes an **append-only, tamper-evident audit event** (actor, sources, model, cost,
approval, rollback). This is enforced in the orchestrator, not per module.
## Consequences
+ Trust, compliance, professional responsibility preserved; defensible trail.
− Some flows require a human step by design (intended).
