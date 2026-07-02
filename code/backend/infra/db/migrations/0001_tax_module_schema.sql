-- Migration 0001: Tax module schema (India, AY 2025-26 v1)
-- idempotent: uses IF NOT EXISTS / DROP ... CASCADE where safe
--
-- NOTE: tax_computations ↔ tax_scenarios have a bidirectional FK.
-- Resolution: create tax_scenarios first (without computation_id), then
-- tax_computations (with scenario_id), then ALTER to add computation_id.

CREATE TABLE IF NOT EXISTS tax_profiles (
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

CREATE TABLE IF NOT EXISTS tax_line_items (
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

-- Create tax_scenarios FIRST (without computation_id) to break the circular FK.
CREATE TABLE IF NOT EXISTS tax_scenarios (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  client_id uuid NOT NULL,
  assessment_year text NOT NULL,
  profile_id uuid NOT NULL REFERENCES tax_profiles(id),
  name text NOT NULL,
  assumptions jsonb NOT NULL,
  is_baseline boolean DEFAULT false,
  created_by uuid REFERENCES users(id),
  created_at timestamptz DEFAULT now()
);

-- Now tax_computations can safely reference tax_scenarios.
CREATE TABLE IF NOT EXISTS tax_computations (
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

-- Add the back-reference from tax_scenarios → tax_computations (idempotent).
ALTER TABLE tax_scenarios
  ADD COLUMN IF NOT EXISTS computation_id uuid REFERENCES tax_computations(id);

CREATE TABLE IF NOT EXISTS tax_rules (
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

CREATE TABLE IF NOT EXISTS tax_rates (
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

CREATE TABLE IF NOT EXISTS dtaa_treaties (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  country_code text NOT NULL,
  article text NOT NULL,
  income_type text NOT NULL,
  rate numeric NOT NULL,
  conditions jsonb DEFAULT '{}',
  limitation_of_benefits text,
  source_text_url text
);

CREATE TABLE IF NOT EXISTS foreign_tax_credits (
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

-- RLS policies (idempotent recreation)
ALTER TABLE tax_profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_tax_profiles ON tax_profiles;
CREATE POLICY tenant_isolation_tax_profiles ON tax_profiles USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE tax_line_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_tax_line_items ON tax_line_items;
CREATE POLICY tenant_isolation_tax_line_items ON tax_line_items USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE tax_computations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_tax_computations ON tax_computations;
CREATE POLICY tenant_isolation_tax_computations ON tax_computations USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE tax_scenarios ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_tax_scenarios ON tax_scenarios;
CREATE POLICY tenant_isolation_tax_scenarios ON tax_scenarios USING (tenant_id::text = current_setting('app.tenant_id', true));

ALTER TABLE tax_rules ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_tax_rules ON tax_rules;
CREATE POLICY tenant_isolation_tax_rules ON tax_rules FOR SELECT USING (true);

ALTER TABLE tax_rates ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_tax_rates ON tax_rates;
CREATE POLICY tenant_isolation_tax_rates ON tax_rates FOR SELECT USING (true);

ALTER TABLE dtaa_treaties ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_dtaa_treaties ON dtaa_treaties;
CREATE POLICY tenant_isolation_dtaa_treaties ON dtaa_treaties FOR SELECT USING (true);

ALTER TABLE foreign_tax_credits ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_foreign_tax_credits ON foreign_tax_credits;
CREATE POLICY tenant_isolation_foreign_tax_credits ON foreign_tax_credits USING (tenant_id::text = current_setting('app.tenant_id', true));
