# Verra Platform Plan v2 — Conversational Tax, Compliance & Wealth Consolidation Agent (India-first)

**Date:** 2026-07-03 · **Supersedes:** `Verra_Tax_Module_Implementation_Plan.md` (which remains the
detailed spec for the tax calculators) · **Status:** Approved direction, implementation in progress.

## 1. Revised product thesis

Verra v2 is a **chat-first agent** for Indian residents and NRIs that unifies:

1. **Taxation** — deterministic computation (liability, regime comparison, salary exemptions,
   TDS reconciliation, advance tax), filing preparation, and cited Q&A.
2. **Compliance** — a rules store spanning the Income-tax Act, SEBI regulations, FEMA/RBI
   (NRI money movement), IRDAI (insurance), and GST; every answer grounded on retrieved rules
   with section-level citations.
3. **Holdings consolidation** — a single ledger of the client's complete financial life:
   mutual funds, stocks, bonds, deposits (FD/RD/PPF/EPF/NPS), insurance (life/health/ULIP),
   loans (home/personal/vehicle/education), real estate, gold, cash — with deterministic
   net-worth, allocation, leverage and insurance-adequacy analytics.
4. **Financial planning** — LLM-drafted, rules-cited plans built strictly on deterministic
   consolidation + calculator outputs, always gated behind human (CA / SEBI-registered IA)
   approval.

The chat surface is the primary interface: conversation, document upload (ingested once,
reused everywhere), client-stated facts, and actions (compute, analyze, plan, approve) all flow
through the same agent loop.

**Unchanged non-negotiables** (BRD/PRD): human-in-the-loop, citations on every figure,
immutable audit log, deterministic math (never LLM arithmetic), jurisdiction/year-versioned
rules, tenant isolation.

## 2. What the review found (and how v2 corrects it)

The 2026-07-03 verification (`Verra_BRD_PRD_Verification_2026-07-03.md`) found the deterministic
tax engine solid but every LLM flow, guardrail, audit write and ingestion path stubbed, plus an
India-first pivot the BRD/PRD never recorded. v2 makes the pivot official: **India (residents +
NRIs) is the MVP jurisdiction**; US/UK remain roadmap. Wave-1 remediation (same date) closed the
stubs: real orchestrator run lifecycle, model-gateway wiring, hash-chained audit, PII/injection
guardrails, Form 16/26AS/AIS extraction, approvals UI. This plan builds on that foundation.

## 3. Architecture additions (v2)

| Component | Type | Purpose |
|---|---|---|
| `verra_shared.holdings` | shared package | Holding models + deterministic `consolidate()` (net worth, allocation, flags with citations) |
| `services/holdings` (8083) | microservice | CRUD + consolidation API; JSONL persistence now, Postgres (`holdings` table w/ RLS, migration 0003) next |
| `verra_shared.rules` | shared package | Versioned regulatory corpus (Income-tax / SEBI / FEMA / IRDAI / GST / MCA) + deterministic `search_rules()` for residents & NRIs |
| Orchestrator capabilities | orchestrator | `portfolio_analysis`, `financial_planning`, `general_qa`; tools `holdings:fetch`, `holdings:consolidate`, real `tax:retrieve_tax_rules` |
| Regulator-aware prompts | orchestrator | System prompt binds the agent to IT Act / SEBI suitability / FEMA / IRDAI framing, section citations mandatory, no security-specific recommendations, draft-only outputs |
| Frontend `/holdings` | web | Consolidation dashboard + holdings manager + "Analyze portfolio" / "Draft financial plan" (runs through the agent, approval-gated) |
| Chat modes | web | Ask · Tax planner · Portfolio · NRI taxes · Financial planning; attach-document-to-chat ingestion flow |

Golden rules unchanged: public traffic only via gateway; modules reach models only via
orchestrator → model_gateway; every run writes hash-chained audit events.

## 4. Compliance posture for advisory features (important)

- **SEBI IA Regulations 2013**: investment *advice* requires a registered adviser. Verra outputs
  are **drafts for a licensed professional**; `financial_planning` runs are hard-gated
  (`approval_required=true`) and the UI says so explicitly. The agent never names specific
  securities/schemes.
- **NRI coverage**: residential-status rules (s.6(1), 6(1A)), s.195 TDS, NRE/NRO/FCNR treatment,
  DTAA relief (s.90/91), LRS TCS (206C(1G)) are first-class rules in the corpus; taxpayer-type
  filters ensure NRI questions retrieve NRI-applicable rules.
- **Insurance flags** cite their basis honestly (regulatory rules vs industry heuristics are
  labeled differently).

## 5. Phased roadmap (v2)

| Phase | Scope | Status |
|---|---|---|
| **W1 — Remediation** | Real run lifecycle, LLM wiring, audit chain, guardrails, ingestion, approvals & pages | ✅ done 2026-07-03 |
| **W2 — Consolidation & planning** | Holdings engine + service, rules corpus, portfolio/planning capabilities, chat modes, doc-in-chat | 🔄 in progress |
| **W3 — Persistence & identity** | Postgres repositories (runs, audit, holdings, tax profiles) with RLS enforced via `app.tenant_id`; gateway JWT auth; per-tenant rate limits; real client/tenant model replacing demo constants | next |
| **W4 — Depth** | Capital-gains calculators (111A/112A/54*), scenario builder UI, compliance calendar (obligations seeded: ITR/advance-tax/GSTR deadlines), eval harness with CPA-verified golden cases in CI, model-gateway streaming + zero-retention headers | next |
| **W5 — Scale** | Temporal durable runs, OTel traces wired, broker/AMC/CDSL integrations for holdings auto-import, e-filing prep exports, US/UK jurisdictions | later |

## 6. Success criteria for W2 (acceptance)

- A client can, in one chat session: upload a Form 16, ask a grounded question about it, add
  holdings, ask "how is my portfolio doing", and request a financial plan — every reply cited,
  every figure deterministic, plan gated behind /approvals, all of it in the audit chain.
- `search_rules("nri fd interest", taxpayer_type="nri")` returns only NRI/all rules with real
  sections; no rule invents thresholds.
- Full CI green (ruff, strict mypy, 190+ backend tests, frontend build/typecheck/lint) and the
  e2e smoke script passes gateway-only (no direct service access).
