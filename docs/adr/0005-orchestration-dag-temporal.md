# ADR-0005: Custom DAG orchestration + Temporal for durability
**Status:** Accepted
## Context
Runs are multi-step, long-running, must checkpoint/resume and survive restarts; we also need a
typed task graph (Planner→Router→Executor→Critic).
## Decision
Model runs as a **typed DAG** executed by our orchestrator core; use **Temporal** (or managed
equivalent) for durable execution, retries, and checkpoint/resume. Evaluate LangGraph for agent-graph
ergonomics behind our interfaces.
## Consequences
+ Reliable long-running jobs; idempotent steps; resumability.
− Operational complexity of a workflow engine; mitigated with managed offering.
