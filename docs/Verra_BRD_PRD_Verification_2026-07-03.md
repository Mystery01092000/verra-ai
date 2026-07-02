# Verra — BRD/PRD Verification & Gap Analysis (2026-07-03)

Full verification of `Verra_BRD.docx` (v0.1) and `Verra_PRD.docx` (v0.1) against the actual
implementation under `code/`. Status columns show state **before** and **after** this session's
remediation work (see "Work completed this session" at the end).

---

## 1. Verdict on the documents themselves

The BRD and PRD are internally consistent and consistent with each other (personas, scope,
metrics, roadmap all line up). Issues found in the documents:

1. **Jurisdiction drift (BRD/PRD vs code).** Both documents state **US is the MVP jurisdiction**
   (PRD §1 "Jurisdictions: US (MVP) · UK · India"). The implementation is **India-first**
   (AY 2025-26 slabs, 87A, HRA/LTA, 26AS/AIS, advance tax §211/234B/234C). This is a deliberate
   pivot made during implementation but the BRD/PRD were never updated. Either update the docs to
   "India (MVP) · US · UK" or record an ADR for the pivot. **The code is right to be
   jurisdiction-versioned; the docs are stale.**
2. **PRD acceptance criteria are US-only** (§6.3.5 speaks of 1040 uploads, Roth conversions,
   24% bracket) and have no India equivalents, so the implemented India calculators have no
   PRD-level acceptance criteria to verify against. The India-side criteria exist only in
   `docs/Verra_Tax_Module_Implementation_Plan.md`.
3. **No FR IDs for the Daily Digest data sources** — FR-DG-1 requires inbox/calendar scanning but
   the Integrations section lists email/calendar as phased; the dependency is not sequenced.
4. **BRD success metrics are unmeasurable in-product today** (hours saved, citation accuracy)
   because no analytics/eval harness exists yet; PRD §11 lists the metrics but no FR requires the
   instrumentation. Recommend an FR for event analytics + the eval suite (PRD §7 mentions evals
   only in passing).
5. **Open questions (PRD §13) remain unresolved** — jurisdiction order was implicitly answered
   (India) by the code; the build-vs-license rules-engine question is answered de facto
   (hand-built rules seeded in `0002_seed_india_ay2025_26.sql`). Close them formally.

## 2. Requirement-by-requirement verification (PRD Musts + BRD Musts)

| Req | Requirement | Before session | After session |
|---|---|---|---|
| BR-1 / FR-TX-1..4 | Ingest & parse documents once, confidence-scored, reusable | **Stub** (echo endpoint; schemas existed unused) | **Partial-real**: classification + regex extraction for Form 16 / 26AS / AIS with per-field confidence, needs_review gating; no OCR (text/JSON input only) |
| BR-2 / FR-TX-5..8 | Cited tax analysis & opportunities in minutes | **Partial**: deterministic calculators real (liability, regimes, HRA/LTA, TDS reconcile, advance tax — all cited); LLM opportunities/QA stubbed | **Real**: executor now routes non-deterministic steps through model_gateway with grounding + citation-required system prompts |
| BR-3 / FR-TX-15 / FR-TR-2 | Human approval before send/file | **Design-only** (flags in registry; critic placeholder) | **Real**: needs_approval state machine, approve/reject endpoints with approver + audit receipt, /approvals UI |
| BR-4 / FR-TR-1 | Immutable audit log w/ receipts | **Stub** (uuid + log line) | **Real**: sha256 hash-chained append-only log, verify endpoint, orchestrator writes per-step + approval events, /audit UI |
| BR-5 / FR-TX-11 | Jurisdiction/year-versioned rules | **Real** (schema + seeded AY 2025-26 rules; calculators guard AY) | unchanged |
| BR-6 / FR-TR-3 | Multi-tenant + RBAC + tenant isolation | **Schema-only**: RLS policies exist but no service connects to Postgres; no auth/RBAC anywhere; gateway open CORS | unchanged at runtime (top remaining gap — see §3) |
| BR-10 | Security/privacy standards, zero-retention | **Missing**: no zero-retention headers, unsalted SHA-256 passwords, hardcoded dev secret fallback | Passwords → salted scrypt; secret warning; zero-retention headers still TODO |
| FR-AS-1..5 | Assistant: modes, citations, context, drafts queued | **Partial**: chat UI real, agent modes real; identical-response bug when unconfigured; citations not enforced | Bug fixed (honest unconfigured notice + provider metadata); citation enforcement added in guardrails + critic |
| FR-TX-9..12 | Scenario modeling, side-by-side, live recompute | **Partial**: compare_regimes real; no UI | Dashboard w/ live assumptions editor + regime comparison (scenario builder UI still shallow vs PRD) |
| FR-CO-1 | Compliance calendar | **Missing** (only `obligations` table) | **Still missing** — biggest un-started Must |
| FR-DG-1 | Daily digest | **Missing** | **Still missing** (needs email/calendar integrations) |
| FR-TR-4 | Admin: sources, jurisdictions, AI controls | **Missing** | **Still missing** |

Roadmap-depth items (Books & Close FR-BK, Audit FR-AU, Client portal FR-CP) are correctly
absent per the phased plan — not counted as gaps.

## 3. Issues found (code)

### Fixed this session
1. `test_bedrock_provider_medium_tier_uses_sonnet` asserted Sonnet while passing `model_tier="large"` (maps to Opus) — test bug.
2. 15 ruff errors: pathlib calls inside async startup across all 7 services (moved to shared sync `prepare_multiproc_dir`), `CircuitState(str, Enum)` → `StrEnum`.
3. Orchestrator called a non-existent registry endpoint (`/internal/tools/lookup`; registry serves `/v1/resolve`) — silently swallowed 404.
4. Executor TODO pointed at model_gateway `/v1/complete`; the real route is `/internal/complete`. LLM steps returned `None` — root cause of "assistant says the same thing regardless of input" (combined with the frontend's constant fallback string in `app/api/chat/route.ts`).
5. `check_guardrails` / `call_model_gateway` / `write_audit_event` in `orchestrator/app/clients.py` were dead code — defined, never called.
6. Supervisor returned hardcoded `{"status": "planned"}`; run status endpoint hardcoded `"executing"` — no real run state.
7. Gateway proxy dropped query strings (broke any filtered GET).
8. Frontend: unsalted SHA-256 password hashes; `.users.json` not gitignored; hardcoded `NEXTAUTH_SECRET` fallback.
9. Design-token violations (inline hex/rgba + `zinc-*` utilities) across chat components and Sidebar, violating the project's no-hardcoded-colors rule.
10. `TaxDashboard` component tree orphaned — built, never routed.
11. Audit service placeholder ("hash-chain in Phase 3") despite BR-4 being a Must; guardrails allowed everything unconditionally.

### Known-remaining (documented, not fixed)
1. **No database persistence at runtime** — no service imports a DB driver; rich schema + RLS are dormant. Runs/audit/profiles live in memory or JSONL. Highest-priority next step.
2. **No authn/authz on the backend** — gateway forwards blindly; RBAC/SSO (FR-TR-3) untouched; CORS `*`.
3. **Temporal & OTel provisioned in compose but unused by code** (no durable workflows, no traces).
4. **Zero-retention headers / provider DPA controls** not implemented in model_gateway.
5. **No streaming** from model_gateway (PRD: first token < 3s).
6. **Compliance calendar, daily digest, admin surface** — un-started PRD Musts.
7. **Eval harness / golden fixtures** (100+ CPA-verified cases planned) — un-started.
8. **US jurisdiction** — nothing implemented; docs say it's the MVP.

## 4. Enhancement recommendations (beyond fixes)

1. **Persistence layer**: add a thin asyncpg/psycopg repository package in `py_shared`, set
   `app.tenant_id` per request so the existing RLS actually enforces isolation; move the run
   store, audit chain, and tax profiles onto the schema that already exists.
2. **Auth**: JWT verification middleware at the gateway (NextAuth-issued tokens), tenant claim →
   RLS setting; per-tenant rate limiting (BRD BR-10, PRD §10).
3. **Docs**: update BRD/PRD to v0.2 — India-first pivot, India acceptance criteria, analytics FR,
   close §13 open questions.
4. **Evals**: golden-case harness wired into CI (the Test & Eval Strategy doc already specifies it).
5. **Streaming + zero-retention headers** in model_gateway; surface provider/model in every
   assistant reply for auditability.
6. **Compliance calendar MVP**: obligations CRUD + seeded India deadlines (GSTR-3B, advance-tax
   instalments, ITR due dates) — the table already exists; it is the cheapest un-started Must.
7. **Scenario builder UI** on top of the existing `build_scenario` capability to fully meet
   FR-TX-9/10.

## 5. Work completed this session (2026-07-03)

- Lint/test hygiene: ruff clean, all suites green.
- Orchestrator: real run lifecycle (planned→executing→completed/needs_approval/failed/rejected),
  LLM steps through model_gateway, guardrails pre-check per step, audit event per step, real
  critic confidence, registry resolve fixed, run list + approve/reject endpoints.
- Audit service: hash-chained append-only JSONL log with verify endpoint.
- Guardrails: PII detection/masking (PAN/Aadhaar/SSN/email/phone), prompt-injection heuristics,
  citation enforcement for money-bearing outputs.
- Ingestion: Form 16 / 26AS / AIS classification + field extraction with confidence and
  needs_review gating.
- Gateway: prefix routing to ingestion/audit, query-string forwarding, tests.
- Frontend: honest unconfigured-chat notice + provider metadata; salted scrypt passwords;
  `.users.json` gitignored; tax dashboard routed & wired to real calculators with live
  assumptions; documents upload wired to ingestion; audit page wired to the real chain with
  verify; new /approvals HITL inbox; design-token cleanup.
