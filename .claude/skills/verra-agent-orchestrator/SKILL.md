---
name: verra-agent-orchestrator
description: >
  Implement/extend the Verra Agent Orchestrator — the common, guardrailed service that manages all
  agents behind the modules. Python/FastAPI microservices (ADR-0016/0017). Use for orchestration
  layers, routing, fallbacks, cost/token, guardrails, durability, observability.
  Spec: docs/Verra_Agent_Orchestrator_Plan.docx · code: code/backend/services/orchestrator.
---

# Verra agent orchestrator (Python / FastAPI microservices)

All agentic work goes through the orchestrator. Modules/clients never call models/tools directly and
never bypass the **gateway** (ADR-0001/0017). Services talk over HTTP/JSON + mTLS.

## Services (code/backend/services)
`gateway` (public edge) · `orchestrator` (this) · `model_gateway` (fallback chain) · `ingestion` (RAG) ·
`guardrails` · `registry` (agents/tools) · `audit`.

## Orchestrator core (under a Supervisor state machine)
1. **L1 Planner** (`core/planner.py`) — request → typed task graph; deterministic templates.
2. **L2 Router** (`core/router.py`) — agent + model tier + tools (capability + cost/latency/quality); smallest sufficient model first.
3. **L3 Executor** (`core/executor.py`) — calls model_gateway/tools; retries+backoff; timeouts; breakers; durable checkpoint/resume; idempotent side effects.
4. **L4 Critic** (`core/critic.py`) — grounding/citation + schema + numeric + confidence; gate consequential/low-confidence to human; write audit receipt.

## Always
- **Guardrails** (guardrails service) on every request & response; block/redact/re-route/escalate.
- **Model gateway** fallback chain: primary → secondary → self-hosted → degraded (cache/rules/human).
- **Cost/token**: budgets, caps, kill-switch, token metering, caching (Orchestrator Plan §9–10).
- **Audit** (audit service): append-only, hash-chained; action receipts (ADR-0015).
- **Observability**: OTel trace per run; eval-gated releases.
- Use pydantic models from `verra_shared`. Conform to `code/backend/api/openapi.yaml`.
