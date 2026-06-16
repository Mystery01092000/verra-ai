# ADR-0001: Orchestrator as a single common service
**Status:** Accepted
## Context
Tax, Books, Audit, Compliance and Assistant all need agents, tools, models, guardrails, budgets and
audit. Duplicating this per module causes drift and inconsistent safety.
## Decision
All agentic work routes through one **Agent Orchestrator** service (see Orchestrator Plan). Modules
never call models/tools directly; they call the orchestrator API.
## Consequences
+ One place for guardrails, HITL gates, cost/token control, fallbacks, audit, observability.
+ Reusable, versioned agents/tools.
− Orchestrator is critical path → must be horizontally scalable and resilient (addressed in design).
