# ADR-0003: Polyglot monorepo (frontend + backend in separate folders)
**Status:** Accepted · Amended 2026-06-16
## Context
We keep one repository but split by concern and language (FE vs BE) per later guidance.
## Decision
One monorepo under `code/`, split into:
- `code/frontend/` — TypeScript: **pnpm workspaces + Turborepo** (apps/web + packages/design-system, shared).
- `code/backend/`  — Python: microservices + `packages/py_shared`, tooling via **uv/ruff/mypy/pytest**.
Shared CI at `code/.github`; governance (CONTRIBUTING, SECURITY) at `code/`.
## Consequences
+ Clean code-vs-docs and FE-vs-BE separation; per-stack tooling; atomic cross-cutting PRs.
− Two toolchains in one repo → CI runs FE and BE jobs separately (see code/.github/workflows/ci.yml).
