# Verra — Tax Module Implementation Plan

> **Scope:** Indian residents and NRIs with India-sourced income, Phase 1 of the Verra Tax product.  
> **Goal:** A client can upload Indian tax documents, chat about tax rules/planning, and get deterministic tax computations — all through the orchestrator with guardrails, citations, human approval, and audit.  
> **Status:** Planning complete; ready for Sprint breakdown.

---

## 1. Executive Summary

The Tax module is the first domain module built on top of the Verra common orchestrator. It targets two taxpayer personas under the Indian Income Tax Act, 1961:

1. **Indian resident** (ordinarily / not-ordinarily resident)
2. **NRI-to-India** (non-resident with India-sourced income, DTAA exposure, foreign tax credits)

The module is intentionally **not a generic chatbot**. It is an orchestrated workflow that combines:
- Document ingestion and extraction (Form 16, 26AS, AIS, bank statements, capital-gains statements, foreign income docs)
- Deterministic tax calculators (old vs new regime, capital gains, NRI rates, TDS reconciliation, advance tax)
- A conversational agent grounded in uploaded documents and versioned statutory rules
- Human-in-the-loop approval for consequential outputs
- Immutable audit receipts

Every numeric output must cite a source document page or a versioned rule card. No tax liability figure is ever produced by an LLM.

---

## 2. Key Requirements

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| **TAX-REQ-001** | Tax work routes through the common orchestrator (`module: tax`); no Tax service calls models/tools directly. | P0 | ADR-0001 |
| **TAX-REQ-002** | Support two personas: **Indian resident** and **NRI-to-India**, with residential status determined under Section 6 of the Income Tax Act. | P0 | Drives profile schema and rule selection |
| **TAX-REQ-003** | Ingest Indian tax documents: Form 16/16A, Form 26AS, AIS, ITR-V, bank statements, capital-gains statements, rental agreements, foreign income docs, foreign tax paid certificates, NRE/NRO interest statements. | P0 | Each doc type needs parser contract |
| **TAX-REQ-004** | Extract normalized income line items across all heads: Salary, House Property, Capital Gains, Business/Profession, Other Sources, plus foreign income. Every extraction carries `doc_id`, `page`, `confidence`. | P0 | Required for deterministic computation |
| **TAX-REQ-005** | Compute Indian tax liability **deterministically**: old/new regime slabs, surcharge, cess, rebate 87A. | P0 | No LLM math |
| **TAX-REQ-006** | Compute NRI tax liability: Section 115E rates, DTAA benefit, foreign tax credit (Section 90/91), special rates on interest/royalty/FTS. | P0 | v1 covers common cases only |
| **TAX-REQ-007** | Apply common deductions/exemptions: 80C, 80D, 80CCD(1B), 80G, 80TTA/80TTB, HRA, LTA, Section 24, Section 80E, NPS. | P0 | |
| **TAX-REQ-008** | Reconcile TDS/TCS from Form 26AS and AIS against computed tax and flag gaps. | P1 | |
| **TAX-REQ-009** | Calculate advance-tax instalments and due dates under Section 211, flag Sections 234B/234C interest. | P1 | |
| **TAX-REQ-010** | Provide a conversational tax agent that answers Indian tax-rule and planning questions, with citations. | P0 | |
| **TAX-REQ-011** | Support scenario modeling: regime switch, 80C changes, capital-gains timing, RSU/ESOP liquidation, property sale (54/54F/54EC). | P1 | |
| **TAX-REQ-012** | Generate draft tax computation + client report only after human approval; write an audit receipt. | P0 | |
| **TAX-REQ-013** | Maintain versioned tax rules per assessment year and jurisdiction. | P0 | Rule changes must not corrupt prior-year computations |
| **TAX-REQ-014** | Integrate with future modules: pull book-closed figures from Books & Close, feed workpapers to Audit, sync obligations to Compliance. | P2 | Contract-first |
| **TAX-REQ-015** | Apply India-specific privacy guardrails: PII/DLP redaction, DPDP awareness, zero-retention provider settings, RLS tenant isolation. | P0 | |
| **TAX-REQ-016** | Chat conversations are audit-logged and resumable across sessions. | P1 | |
| **TAX-REQ-017** | Mobile-responsive upload, chat, and scenario flows. | P1 | |

---

## 3. Data Model Extensions

Extend `code/backend/infra/db/schema.sql` with the following tenant-isolated tables. All tables need RLS policies mirroring the existing pattern (`tenant_id::text = current_setting('app.tenant_id', true)`).

### 3.1 Core Tax tables

```sql
CREATE TABLE tax_profiles (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  client_id uuid NOT NULL REFERENCES clients(id),
  assessment_year text NOT NULL,
  jurisdiction text NOT NULL DEFAULT 'IN',
  taxpayer_type text CHECK (taxpayer_type IN ('resident_ordinarily','resident_not_ordinarily','non_resident')),
  residential_status_json jsonb NOT NULL DEFAULT '{}',   -- days_in_india, citizenship, prior status
  opted_new_regime boolean DEFAULT false,
  income_summary jsonb NOT NULL DEFAULT '{}',
  deductions_summary jsonb NOT NULL DEFAULT '{}',
  foreign_income_summary jsonb NOT NULL DEFAULT '{}',
  flags jsonb NOT NULL DEFAULT '{}',                      -- missing docs, conflicts, opportunities
  updated_at timestamptz DEFAULT now(),
  UNIQUE(tenant_id, client_id, assessment_year, jurisdiction)
);

CREATE TABLE tax_line_items (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  client_id uuid NOT NULL REFERENCES clients(id),
  assessment_year text NOT NULL,
  document_id uuid REFERENCES documents(id),
  head text NOT NULL CHECK (head IN ('salary','house_property','capital_gains','business','other_sources','foreign')),
  line_type text NOT NULL,                                -- e.g., basic_salary, hra, interest_savings, stcg_equity
  description text,
  amount numeric(15,2) NOT NULL,
  currency text NOT NULL DEFAULT 'INR',
  foreign_amount numeric(15,2),
  foreign_currency text,
  page int,
  bbox jsonb,
  confidence numeric(3,2) CHECK (confidence BETWEEN 0 AND 1),
  extracted jsonb NOT NULL DEFAULT '{}',
  verified boolean DEFAULT false,
  verified_by uuid REFERENCES users(id),
  verification_note text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE tax_computations (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  client_id uuid NOT NULL,
  assessment_year text NOT NULL,
  run_id uuid REFERENCES runs(id),
  profile_id uuid REFERENCES tax_profiles(id),
  scenario_id uuid REFERENCES tax_scenarios(id),
  inputs_hash text NOT NULL,
  regime text NOT NULL CHECK (regime IN ('old','new')),
  taxpayer_type text NOT NULL,
  income_summary jsonb NOT NULL,
  deduction_summary jsonb NOT NULL,
  taxable_income numeric(15,2) NOT NULL,
  tax_liability numeric(15,2) NOT NULL,
  surcharge numeric(15,2) NOT NULL,
  cess numeric(15,2) NOT NULL,
  rebate_87a numeric(15,2) NOT NULL,
  tds_tcs_credit numeric(15,2) NOT NULL,
  advance_tax_paid numeric(15,2) NOT NULL,
  foreign_tax_credit numeric(15,2) NOT NULL DEFAULT 0,
  net_tax_refund_due numeric(15,2) NOT NULL,
  computation_json jsonb NOT NULL,                        -- full working
  citations jsonb NOT NULL,
  status text NOT NULL CHECK (status IN ('draft','approved','filed')),
  created_at timestamptz DEFAULT now()
);

CREATE TABLE tax_scenarios (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  client_id uuid NOT NULL,
  assessment_year text NOT NULL,
  profile_id uuid NOT NULL REFERENCES tax_profiles(id),
  name text NOT NULL,
  assumptions jsonb NOT NULL,                             -- diff from base line items
  computation_id uuid REFERENCES tax_computations(id),
  is_baseline boolean DEFAULT false,
  created_by uuid REFERENCES users(id),
  created_at timestamptz DEFAULT now()
);
```

### 3.2 Knowledge tables

```sql
CREATE TABLE tax_rules (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  jurisdiction text NOT NULL DEFAULT 'IN',
  assessment_year text NOT NULL,
  section text NOT NULL,                                  -- e.g., "80C", "111A", "87A"
  category text NOT NULL CHECK (category IN ('deduction','exemption','rate','rebate','residency_test','procedure')),
  name text NOT NULL,
  body text NOT NULL,                                     -- plain-language rule + conditions
  conditions jsonb DEFAULT '{}',
  effective_from date,
  effective_to date,
  source_url text,
  source_citation text NOT NULL,                          -- "Income Tax Act, 1961, Section 80C"
  version text NOT NULL,
  UNIQUE(jurisdiction, assessment_year, section, version)
);

CREATE TABLE tax_rates (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  jurisdiction text NOT NULL DEFAULT 'IN',
  assessment_year text NOT NULL,
  regime text NOT NULL CHECK (regime IN ('old','new')),
  income_head text NOT NULL,                              -- salary, ltcg_equity_112A, stcg_equity_111A, etc.
  min_amount numeric,
  max_amount numeric,
  rate numeric NOT NULL,
  surcharge_rate jsonb DEFAULT '{}',
  cess_rate numeric DEFAULT 0.04
);

CREATE TABLE dtaa_treaties (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  country_code text NOT NULL,
  article text NOT NULL,
  income_type text NOT NULL,
  rate numeric NOT NULL,
  conditions jsonb DEFAULT '{}',
  limitation_of_benefits text,
  source_text_url text
);

CREATE TABLE foreign_tax_credits (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  client_id uuid NOT NULL,
  assessment_year text NOT NULL,
  country text NOT NULL,
  income_head text NOT NULL,
  foreign_income numeric(15,2) NOT NULL,
  foreign_tax_paid numeric(15,2) NOT NULL,
  credit_claimed numeric(15,2) NOT NULL,
  supporting_doc_id uuid REFERENCES documents(id)
);
```

### 3.3 Document taxonomy

Extend `documents.type` enum to include:

```sql
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'form_16';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'form_16a';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'form_26as';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'ais';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'itr_v';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'bank_statement';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'capital_gains_statement';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'rental_agreement';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'foreign_income';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'foreign_tax_certificate';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'nre_nro_statement';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'donation_receipt';
```

Also extend `obligations` with India filing events (ITR due date, advance-tax instalments, TDS return deadlines, AIS correction window).

---

## 4. Orchestrator Design for Tax

### 4.1 Module/capability contract

All Tax work is a `RunRequest` with `module: "tax"`. Capabilities registered in the registry service:

| Capability | Purpose | Typical trigger |
|---|---|---|
| `tax_analysis` | End-to-end ingestion → computation → opportunities → report | Upload documents + click "Analyze" |
| `tax_qa` | Answer Indian tax rules and planning questions | Chat message |
| `tax_scenario` | Compare old vs new regime or what-if assumptions | Scenario modeling UI |
| `document_reconcile` | Cross-check Form 16, 26AS, AIS, bank interest | Reconcile button |
| `filing_prep` | Assemble draft ITR schedules and review package | End-of-year run |

### 4.2 Planner templates

The orchestrator planner emits typed DAGs. Example `tax_analysis` DAG:

```text
1. classify_documents      (ingestion)
2. parse_documents         (ingestion)
3. extract_line_items      (ingestion)
4. human_review_low_conf   (approval gate if confidence < 0.8)
5. build_tax_profile       (deterministic aggregation)
6. retrieve_tax_rules      (RAG)
7. compute_income_heads    (calculator tools, parallel)
8. compute_deductions      (calculator tool)
9. compute_tax_liability   (calculator tool)
10. reconcile_tds          (calculator tool)
11. detect_opportunities   (agent reasoning, constrained)
12. generate_draft_report  (templated generation)
13. human_approval         (approval gate)
14. emit_audit_receipt     (audit service)
```

Planner templates are stored in a new `plan_templates` table so Audit/Books/Compliance can register equivalent templates without changing orchestrator code.

### 4.3 Registry tools

| Tool | Input | Output | Deterministic? |
|---|---|---|---|
| `parse_indian_tax_document` | `document_id`, `doc_type` | normalized extraction JSON | No (confidence scored) |
| `retrieve_tax_rules` | `query`, `assessment_year`, `jurisdiction` | rule cards + citations | No (retrieval) |
| `retrieve_client_docs` | `client_id`, `doc_types[]`, `assessment_year` | chunks + structured fields | No (retrieval) |
| `compute_income_head` | `client_id`, `assessment_year`, `head`, `regime` | head-level income/loss | **Yes** |
| `compute_deductions` | `client_id`, `assessment_year`, `regime` | aggregate deductions | **Yes** |
| `compute_tax_liability` | `client_id`, `assessment_year`, `regime`, `taxpayer_type` | tax, surcharge, cess, rebate | **Yes** |
| `compute_capital_gains` | transactions array | STCG/LTCG per asset class | **Yes** |
| `compute_house_property` | rent, municipal tax, interest, self_occupied | Section 23/24 income/loss | **Yes** |
| `compute_salary_exemptions` | basic, hra, rent, city, lta | HRA, LTA, standard deduction | **Yes** |
| `compute_nri_tax` | residential status, India income, foreign income, treaty | Section 115E, DTAA relief, FTC | **Yes** |
| `reconcile_tds` | Form 16, 26AS, AIS amounts | matched/unmatched TDS | **Yes** |
| `compute_advance_tax` | projected liability, paid, date | instalment schedule + 234C | **Yes** |
| `compare_regimes` | `client_id`, `assessment_year` | old vs new delta | **Yes** |
| `build_scenario` | `base_profile_id`, `overrides` | recomputed computation | **Yes** |
| `determine_residential_status` | days in India, citizenship, prior status | resident/RNOR/NRI | **Yes** |
| `generate_draft_output` | `run_id`, `output_type` | prose report / ITR schedule | No (templated) |

### 4.4 Critic/guardrails rules for Tax

- **L4 Critic:** every numeric output must cite a document page or `tax_rules.id`; numeric values must match deterministic calculator output.
- **Output guardrails:** block uncited tax advice; refuse speculative filing positions; flag "I am not a substitute for a CA" disclaimer on planning answers.
- **Input guardrails:** redact PAN/Aadhaar from prompts; block prompt injection; validate `tenant_id` and `assessment_year`.

### 4.5 Extensibility for future modules

The orchestrator remains module-agnostic. Future modules register their own capabilities, planner templates, and tools in the registry. The only shared contract is the `RunRequest` shape:

```json
{
  "tenantId": "...",
  "module": "tax" | "books" | "audit" | "compliance" | "assistant",
  "capability": "...",
  "input": {},
  "contextRefs": ["doc_1", "doc_2"],
  "budget": {"maxUsd": 2.0, "maxTokens": 50000}
}
```

---

## 5. Knowledge Management

### 5.1 Knowledge layers

| Layer | Content | Management |
|---|---|---|
| **Statutory rules** | Income Tax Act 1961, annual Finance Acts, CBDT circulars | `tax_rules` + `tax_rates` tables; versioned by assessment year; updated by rule-admin workflow |
| **DTAA treaties** | India tax treaties with US, UK, UAE, Singapore, etc. | `dtaa_treaties` table; referenced deterministically by country + income type |
| **Client documents** | Form 16, 26AS, AIS, bank statements, etc. | Ingestion → `documents` + `doc_chunks` (pgvector); retrieval returns doc_id + page |
| **Deterministic calculators** | Tax math, slabs, indexation, TDS reconciliation | Python modules versioned by assessment year; unit tested against CA fixtures |
| **Planning playbooks** | Common scenarios, few-shot examples | Curated, human-reviewed prompt fragments; not a source of truth for figures |

### 5.2 Rule update workflow

1. Tax team or regulatory monitoring flags a Finance Act change.
2. Insert new `tax_rules` / `tax_rates` rows with `effective_from` and new `version`.
3. Run regression eval against prior-year golden fixtures.
4. Mark old rules `effective_to` but never delete them.

### 5.3 Retrieval strategy

- **Structured queries** for `tax_rules` and `tax_rates` (by section, assessment year, jurisdiction).
- **Vector search** over `doc_chunks` for document-grounded questions and CBDT circulars.
- **Hybrid rerank:** statute rules > circulars > client documents.

---

## 6. Ingestion Pipeline

### 6.1 Document upload flow

```text
UI upload → gateway → ingestion service → S3/MinIO → classify → OCR/parse → extract → normalize → line items → confidence gate → compute
```

### 6.2 Pipeline stages

| Stage | Details |
|---|---|
| **Upload** | Presigned S3/Minio URLs; whitelist PDF/PNG/JPEG/CSV/XLSX; 25 MB max; virus scan stub |
| **Classify** | Vision/text classifier picks doc type and resident/NRI flag; fallback to user selection |
| **OCR / parse** | Layout-aware OCR; table extraction for Form 16/26AS/AIS; bank statement parser |
| **Extract** | Per-doc-type JSON schema extraction; outputs candidates with `page` + `bbox` |
| **Normalize** | Map to `tax_line_items` schema; detect duplicate/conflicting TDS; convert to INR |
| **Confidence gate** | Items below 0.8 confidence or conflicts pause at `awaiting_approval` |
| **Human review** | Inline line-item editor; edits are audit-logged |
| **Compute** | Deterministic calculators called by orchestrator |

### 6.3 Extraction targets per doc type

| Document | Extracted fields |
|---|---|
| Form 16 | employer PAN/TAN, gross salary, HRA, Section 16 deductions, TDS |
| Form 26AS | TDS/TCS credits, advance tax, self-assessment tax, refund, SFT |
| AIS | additional income (interest, dividends), SFT |
| Bank statements | interest income, large transactions |
| Capital gains statements | STCG/LTCG with dates, buy/sell value, expenses, FMV |
| Rental agreements | rent received, municipal taxes, ownership share |
| Foreign income docs | foreign salary, dividends, tax paid abroad, DTAA position |

---

## 7. Frontend / Chatbot UX

### 7.1 Routes/screens

| Route | Purpose |
|---|---|
| `/tax/[year]` | Tax workspace dashboard |
| `/tax/[year]/documents` | Upload + document list + extraction status |
| `/tax/[year]/review` | Human review of low-confidence line items |
| `/tax/[year]/scenario` | Side-by-side scenario modeling |
| `/tax/[year]/chat` | Full-page assistant history |
| `/approvals` | Cross-module approval inbox |

### 7.2 Key components

- `TaxDashboard` — KPI tiles (tax payable, effective rate, refund, TDS claimed), all cited.
- `IncomeBreakdown` — per-head income table with citations.
- `DocumentUploader` — drag-drop with doc-type hints and progress.
- `LineItemEditor` — inline editable fields keeping original OCR text + reviewer note.
- `ScenarioBuilder` — duplicate baseline, edit assumptions, compare.
- `AssistantThread` — streaming chat with cited chips, follow-up suggestions.
- `ApproveBar` — sticky action bar for approval gates.

### 7.3 Approval gates in UI

| Action | Trigger |
|---|---|
| Accept low-confidence extraction | confidence < 0.8 or conflict detected |
| Compute tax | first computation per AY |
| Promote scenario to baseline | scenario differs from baseline |
| Generate client report | any computation result |
| E-filing handoff | final draft ready |

### 7.4 Citation UX

Every money value uses a `CitedAmount` component:
- Hover reveals doc name, page, extracted snippet.
- Low confidence: amber outline + "Needs review".
- Missing citation: red outline + "No source"; blocked from computation.

---

## 8. Implementation Roadmap

### Phase 1 — Foundation (2–3 weeks)

1. **Tax schema migration** — add `tax_profiles`, `tax_line_items`, `tax_computations`, `tax_scenarios`, `tax_rules`, `tax_rates`, `dtaa_treaties`, `foreign_tax_credits`; extend `documents.type` and `obligations`; add RLS policies.
2. **Seed AY 2025-26 rules** — old/new regime slabs, surcharge, cess, rebate 87A, common sections.
3. **Document parser contracts** — JSON schemas for Form 16, 26AS, AIS, bank statements, capital-gains statements.
4. **Deterministic calculator suite v1** — income heads, deductions, tax liability, regime comparison.

### Phase 2 — Orchestrator integration (2–3 weeks)

5. **Registry tax capabilities/tools** — register agents and tools in the registry service.
6. **Planner templates** — `tax_analysis`, `tax_qa`, `tax_scenario`, `document_reconcile`.
7. **Ingestion extraction** — classify, OCR, extract, normalize into `tax_line_items`.
8. **RAG retrieval tools** — `retrieve_tax_rules` + `retrieve_client_docs` backed by pgvector.
9. **End-to-end tax_analysis run** — plan → route → execute → critic → approval gate → audit receipt.

### Phase 3 — Frontend + chat (2–3 weeks)

10. **Tax dashboard** — workspace with KPIs, income breakdown, citations.
11. **Document upload + review queue** — upload, status, low-confidence editor.
12. **Floating assistant** — streaming chat with citations and follow-ups.
13. **Scenario modeling** — side-by-side compare with deterministic recompute.
14. **Approval UX** — inline approve/reject with audit receipt preview.

### Phase 4 — NRI + advanced features (2–3 weeks)

15. **NRI engine** — residential status, Section 115E, DTAA lookup, foreign tax credit.
16. **TDS reconciliation** — cross-check Form 16, 26AS, AIS.
17. **Advance tax calculator** — instalments + 234B/234C interest.
18. **Opportunity detection** — regime switch, 80C headroom, loss harvesting, 54/54F/54EC.

### Phase 5 — Trust + eval (ongoing)

19. **Golden eval set** — resident + NRI fixtures; numeric accuracy = 100%, citation recall ≥ 95%.
20. **Guardrail red-team** — PAN/Aadhaar redaction, injection resistance, uncited-number blocking.
21. **RLS tests** — cross-tenant read denied on all new tables.
22. **Module integration hooks** — stable JSON schema for Books & Close, Audit, Compliance.

---

## 9. Dependencies on Core Platform

| Dependency | Why it blocks Tax | Relevant stories |
|---|---|---|
| Orchestrator core (Supervisor, Planner, Router, Executor, Critic) | Tax runs are orchestrated DAGs | VERRA-008–013 |
| Registry service | Tax capabilities must be discoverable | VERRA-010 |
| Model gateway + fallback chain | Resilient LLM calls for extraction/QA | VERRA-012 |
| Ingestion / RAG pipeline | Document grounding and citations | VERRA-022–023 |
| Guardrails | PII/DLP, citation enforcement, numeric checks | VERRA-014–015 |
| Human approval gate | Filing drafts/reports require explicit approval | VERRA-016 |
| Audit service | Immutable receipts for every run | VERRA-017 |
| Budget/token manager | Cost caps on long runs | VERRA-018 |
| Gateway authN/Z + tenant resolution | Sensitive PII requires tenant isolation | VERRA-007 |
| Eval harness | Regression testing | VERRA-020 |

**Definition of ready for Phase 1:** VERRA-005 through VERRA-018 and VERRA-022/023 are merged and the orchestrator can execute a `tax_analysis` run end-to-end with mocked extraction.

---

## 10. Risks and Validation

| Risk | Mitigation | Validation |
|---|---|---|
| OCR errors on poor-quality Indian PDFs | Confidence scoring + human review; layout-aware OCR | Golden set field-level F1 |
| LLM math or hallucinated advice | Deterministic calculators; critic numeric cross-check; guardrails block uncited figures | Red-team prompts; eval harness |
| Regulatory churn | Version rules by assessment year; annual update workflow | Year-over-year regression tests |
| NRI / DTAA complexity | v1 scopes common cases; edge cases route to human reviewer | NRI fixture set + CPA review |
| Cross-tenant data leakage | RLS on every new table; ingestion sets `app.tenant_id` | Multi-tenant integration tests |
| Approval latency | Approval only on consequential outputs; batch review mode | Load test approval queue |
| Integration fragility with future modules | Stable `tax_computations` JSON schema; contract tests | Stub integration tests |

### Success criteria

- [ ] All calculators pass 100+ CPA-verified fixtures.
- [ ] End-to-end `tax_analysis` run produces cited, approved computation with audit receipt.
- [ ] Golden eval set: citation recall ≥ 95%, numeric accuracy = 100%, hallucination rate < 2%.
- [ ] Guardrail suite blocks PAN/Aadhaar leakage and prompt injection.
- [ ] RLS tests prove tenant-A cannot read tenant-B tax data.
- [ ] Frontend scenario comparison updates in < 2 seconds.
- [ ] Registry can register a stub Audit agent without orchestrator code change.

---

## 11. Next Immediate Actions

1. Create the Tax schema migration and seed AY 2025-26 rules/rates.
2. Define JSON schemas for the first three document types: Form 16, Form 26AS, AIS.
3. Implement the first deterministic calculator: `compute_tax_liability` (old vs new regime).
4. Register the first Tax capability (`tax_analysis`) and tool schemas in the registry service.
5. Add a planner template for `tax_analysis`.
6. Build one frontend screen: the Tax dashboard shell with design-system tokens.

For the latest blocker fixes and current project state, see `docs/Active_Implementation_Log.md`.
