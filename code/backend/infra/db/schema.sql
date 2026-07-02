-- Verra schema (excerpt) — PostgreSQL + pgvector, RLS multi-tenancy (ADR-0007/0009/0015).
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  type text NOT NULL CHECK (type IN ('firm','company','individual')),
  jurisdictions text[] NOT NULL DEFAULT '{}',
  settings jsonb NOT NULL DEFAULT '{}', created_at timestamptz DEFAULT now());

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  role text NOT NULL, sso_subject text, permissions jsonb DEFAULT '{}');

CREATE TABLE clients (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  type text NOT NULL, jurisdictions text[] DEFAULT '{}', profile jsonb DEFAULT '{}');

CREATE TABLE documents (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  client_id uuid REFERENCES clients(id),
  type text, source text, parsed jsonb, page_refs jsonb, confidence numeric, version int DEFAULT 1);

CREATE TABLE doc_chunks (             -- RAG (ADR-0013)
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, document_id uuid REFERENCES documents(id),
  content text, page int, embedding vector(1536));
CREATE INDEX ON doc_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE engagements (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, client_id uuid REFERENCES clients(id),
  type text CHECK (type IN ('tax','books','audit','compliance')), status text, deadlines jsonb);

CREATE TABLE obligations (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, client_id uuid REFERENCES clients(id),
  jurisdiction text, form text, period text, due_date date, status text, rule_version text);

-- Orchestrator
CREATE TABLE runs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, engagement_id uuid,
  module text, capability text, status text,
  budget jsonb, cost_usd numeric DEFAULT 0, tokens_in int DEFAULT 0, tokens_out int DEFAULT 0,
  trace_id text, created_at timestamptz DEFAULT now());
CREATE TABLE plans (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id uuid NOT NULL, run_id uuid REFERENCES runs(id), task_graph jsonb, template text, version text);
CREATE TABLE steps (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id uuid NOT NULL, run_id uuid REFERENCES runs(id), agent text, model text, tools text[], status text, retries int DEFAULT 0, tokens int DEFAULT 0, cost_usd numeric DEFAULT 0, output_ref text);
CREATE TABLE routing_decisions (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id uuid NOT NULL, step_id uuid REFERENCES steps(id), chosen jsonb, reason text, fallbacks_used jsonb);
CREATE TABLE agent_versions (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), name text, version text, manifest jsonb, eval_status text, lifecycle text);
CREATE TABLE tool_defs (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), name text, version text, json_schema jsonb, permissions text[], sandbox_profile text);
CREATE TABLE budgets (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id uuid NOT NULL, scope text, limits jsonb, consumed jsonb, period text);

-- Append-only, hash-chained audit (ADR-0015)
CREATE TABLE audit_events (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL, run_id uuid, actor text, action text,
  sources jsonb, provider text, cost_usd numeric, tokens int,
  approval jsonb, prev_hash text, hash text, created_at timestamptz DEFAULT now());

-- RLS: every tenant-scoped table is isolated by tenant_id = current_setting('app.tenant_id')
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_users ON users USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_clients ON clients USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_documents ON documents USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE doc_chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_doc_chunks ON doc_chunks USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE engagements ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_engagements ON engagements USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE obligations ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_obligations ON obligations USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_runs ON runs USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_plans ON plans USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE steps ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_steps ON steps USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE routing_decisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_routing_decisions ON routing_decisions USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_budgets ON budgets USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_audit_events ON audit_events USING (tenant_id::text = current_setting('app.tenant_id', true));


-- Tax module schema (India, AY 2025-26 v1)

CREATE TABLE tax_profiles (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  client_id uuid NOT NULL REFERENCES clients(id),
  assessment_year text NOT NULL,
  jurisdiction text NOT NULL DEFAULT 'IN',
  taxpayer_type text CHECK (taxpayer_type IN ('resident_ordinarily','resident_not_ordinarily','non_resident')),
  residential_status_json jsonb NOT NULL DEFAULT '{}',
  opted_new_regime boolean DEFAULT false,
  income_summary jsonb NOT NULL DEFAULT '{}',
  deductions_summary jsonb NOT NULL DEFAULT '{}',
  foreign_income_summary jsonb NOT NULL DEFAULT '{}',
  flags jsonb NOT NULL DEFAULT '{}',
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
  line_type text NOT NULL,
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
  computation_json jsonb NOT NULL,
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
  assumptions jsonb NOT NULL,
  computation_id uuid REFERENCES tax_computations(id),
  is_baseline boolean DEFAULT false,
  created_by uuid REFERENCES users(id),
  created_at timestamptz DEFAULT now()
);

CREATE TABLE tax_rules (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  jurisdiction text NOT NULL DEFAULT 'IN',
  assessment_year text NOT NULL,
  section text NOT NULL,
  category text NOT NULL CHECK (category IN ('deduction','exemption','rate','rebate','residency_test','procedure')),
  name text NOT NULL,
  body text NOT NULL,
  conditions jsonb DEFAULT '{}',
  effective_from date,
  effective_to date,
  source_url text,
  source_citation text NOT NULL,
  version text NOT NULL,
  UNIQUE(jurisdiction, assessment_year, section, version)
);

CREATE TABLE tax_rates (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  jurisdiction text NOT NULL DEFAULT 'IN',
  assessment_year text NOT NULL,
  regime text NOT NULL CHECK (regime IN ('old','new')),
  income_head text NOT NULL,
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

ALTER TABLE tax_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tax_profiles ON tax_profiles USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE tax_line_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tax_line_items ON tax_line_items USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE tax_computations ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tax_computations ON tax_computations USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE tax_scenarios ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tax_scenarios ON tax_scenarios USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE tax_rules ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tax_rules ON tax_rules FOR SELECT USING (true);

ALTER TABLE tax_rates ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tax_rates ON tax_rates FOR SELECT USING (true);

ALTER TABLE dtaa_treaties ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_dtaa_treaties ON dtaa_treaties USING (true);

ALTER TABLE foreign_tax_credits ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_foreign_tax_credits ON foreign_tax_credits USING (tenant_id::text = current_setting('app.tenant_id', true));


-- Holdings consolidation (assets, liabilities, insurance) — account numbers stored masked only
CREATE TABLE holdings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  client_id uuid NOT NULL REFERENCES clients(id),
  type text NOT NULL CHECK (type IN (
    'mutual_fund','stock','bond','fixed_deposit','recurring_deposit','ppf','epf','nps',
    'insurance_life','insurance_health','insurance_ulip',
    'loan_home','loan_personal','loan_vehicle','loan_education',
    'real_estate','gold','cash','other')),
  name text NOT NULL,
  institution text,
  current_value numeric(15,2) NOT NULL CHECK (current_value >= 0),
  invested_value numeric(15,2),
  units numeric,
  account_masked text,
  currency text NOT NULL DEFAULT 'INR',
  as_of_date date,
  premium_annual numeric(15,2),
  sum_assured numeric(15,2),
  outstanding_amount numeric(15,2),
  interest_rate numeric,
  emi numeric(15,2),
  maturity_date date,
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE holdings ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_holdings ON holdings USING (tenant_id::text = current_setting('app.tenant_id', true));
