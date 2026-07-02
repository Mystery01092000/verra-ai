-- 0003: Holdings consolidation (assets, liabilities, insurance).
-- Account numbers are stored masked only (last 4 characters) — never in full.

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
