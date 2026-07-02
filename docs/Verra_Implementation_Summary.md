# Verra — Consolidated Implementation Summary

**As of:** 2026-07-03 · **Validation:** 213 backend tests green · ruff clean · strict mypy clean
across all 8 services + shared package · frontend build/typecheck/lint green · docker compose
config valid · gateway-only e2e smoke test passing.

This document consolidates everything implemented in the Verra codebase to date. Companion docs:
`Verra_BRD_PRD_Verification_2026-07-03.md` (gap analysis), `Verra_Platform_Plan_v2.md` (forward
plan), `Active_Implementation_Log.md` (running journal).

---

## 1. System shape

```
Next.js web (apps/web)
   └─ /api/* server routes ──► gateway :8080  (sole public entry, ADR-0001)
                                  ├─ /v1/ingest      ──► ingestion  :8087
                                  ├─ /v1/audit/*     ──► audit      :8086
                                  ├─ /v1/holdings/*  ──► holdings   :8083
                                  └─ /v1/* (default) ──► orchestrator :8081
                                        ├─ registry      :8085  (capabilities/tools)
                                        ├─ guardrails    :8084  (PII / injection / citations)
                                        ├─ audit         :8086  (hash-chained event log)
                                        ├─ holdings      :8083  (consolidation engine)
                                        └─ model_gateway :8082  (Bedrock → OpenAI fallback)
Shared: packages/py_shared/verra_shared — tax calculators · holdings engine ·
        regulatory rules corpus · extraction schemas · infra (logging/metrics/CB)
```

## 2. Deterministic engines (no LLM arithmetic — ever)

### Tax (`verra_shared.tax`) — India AY 2025-26, residents & NRIs
- **Liability** (`liability.py`): slabs (old/new regime), capped Chapter VI-A deductions,
  surcharge with marginal relief, 87A rebate, 4% cess, effective rate — every component cited
  to its section.
- **Regime comparison** (`compare.py`): both regimes computed, recommendation + saving (115BAC).
- **Salary exemptions** (`salary.py`): HRA (10(13A)/Rule 2A metro/non-metro), LTA (10(5)),
  standard deduction; regime-aware.
- **TDS reconciliation** (`reconcile.py`): Form 16 ↔ 26AS ↔ AIS by TAN; matched / minor-variance /
  mismatch / missing flags; net claimable per s.199/Rule 37BA.
- **Advance tax** (`advance_tax.py`): s.211 instalments, 234B/234C interest.
- **Extraction schemas** (`extraction.py`): Form 16 / 26AS / AIS Pydantic models with per-field
  confidence and page references.

### Holdings consolidation (`verra_shared.holdings`) — NEW
- 19 holding types (funds, stocks, bonds, FD/RD/PPF/EPF/NPS, life/health/ULIP insurance,
  4 loan classes, real estate, gold, cash, other); account numbers always masked to last-4.
- `consolidate()`: net worth, assets vs liabilities, category allocation (sums to 100%),
  insurance-cover totals, and four advisory flags with honestly-sourced citations:
  concentration >25%, life cover <10× income (labeled industry heuristic), debt ratio >50%,
  no health cover.

### Regulatory rules corpus (`verra_shared.rules`) — NEW
- 41 rules across Income-tax Act (slabs, 87A, Chapter VI-A, capital gains 111A/112A/54*,
  advance tax), NRI (s.6 residency + 6(1A) deemed residency, s.195 TDS, NRE/NRO/FCNR, DTAA
  s.90/91, Schedule FA, 115C–115I, LRS TCS 206C(1G)), FEMA/RBI, SEBI (IA suitability & risk
  profiling, MF riskometer/categorization, PMS minimum), IRDAI (free-look, cover guidance), GST.
- `search_rules()`: deterministic keyword scoring with taxpayer-type (resident/NRI), regulator
  and tag filters. Every rule carries its official source string.

## 3. Services

| Service | State | Highlights |
|---|---|---|
| **gateway** (8080) | real | Prefix routing (ingest/audit/holdings/orchestrator), query-string + non-JSON passthrough, 502 on outage. Auth/RBAC still TODO (Plan v2 W3). |
| **orchestrator** (8081) | real | Planner templates: tax_analysis, tax_qa, tax_scenario, portfolio_analysis, financial_planning, general_qa. Executor: 6 deterministic tax tools in-process, holdings fetch/consolidate via HTTP, rules retrieval via corpus, LLM steps via model_gateway with grounding + citation-mandatory prompts. Supervisor: real run state machine (planned→executing→done/awaiting_approval/failed), guardrails check per step, audit event per step, cost/token accumulation. Critic: signal-based confidence; uncited answers or approval-required capabilities gate to human review. Endpoints: create/get/list runs, approve/reject with approver receipts, /internal/tools/tax/*. |
| **model_gateway** (8082) | real | BedrockProvider (Claude via AnthropicBedrock; bearer or key auth) → OpenAIProvider fallback chain; tier mapping small/medium/large. Streaming + zero-retention headers pending. |
| **holdings** (8083) | real (new) | CRUD + consolidation; JSONL op-log persistence; masking enforced at storage. |
| **guardrails** (8084) | real | PAN/Aadhaar/SSN/email/phone detection with masking (raw PII never echoed), prompt-injection heuristics (blocking), citation enforcement for money-bearing outputs. |
| **registry** (8085) | real (in-memory) | 8 capabilities with approval_required flags + model tiers; 13 tools with schemas. |
| **audit** (8086) | real | SHA-256 hash-chained append-only JSONL log (genesis→chain), resume-on-restart, tamper-detecting /verify, list with tenant filter. No update/delete paths. |
| **ingestion** (8087) | real | Form 16/26AS/AIS classification (weighted signatures) + regex field extraction with per-field confidence and section provenance; needs_review gating (classification <0.6 or money fields <0.7); JSON passthrough validation. OCR not yet integrated (text/JSON input). |

## 4. Frontend (apps/web)

- **Chat agent** (home + /tax/[year]): provider cascade Bedrock Nova → Anthropic → backend
  gateway (RunRequest wire format) → honest "unconfigured" system notice (never a fake answer);
  provider/model caption on replies; modes: Ask · Tax planner · Portfolio · NRI taxes ·
  Financial planning (+ tax-specific modes on the tax page); regulatory system prompts
  (IT Act / SEBI suitability / FEMA / IRDAI, section citations, no named securities,
  draft-for-licensed-review). Attach-a-document flow: .txt/.json ingested via the ingestion
  service, extracted context chip shown, summary folded into the conversation.
- **/holdings** (new): consolidation dashboard (net-worth hero, allocation bars, insurance
  cover, advisory flag cards with citations, annual-income refinement), holdings manager
  (grouped types, per-type dynamic fields, delete-with-confirm), "Analyze portfolio" and
  "Draft financial plan" actions that create orchestrator runs and render cited results —
  financial plans always route to /approvals.
- **/tax/[year]**: two-pane — live deterministic dashboard (KPI tiles with CitedAmount,
  regime comparison, debounced assumptions editor per FR-TX-12) + tax chatbot. Sample-data
  mode is explicitly badged when the backend is down.
- **/documents**: real upload → ingestion; docType + confidence bar, per-field confidence
  table, low-confidence highlighting, needs_review banner.
- **/audit**: live hash-chain viewer with verify button; honest empty state.
- **/approvals** (new): human-in-the-loop inbox — pending runs, approver identity, approve /
  reject with notes, decision receipts; failures state clearly that no decision was recorded.
- **Auth**: NextAuth credentials; scrypt-salted password hashes (legacy sha256 purged),
  `.users.json` gitignored, production requires NEXTAUTH_SECRET.
- **Design system**: all new UI on design tokens (no hardcoded colors); semantic overlay/on-dark
  vars added to globals.css; WCAG-conscious (ARIA roles on interactive components).

## 5. Trust layer (BRD BR-3/BR-4 — the non-negotiables)

- **Citations:** every deterministic figure carries its section citation end-to-end
  (calculator → orchestrator → UI CitedAmount / citation chips). LLM answers without citations
  are gated by the critic; guardrails block money-bearing outputs missing citations.
- **Human-in-the-loop:** `approval_required` capabilities (tax_analysis, filing_prep,
  financial_planning) and low-confidence runs end `awaiting_approval`; only /approvals
  (with named approver) can complete them; approvals/rejections write audit receipts.
- **Immutable audit:** every run start/step/completion/approval appends to the hash chain;
  chain verification is user-visible (/audit → Verify).
- **PII:** guardrails mask PAN/Aadhaar/SSN in flagged content; holdings masks account numbers
  at storage time.

## 6. Infra, CI, DB

- **CI** (`code/.github/workflows/ci.yml`): frontend lint/typecheck/build; backend ruff +
  strict mypy + pytest per service with py_shared on MYPYPATH (py.typed added so shared types
  are enforced); placeholder evals job.
- **docker-compose**: postgres (pgvector), redis, minio, temporal (+UI), otel-collector, and
  all 8 app services with wired env.
- **Schema** (`infra/db/schema.sql` + migrations 0001–0003): tenants/users/clients/documents/
  doc_chunks(pgvector)/engagements/obligations, orchestrator tables, hash-chain audit_events,
  8 tax tables (rules & rates seeded for AY 2025-26), holdings — all with tenant-isolation RLS.
  Note: services do not yet connect to Postgres at runtime (Plan v2 W3); stores are in-memory /
  JSONL today.

## 7. Verified end-to-end (smoke, gateway-only)

1. `POST /v1/runs` tax_analysis (₹18L salary, new regime) → deterministic compute with
   citations → `awaiting_approval` → listed in approvals → approved by named approver → `done`.
2. Audit chain: 5+ events (run_started/steps/completed/approved), `/v1/audit/verify` → intact.
3. `POST /v1/ingest` Form 16 text → classified form16 (0.8), extracted fields, needs_review.
4. `POST /v1/tools/tax/compare_regimes` → recommends new regime, saving ₹88,400 (cited).
5. Holdings: add MF + home loan + term plan → consolidation: correct net worth, all four
   advisory flags fire with citations.
6. portfolio_analysis run: holdings fetch → consolidate → rules retrieval all succeed; LLM
   step degrades gracefully without model credentials and the run gates to human review.
7. general_qa (NRI, "Is NRE FD interest taxable?") retrieves it-10-4-nre-interest,
   it-nro-taxation, fema-nri-accounts, it-10-15-fcnr — correctly NRI-filtered.

## 8. Known gaps (tracked in Plan v2)

W3: Postgres persistence + RLS enforcement, gateway authn/authz, real tenant/client model.
W4: capital-gains calculators, scenario builder UI, compliance calendar, eval golden set in CI,
model-gateway streaming + zero-retention headers. W5: Temporal durability, OTel wiring,
holdings auto-import integrations, e-filing exports, US/UK jurisdictions.
