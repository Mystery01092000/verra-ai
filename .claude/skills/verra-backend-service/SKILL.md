---
name: verra-backend-service
description: >
  Create or modify a Verra backend microservice. Use when adding/editing a FastAPI service under
  code/backend/services. Enforces the microservice conventions (ADR-0016/0017).
---

# Verra backend microservice (Python / FastAPI)

## Conventions (every service)
- Layout: `services/<name>/{app/main.py, app/..., pyproject.toml, Dockerfile, tests/, README.md}`.
- `app/main.py` exposes `GET /health` and the service's endpoints; use **pydantic** models from `verra_shared`.
- Internal-only services are reached via HTTP + **mTLS**; **only `gateway` is public** (ADR-0017).
- Tooling: **ruff** (lint+format), **mypy --strict**, **pytest**. Config in `code/backend/pyproject.toml`.
- Async I/O (httpx, async def). Deterministic calculators (tax math) are tools, not LLM output.
- Wire new services into `code/backend/docker-compose.yml` and the CI backend job.

## Golden rules
- Modules never call models/tools directly — go through the **orchestrator** (ADR-0001).
- Every consequential action passes a human gate and writes to the **audit** service (ADR-0015).
- Conform requests/responses to `code/backend/api/openapi.yaml`.
