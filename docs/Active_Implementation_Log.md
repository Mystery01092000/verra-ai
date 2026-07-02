# Verra — Active Implementation Log

> This file is a running journal of implementation work on Verra. Agents should read it before starting work and update it when they finish a task.

---

## Current Goal

Fix the critical architectural blockers identified in `docs/Verra_Implementation_Review_and_Roadmap.md` so the repo builds cleanly and the Sprint-0 scaffold is sound.

## Blockers being fixed

1. `code/frontend/turbo.json` uses deprecated `pipeline` key → rename to `tasks`.
2. OpenAPI camelCase vs `verra_shared` Pydantic snake_case mismatch → standardize wire format.
3. CI backend job does not install service dependencies → add install step.
4. `docker-compose.yml` missing Temporal and OTel collector → add services.
5. `schema.sql` RLS incomplete → add policies for all tenant-scoped tables.
6. No migration runner → add lightweight migration skeleton.

## Completed work

- Generated `docs/Verra_Implementation_Review_and_Roadmap.md` from full doc/code review.
- Created this log.
- **Frontend build/typecheck/lint fixed:**
  - Renamed `pipeline` → `tasks` in `code/frontend/turbo.json`.
  - Removed `.js` extensions from TS workspace imports in `packages/design-system/src/index.ts` and `tailwind-preset.ts`.
  - Added missing `@types/node`, `eslint`, and `@typescript-eslint/*` devDependencies to `@verra/design-system` and `@verra/shared`.
  - Added `parserOptions.project: true` to `code/frontend/.eslintrc.json` for type-aware linting.
  - Verified `pnpm build`, `pnpm typecheck`, and `pnpm lint` all pass.
- **API casing normalized (OpenAPI ↔ Pydantic ↔ FE):**
  - Added `_VerraBase` in `verra_shared/models.py` with `alias_generator=to_camel` + `populate_by_name=True`.
  - Updated all shared models to inherit from `_VerraBase`; added `RunAccepted` model.
  - Updated `orchestrator/app/main.py` to return typed `RunAccepted` / `RunResult` models.
  - Verified wire format is camelCase (`runId`, `tokensIn`, etc.) while Python stays snake_case.
  - Fixed `dict` annotations and import sorting across backend so `ruff check .` and per-service `mypy` pass.

## Completed work (continued)

- **CI backend fixed:**
  - Installed runtime dependencies (`fastapi`, `uvicorn`, `pydantic`, `httpx`) and editable `verra-shared`.
  - Added per-service `mypy` and `pytest` loops using `MYPYPATH`/`PYTHONPATH` so duplicate `app` packages resolve correctly.
- **Docker compose extended:**
  - Added `temporal` (auto-setup) and `temporal-ui` services.
  - Added `otel-collector` service with config at `infra/otel/otel-collector-config.yaml`.
  - Wired `TEMPORAL_HOST` and `OTEL_EXPORTER_OTLP_ENDPOINT` into the orchestrator and model_gateway.
  - Verified `docker compose config` is valid.

## Completed work (continued)

- **RLS completed:**
  - Added `ENABLE ROW LEVEL SECURITY` + tenant-isolation policies for `users`, `clients`, `documents`, `doc_chunks`, `engagements`, `obligations`, `runs`, `plans`, `steps`, `routing_decisions`, `budgets`, `audit_events` in `infra/db/schema.sql`.
- **Migration runner added:**
  - Created `infra/db/migrate.py` that applies `schema.sql` and numbered `migrations/*.sql` files, tracking them in `schema_migrations`.
  - Added `infra/db/migrations/README.md` and `infra/db/requirements-migrate.txt`.

## Validation results

- **Frontend:** `pnpm build`, `pnpm typecheck`, `pnpm lint` all pass.
- **Backend:** `ruff check .` passes; per-service `mypy` passes for all 7 services + `py_shared`; per-service `pytest` health checks pass.
- **Docker compose:** `docker compose config` validates (local runtime requires Docker daemon).

## In-progress

- Tax module implementation planning completed.
- Next agent can start Phase 1 of the Tax module (schema + AY 2025-26 rules + first calculator).

## Completed work (continued)

- **Tax module plan created:**
  - Generated `docs/Verra_Tax_Module_Implementation_Plan.md`.
  - Scope: Indian residents + NRIs; document ingestion; deterministic calculators; conversational agent; scenario modeling; HITL approval; audit.
  - Defined unified requirements, data model extensions, orchestrator capabilities/tools, ingestion pipeline, frontend/chatbot UX, phased roadmap, and eval criteria.

## Completed work (continued)

- **Tax Phase 1 foundation implemented:**
  - Added Tax schema tables to `infra/db/schema.sql` with RLS: `tax_profiles`, `tax_line_items`, `tax_computations`, `tax_scenarios`, `tax_rules`, `tax_rates`, `dtaa_treaties`, `foreign_tax_credits`.
  - Created migration files `0001_tax_module_schema.sql` and `0002_seed_india_ay2025_26.sql`.
  - Seeded AY 2025-26 rules: Section 87A rebate, standard deduction, 80C/80D/80CCD(1B)/24, surcharge brackets, old/new regime slabs.
  - Built deterministic calculator `verra_shared.tax.compute_tax_liability` with old/new regime, rebate, surcharge, cess, NRI handling, and unit tests.
  - Defined Pydantic extraction schemas for `Form16`, `Form26AS`, and `AIS` with JSON-schema export.
  - Implemented in-memory registry with Tax capabilities (`tax_analysis`, `tax_qa`, `tax_scenario`) and tools (`compute_tax_liability`, `compare_regimes`, `retrieve_tax_rules`, etc.).
  - Added planner templates for `tax_analysis`, `tax_qa`, and `tax_scenario` in `orchestrator/core/planner.py`.
  - Built Tax dashboard frontend shell at `/tax/[year]` with `KpiTile`, `IncomeBreakdown`, and `CitedAmount` components, plus home-page link.

## Validation results (updated)

- **Frontend:** `pnpm build`, `pnpm typecheck`, `pnpm lint` all pass.
- **Backend:** `ruff check .` passes; per-service `mypy` passes for all 7 services + `py_shared`; per-service `pytest` health checks pass (including new tax calculator tests).
- **Docker compose:** `docker compose config` validates.

## Completed work (continued)

- **Tax Phase 2 — calculators, architecture fixes, and orchestrator wiring:**

  ### Bug fixes
  - **Standard deduction new regime corrected:** `DEDUCTION_CAPS["standard_deduction_new_regime"]`
    set to ₹75,000 (Finance Act 2024, effective AY 2025-26). Previously uncapped; now enforced
    in `_capped_deductions` with a citation referencing the Finance Act.
  - **Circular FK in migration 0001 fixed:** `tax_computations` referenced `tax_scenarios` before
    it was created. Reordered: `tax_scenarios` created first (without `computation_id`), then
    `tax_computations`, then `ALTER TABLE tax_scenarios ADD COLUMN IF NOT EXISTS computation_id`.
  - **Seed SQL updated:** standard deduction description now correctly states ₹75,000 under new
    regime with the JSON `conditions` field carrying both caps for reference.

  ### New deterministic calculators (`verra_shared.tax`)
  - **`compare.py` — `compare_regimes()`:** Runs both regimes and returns `RegimeComparison`
    with `recommended_regime`, `tax_delta`, `tax_saving`, and a plain-language `summary`.
  - **`salary.py` — `compute_hra_exemption()`, `compute_lta_exemption()`,
    `compute_salary_exemptions()`:** HRA under Section 10(13A)/Rule 2A (metro 50%/non-metro 40%),
    LTA under Section 10(5), and a composite aggregator. HRA/LTA not applied under new regime.
  - **`reconcile.py` — `reconcile_tds()`:** Cross-checks Form 16, Form 26AS, AIS; flags
    missing-in-26AS entries, minor variances (<₹100), and mismatches; returns `net_tds_claimable`
    (authoritative 26AS/AIS figure) and human-readable flags.
  - **`advance_tax.py` — `compute_advance_tax()`:** Section 211 instalment schedule for AY 2025-26;
    Section 234B interest on total shortfall; Section 234C interest per deferred instalment.
  - **`tax/__init__.py` updated:** exports all new models and functions.

  ### Orchestrator wiring
  - **`orchestrator/app/tools.py` (new):** FastAPI router at `/internal/tools/tax/*` exposing
    all six deterministic tool endpoints for external test harnesses.
  - **`orchestrator/app/main.py`:** includes `tools_router` so the endpoints are live.
  - **`orchestrator/app/core/executor.py` wired:** `_dispatch_tax_tool()` calls Python functions
    directly (same process) for all deterministic tools; non-deterministic steps return a stub
    pending model_gateway wiring.
  - **`orchestrator/app/core/router.py` wired:** calls `POST /v1/resolve` on the registry service
    via httpx to fetch the tool manifest; gracefully falls back to `None` if registry is down.

  ### Registry expanded (`services/registry/app/registry.py`)
  - New capabilities: `document_reconcile`, `filing_prep`.
  - New tools: `compute_salary_exemptions`, `compute_hra_exemption`, `compute_advance_tax`,
    `reconcile_tds`, `parse_indian_tax_document`, `determine_residential_status`,
    `generate_draft_output`.
  - Existing tools updated with richer `required_tools` lists.

  ### Tests (31 total, all passing)
  - `tests/test_compare_regimes.py` — 5 tests: low-income new regime wins, high-deduction old
    regime wins, delta sign matches recommendation, NRI no rebate in both, saving = |delta|.
  - `tests/test_salary_exemptions.py` — 11 tests: HRA metro/non-metro, rent-paid binding,
    zero rent, LTA capping, aggregate old/new regime combinations.
  - `tests/test_tax_liability.py` — 4 new tests: new regime std ded at 75k, over-cap clamped,
    citation references Finance Act 2024.

## Validation results (updated)

- **Backend:** `ruff check .` passes; `mypy` passes on `py_shared`, `orchestrator`, `registry`;
  31 unit tests pass.
- **Frontend:** unchanged — `pnpm build/typecheck/lint` still pass.
- **Docker compose:** `docker compose config` validates.

## In-progress

- None. Tax Phase 2 calculator + orchestrator wiring complete.

## Known remaining gaps / next work

- **Tax Phase 2 remaining:**
  1. Implement ingestion extraction for Form 16 / 26AS / AIS (OCR → structured JSON).
  2. Build tax profile builder from extracted line items → `tax_profiles` / `tax_line_items`.
  3. Implement RAG retrieval tools (`retrieve_tax_rules`, `retrieve_client_docs`) backed by pgvector.
  4. Wire non-deterministic steps (opportunities, QA, draft) through `model_gateway /v1/complete`.
  5. Add floating assistant chat frontend (`AssistantThread` component, `/tax/[year]/chat` page).
  6. Add scenario modeling page (`ScenarioBuilder`, `/tax/[year]/scenario`).
  7. Add document upload + review queue (`DocumentUploader`, `LineItemEditor`,
     `/tax/[year]/documents`, `/tax/[year]/review`).
  8. Wire `TaxDashboard` to real orchestrator API (replace mock data).
  9. Human approval gate UI (`ApproveBar`, `/approvals` inbox).
  10. Build India/NRI golden eval fixtures (100+ CPA-verified cases).

- **Sprint-0 platform stories still stubbed:** model gateway providers, guardrails logic,
  audit hash-chaining, eval harness, Temporal durable workflows.
- Tailwind preset still only exposes a subset of tokens.

---

## Session 2026-07-03 — BRD/PRD verification, remediation waves 1 & 2

- **Verification:** full BRD/PRD vs code gap analysis → `docs/Verra_BRD_PRD_Verification_2026-07-03.md`.
- **Wave 1 (remediation):** orchestrator real run lifecycle + LLM wiring via model_gateway
  `/internal/complete` + guardrails/audit calls + approve/reject endpoints; audit hash-chained
  JSONL log with /verify; guardrails PII/injection/citation checks; ingestion Form16/26AS/AIS
  classification+extraction; gateway prefix routing + query-string + non-JSON passthrough;
  frontend: chat unconfigured-notice fix (identical-response bug), salted password hashing,
  design-token cleanup, tax dashboard wired live, documents/audit/approvals pages wired real.
- **Wave 2 (expanded vision):** `verra_shared.holdings` (19 types, deterministic consolidate +
  advisory flags) + holdings service (8083, JSONL persistence, account masking);
  `verra_shared.rules` (41-rule IT/SEBI/FEMA/IRDAI/GST corpus + search); orchestrator
  capabilities portfolio_analysis / financial_planning / general_qa with regulator-aware
  prompts; frontend /holdings page, chat modes (Portfolio/NRI/Planning),
  attach-document-to-chat ingestion.
- **Hygiene:** ruff clean; strict mypy clean everywhere (py.typed added, CI MYPYPATH fixed);
  circuit breaker fails open on Redis loss; stale model-tier test fixed; compare_regimes no
  longer requires `regime`; frontend run modules fixed to `assistant`.
- **Validation:** 213 backend tests, frontend build/typecheck/lint, compose config, and a
  gateway-only e2e smoke (runs+approvals+audit chain+ingest+holdings+rules) all green.
- **Docs:** `Verra_Platform_Plan_v2.md` (improved plan), `Verra_Implementation_Summary.md`
  (consolidated implementation record).

## Session 2026-07-03 (continued) — Bedrock live + browser E2E

- **NovaProvider added to model_gateway** (boto3 converse, env-overridable tier map
  NOVA_MODEL_SMALL/MEDIUM/LARGE) in the fallback chain Claude → Nova → OpenAI, so free-tier
  Bedrock accounts (Nova-only access) power the orchestrator's LLM steps. 3 new tests.
- **Full stack run live on Bedrock Nova** (AWS profile `verra`, us-east-1): chat, portfolio_analysis
  (done, 12 citations), financial_planning (awaiting_approval → approved in UI with audit receipt).
- **Browser E2E pass** (Chrome automation): chat modes incl. NRI (s.6/10(4) answers, FEMA chips),
  follow-up context, attach-Form16-to-chat → ingested → document-grounded answers; tax dashboard
  live recompute (₹7L → 87A rebate → ₹0 tax); holdings add/consolidate + flag clears; approvals
  sign-off; audit chain verify ("Chain intact — 19 events"). Recording: verra_e2e_workflows.gif.
- **Extraction robustness fix found by E2E:** AMOUNT regex now accepts Rs./INR/₹ prefixes;
  Form 16 identity labels accept "Name of Employer:"-style inline variants; quarter/total rows
  accept narrative format. Regression test added (36 ingestion tests).
- Validation: 217 backend tests, strict mypy, ruff, frontend build — all green.

---
