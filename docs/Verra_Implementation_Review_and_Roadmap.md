# Verra — Implementation Review & Roadmap

**Status:** Implementation-ready scaffold | **Review date:** 26 June 2026 | **Scope:** docs, design, code, CI/CD, .claude automation

---

## 1. Executive Summary

Verra is a concept AI-native B2B SaaS for accounting, tax, audit and compliance. The project has a mature **product + architecture paper trail** (BRD, PRD, System Design, Agent Orchestrator Plan, 18 ADRs), a **working microservice scaffold** (7 FastAPI services, Next.js frontend, PostgreSQL+pgvector, Redis, MinIO), a **design system** modeled on ideation, and a **Claude Code automation layer** (skills, agents, hooks, commands). The repo is intentionally at the "skeleton + stubs" stage: every major component has an endpoint and a Dockerfile, but the business logic inside most services is still `TODO`.

This document reviews the current state, validates consistency between documents and code, lists the gaps that must be closed before a real tax-analysis run works end-to-end, and proposes a prioritized implementation roadmap.

**Bottom line:** The project is well-architected and consistent. The highest-value next step is to make the **Sprint-0 goal** real: a request that flows through the orchestrator with guardrails, model fallback, human approval, audit receipt, budget enforcement, and an eval harness gating CI.

---

## 2. Project Overview

| Dimension | Decision | Source |
|---|---|---|
| Product | AI engine across accounting, tax, audit, compliance; Tax is the MVP | `docs/Verra_BRD.docx`, `docs/Verra_PRD.docx` |
| Tenants | Firms, companies, individuals; multi-jurisdiction (US → UK → India) | PRD §1, ADR-0009 |
| Frontend | Next.js 14 + React 18 + Tailwind + pnpm/turbo workspaces | ADR-0002/0004 |
| Backend | Python 3.12 + FastAPI microservices | ADR-0016/0017 |
| AI runtime | Custom multi-layer orchestrator + Temporal (durable workflows) | ADR-0005, Orchestrator Plan |
| Model access | Provider-agnostic model gateway with fallback chain | ADR-0006 |
| Data | PostgreSQL + pgvector, Redis, S3-compatible object store | ADR-0007/0008/0013 |
| Trust layer | Human-in-the-loop gates, immutable hash-chained audit log | ADR-0015 |
| Guardrails | OPA/Cedar policy engine + layered validators | ADR-0011 |
| Observability | OpenTelemetry + LLM-trace tooling | ADR-0012 |
| Infra | Docker, Kubernetes (Helm), Terraform, GitHub Actions | ADR-0014 |

---

## 3. Documentation Inventory & Review

### 3.1 Core documents

| Document | Format | Completeness | Notes |
|---|---|---|---|
| `README.md` (root) | Markdown | Strong | Clear positioning, architecture diagram summary, tech stack, repo map, status |
| `CLAUDE.md` | Markdown | Strong | Non-negotiable principles, design system, .claude scaffold index, build commands |
| `code/README.md` | Markdown | Adequate | Monorepo structure and run commands |
| `docs/Verra_BRD.docx` | DOCX | Strong | Business rationale, market sizing, personas, scope, requirements `BR-1..12`, roadmap |
| `docs/Verra_PRD.docx` | DOCX | Strong | Goals/non-goals, functional requirements by module (`FR-*`), AI design, data model, NFRs |
| `docs/Verra_System_Design.docx` | DOCX | Strong | Service topology, data model, API, runtime flow, deployment, security, observability |
| `docs/Verra_Agent_Orchestrator_Plan.docx` | DOCX | Strong | L1–L4 layers, registry, model gateway, cost/token management, guardrails, SLOs |
| `docs/Verra_Execution_Plan.docx` | DOCX | Strong | Phases, team, workstreams, Figma build order, launch checklist |
| `docs/Verra_Test_and_Eval_Strategy.md` | Markdown | Adequate | Test pyramid + AI eval harness; points to ADRs/CI but lacks concrete harness code |

### 3.2 Architecture Decision Records (`docs/adr/`)

18 ADRs cover every major choice. They are consistent, immutable, and correctly superseded (e.g., ADR-0002 split into frontend TS / backend Python).

Key accepted decisions:
- **ADR-0001:** Orchestrator as common service — modules never call models/tools directly.
- **ADR-0005:** Custom DAG + Temporal for durable workflows.
- **ADR-0006:** Model gateway with fallback chain.
- **ADR-0009:** Shared-DB multi-tenancy with `tenant_id` + PostgreSQL RLS.
- **ADR-0015:** Human-in-the-loop + immutable audit log.
- **ADR-0016/0017:** Python/FastAPI microservices from day one.

### 3.3 Design artifacts (`design/`)

| Artifact | Status |
|---|---|
| `design-tokens.json` / `.css` | Complete, consistent, single source of truth |
| `verra-prototype.html` / `-glass.html` | Clickable prototypes; referenced as UX source of truth |
| `figma-build-spec.md` / `ideation-ux-reference.md` | Clear build order and visual language summary |
| SVG diagrams (orchestrator, ERD, sequence, deployment) | Present and use the design tokens |

### 3.4 Backlog (`docs/backlog/`)

`sprint-0-backlog.csv` is import-ready (Epic, StoryID, Title, Type, Priority, Estimate, AcceptanceCriteria, DependsOn). Sprint 0 goal is well-defined and matches the orchestrator-first implementation strategy.

---

## 4. Architecture & Design Review

### 4.1 Microservice topology

The 7 services match ADR-0017 and System Design §2.1:

1. `gateway` — public edge
2. `orchestrator` — Supervisor + L1–L4 core
3. `model_gateway` — provider abstraction + fallback chain
4. `ingestion` — OCR/parse/extract/retrieve
5. `guardrails` — input/output/policy validation
6. `registry` — agent + tool manifests
7. `audit` — append-only hash-chained log

### 4.2 Orchestrator layers

Implemented as stubs in `code/backend/services/orchestrator/app/core/`:
- `planner.py` — returns a single placeholder step.
- `router.py` — returns a hard-coded "cheapest-sufficient" route.
- `executor.py` — returns an empty result.
- `critic.py` — checks only whether `citations` is non-empty.

The skeleton matches the Supervisor state machine described in the Orchestrator Plan, but **no durable workflow engine (Temporal) is wired yet**, and guardrails/audit/cost calls are commented as `TODO`.

### 4.3 API contract

`code/backend/api/openapi.yaml` defines:
- `POST /v1/runs`
- `GET /v1/runs/{id}`
- `GET /v1/runs/{id}/events` (SSE)
- `POST /v1/runs/{id}/approve` / `reject`

The contract aligns with the Orchestrator Plan §16. However, **the OpenAPI schema uses camelCase** (`tenantId`, `contextRefs`, `maxUsd`) while the **Pydantic models in `verra_shared/models.py` use snake_case** (`tenant_id`, `context_refs`, `max_usd`). Frontend shared types also use camelCase. This is a real contract mismatch that will break generated clients if not normalized.

### 4.4 Data model

`code/backend/infra/db/schema.sql` covers the ERD entities: `tenants`, `users`, `clients`, `documents`, `doc_chunks` (pgvector), `engagements`, `obligations`, orchestrator tables (`runs`, `plans`, `steps`, `routing_decisions`, `agent_versions`, `tool_defs`, `budgets`), and `audit_events`.

**Gap:** RLS is only `ENABLE`d + policy-created for `clients`. The comment says "repeat ... generated in migrations," but no migration files exist yet. Every tenant-scoped table needs the same treatment.

### 4.5 Design system

Tokens are consistent across `design/design-tokens.json`, `design/design-tokens.css`, and `code/frontend/packages/design-system/src/tokens.ts`. The Tailwind preset is minimal but uses tokens correctly.

---

## 5. Code Scaffold Review

### 5.1 Backend (`code/backend/`)

| File/Area | State | Notes |
|---|---|---|
| `docker-compose.yml` | Valid | `docker compose config` succeeds; Postgres+pgvector, Redis, MinIO, 7 services wired |
| `api/openapi.yaml` | Draft | Paths/schemas defined; camelCase/snake_case mismatch to resolve |
| `infra/db/schema.sql` | Draft | Tables present; RLS incomplete; no migration runner |
| `packages/py_shared/verra_shared/models.py` | Draft | Core Pydantic types; snake_case fields |
| `services/gateway/app/main.py` | Stub | Health, middleware placeholder, `/v1/runs` proxy; no OIDC/mTLS/tenant/rate-limit/idempotency yet |
| `services/orchestrator/app/main.py` | Stub | Internal run endpoints; imports `core` layers |
| `services/orchestrator/app/core/*.py` | Stubs | Layer skeletons present; logic is `TODO` |
| `services/model_gateway/app/main.py` | Stub | `/v1/complete` endpoint |
| `services/model_gateway/app/providers.py` | Stub | `FallbackChain` with no providers registered |
| `services/ingestion/app/main.py` | Stub | `/v1/ingest` returns `{"todo": true}` |
| `services/guardrails/app/main.py` | Stub | `/v1/check` returns `{"todo": true}` |
| `services/registry/app/main.py` | Stub | `/v1/resolve` returns `{"todo": true}` |
| `services/audit/app/main.py` | Stub | `/v1/events` returns `{"todo": true}` |
| Service Dockerfiles | Minimal | Install deps manually; do not install `verra-shared` from workspace |
| Service `pyproject.toml` | Present | Declare `verra-shared` dependency, but workspace build is not wired in Dockerfiles |

### 5.2 Frontend (`code/frontend/`)

| File/Area | State | Notes |
|---|---|---|
| `turbo.json` | **Broken** | Uses `pipeline` key; turbo v2 requires `tasks`. `pnpm build/typecheck/lint` all fail with rename error |
| `apps/web/app/page.tsx` | Placeholder | Imports tokens, but hardcodes `fontFamily: 'Inter, sans-serif'` instead of `tokens.type.body.family` |
| `packages/design-system/src/tokens.ts` | Good | Mirrors `design/design-tokens.json` |
| `packages/design-system/src/tailwind-preset.ts` | Minimal | Only exposes a few colors; should expand to full token map |
| `packages/shared/src/types.ts` | Good | Mirrors OpenAPI/verra_shared shapes (camelCase) |

### 5.3 CI/CD (`code/.github/workflows/`)

- `ci.yml`: separate frontend/backend/evals jobs. Frontend job is correct. Backend job installs `ruff mypy pytest` but **does not install FastAPI or service dependencies**, so `pytest` will fail in CI even after lint passes. Evals job is a `TODO` echo.
- `cd.yml`: tag-triggered deployment placeholder.

### 5.4 .claude automation (`/.claude/`)

Comprehensive and aligned:
- **Skills:** 12 skills covering tax analysis, orchestrator, backend/frontend, design system, ingestion, audit, compliance, security, requirements, Figma.
- **Agents:** tax-analyst, design-engineer, backend-engineer, compliance-reviewer.
- **Commands:** `/tax-analysis`, `/new-screen`, `/new-service`, `/figma-build`, `/brd-prd`, `/security-review`.
- **Hooks:** session-start guardrails, PII guard, bash guard, path protection, design validation, code formatting.

The hooks correctly block destructive commands and secret exposure, warn on non-token colors, and protect generated `.docx` files.

---

## 6. Validation Findings: Issues, Gaps & Inconsistencies

### 6.1 Critical blockers (must fix before Sprint-0 demo)

| # | Issue | Location | Impact | Recommended fix |
|---|---|---|---|---|
| 1 | `turbo.json` uses deprecated `pipeline` key | `code/frontend/turbo.json` | Frontend build/typecheck/lint fail | Rename `pipeline` → `tasks` |
| 2 | OpenAPI camelCase vs Pydantic snake_case mismatch | `api/openapi.yaml` ↔ `packages/py_shared/verra_shared/models.py` | Generated clients break; FE/BE contract unclear | Standardize on one casing (recommend OpenAPI camelCase + generated server models, or alias fields) |
| 3 | CI backend job lacks dependency install | `code/.github/workflows/ci.yml` | `pytest` fails in CI; false-negative health checks | Add `pip install -e services/* -e packages/py_shared` or use `uv` workspace sync |
| 4 | No Temporal/OTel in docker-compose | `code/backend/docker-compose.yml` note | Durable workflows and observability stories blocked | Add `temporal` and `otel-collector` services in a follow-up PR |
| 5 | RLS incomplete | `code/backend/infra/db/schema.sql` | Tenant isolation not enforced for most tables | Add `ENABLE ROW LEVEL SECURITY` + policies for all tenant-scoped tables; add migration runner |

> **Status:** All five critical blockers have been fixed. See `docs/Active_Implementation_Log.md` for the exact commits/changes and validation results.

### 6.2 Major gaps (Sprint-0 stories)

| Story | Gap | Where implemented |
|---|---|---|
| VERRA-007 | Gateway authN/Z, tenant resolution, rate limits, idempotency replay | `services/gateway/app/main.py` |
| VERRA-008 | Durable workflow engine spike (Temporal) | `docker-compose.yml` + `orchestrator/core/supervisor.py` |
| VERRA-009 | Planner templates (tax_analysis) | `orchestrator/core/planner.py` |
| VERRA-010 | Capability-based router via registry | `orchestrator/core/router.py` |
| VERRA-011 | Retries/backoff/timeouts/circuit breakers | `orchestrator/core/executor.py` |
| VERRA-012 | Model gateway fallback chain with real providers | `services/model_gateway/app/providers.py` |
| VERRA-013 | Real critic: grounding, schema, numeric, confidence | `orchestrator/core/critic.py` |
| VERRA-014/015 | Guardrails logic (input/output/policy) | `services/guardrails/app/main.py` |
| VERRA-016 | Human approval gate + resume | `orchestrator/core/supervisor.py` |
| VERRA-017 | Immutable hash-chained audit log | `services/audit/app/main.py` |
| VERRA-018 | Budget envelope + token accounting | `orchestrator/core/supervisor.py` + schema `budgets` |
| VERRA-020 | Eval harness + golden set | No code yet; only strategy doc |

### 6.3 Minor inconsistencies

- `code/frontend/apps/web/app/page.tsx` hardcodes `Inter, sans-serif` despite `tokens.type.body.family` being available.
- Tailwind preset only exposes a subset of tokens (indigo, ink, cream); should expose full palette/radius/shadows.
- `Makefile` `dev` target runs backend in background then foreground frontend; if frontend exits, backend stays up. Acceptable but worth documenting.
- `.nvmrc` and `package.json` engines require Node ≥20, but CI pins `node-version: 20` — consistent.

### 6.4 Strengths to preserve

- ADRs are the authoritative decision trail and are internally consistent.
- The microservice boundaries are coarse-grained and well-justified (ADR-0017).
- Design tokens are single-sourced and propagated to CSS, JSON, and TS.
- The .claude scaffold operationalizes governance (HITL, citations, audit, zero-retention) better than most early-stage projects.
- `docker-compose.yml` is valid and brings up the data plane + services with one command.
- The Sprint-0 backlog is granular, prioritized, and dependency-linked.

---

## 7. Implementation Roadmap

The roadmap below maps the existing Sprint-0 backlog into concrete epics, with the goal of making the Sprint-0 acceptance criterion pass: **"A request flows end-to-end through the guardrailed orchestrator (plan→route→execute→critic), with a model fallback, a human approval gate, an audit receipt, budgets enforced, and the eval harness gating CI."**

### Phase 0 — Foundation fixes (Week 1)

1. **Fix frontend tooling** — rename `pipeline` → `tasks` in `turbo.json`; expand Tailwind preset to full tokens.
2. **Fix CI backend job** — install service dependencies so `pytest` can collect tests.
3. **Normalize API casing** — decide camelCase vs snake_case and align `openapi.yaml`, `verra_shared`, and `@verra/shared`.
4. **Complete RLS** — add policies for all tenant tables and introduce a migration runner (e.g., Alembic or `yoyo`).
5. **Local data-plane verification** — `docker compose up -d` + health checks green.

### Phase 1 — Orchestrator core (Weeks 2–4)

1. **Gateway cross-cutting concerns:** OIDC token validation, tenant context resolution, rate-limit stub, idempotency-key replay cache.
2. **Supervisor state machine:** persist run state in Postgres, support pause/resume/await-approval.
3. **Planner templates:** `tax_analysis`, with typed DAG steps.
4. **Router:** call `registry` to resolve agent + model tier + tools; emit `routing_decisions` rows.
5. **Executor:** httpx clients to `model_gateway` and tools; retries + exponential backoff + timeouts; idempotency keys.
6. **Critic:** real grounding/citation checks, schema validation, numeric cross-check against deterministic calculators, confidence score.

### Phase 2 — Trust & cost layer (Weeks 4–6)

1. **Guardrails service:** input schema, PII/DLP redaction, prompt-injection classifier stub, policy check via OPA/Cedar or in-house rules.
2. **Audit service:** append-only hash-chained `audit_events`; action receipt endpoint.
3. **Human approval gate:** `needs_approval` pauses run; `POST /approve`/`/reject` resumes with actor signature.
4. **Budget/token manager:** per-run budgets, soft warn / hard cap, token metering, cost attribution.
5. **Model gateway:** register Anthropic (primary), secondary provider stub, self-hosted stub, degraded mode; circuit breaker.

### Phase 3 — Ingestion & Tax MVP (Weeks 7–10)

1. **Ingestion pipeline:** document upload → OCR/parse → structured extraction with page refs + confidence → `documents`/`doc_chunks`.
2. **Tax profile & deterministic calculators:** US federal brackets, marginal/effective rate, withholding, estimate gaps.
3. **Tax-analysis agent:** opportunity detection (Roth headroom, loss harvesting, credits) with citations.
4. **Scenario modeling:** side-by-side compare, editable assumptions, real-time recompute.
5. **Client-ready outputs:** letter + interactive report + talking points; gated by approval + audit receipt.

### Phase 4 — Eval harness & CI gate (Weeks 8–12, parallel)

1. **Golden dataset:** anonymized US 1040 fixtures with expected citations and tax figures.
2. **Eval runner:** citation accuracy, numeric correctness, hallucination/refusal rates, guardrail block rates.
3. **CI `evals` job:** runs regression suite; blocks merge on regression.
4. **Online eval stub:** canary comparison placeholder for production.

### Phase 5 — Observability & durability (Weeks 10–14)

1. Add Temporal service to docker-compose and K8s Helm charts.
2. Wire durable workflows into `supervisor.py`.
3. OpenTelemetry instrumentation across gateway → orchestrator → services → providers.
4. SLO dashboards and alerting stubs.

---

## 8. Immediate Next Steps (this week)

1. **Merge tooling fixes:** `turbo.json` rename, CI dependency install, API casing decision.
2. **Pick the API casing standard** and update `openapi.yaml`, `verra_shared/models.py`, and `@verra/shared/src/types.ts` in one PR.
3. **Add Alembic/yoyo migration skeleton** and complete RLS policies for all tenant tables.
4. **Implement gateway tenant + idempotency stubs** so the public surface has the shape promised in the System Design.
5. **Implement the orchestrator happy path:** planner → router → executor → critic writing real `runs`/`plans`/`steps` rows, even if model calls are mocked.
6. **Create the first golden eval case** for a simple 1040 tax-analysis run so the `evals` CI job has something real to run.

---

## 9. Recommendations

1. **Keep ADRs authoritative.** Every new major choice (vector DB split, gRPC, per-service DB) should get an ADR per ADR-0000.
2. **Treat the OpenAPI spec as the FE/BE contract.** Generate both the Python request models and the TypeScript client from it to eliminate casing/field drift.
3. **Invest in the eval harness early.** In a regulated product, eval-gated releases are not optional; the harness should be the second-highest priority after the orchestrator skeleton.
4. **Don't over-engineer the registry/guardrails v1.** A JSON-file or in-memory registry with versioned manifests is enough for Sprint 0; graduate to a database-backed policy engine once the core loop is stable.
5. **Document the "degraded" mode.** The fallback chain ending in "queue for human" is a trust feature, not a bug. Make sure UX and ops runbooks know how to surface it.
6. **Use the .claude scaffold.** The skills/agents/hooks already encode the project's principles; route implementation tasks through them to maintain consistency.

---

## 10. Conclusion

Verra has a strong, coherent design and a clean scaffold. The documentation is internally consistent and the code skeleton correctly reflects the architecture. The main work ahead is moving from stubs to an end-to-end tax-analysis run while preserving the trust, observability, and governance layers that differentiate the product. Fixing the tooling blockers first will unblock parallel work across frontend, backend, and evals.
