-- Migration 0002: Seed India tax rules and rates for AY 2025-26 (FY 2024-25)
-- Sources: Finance Act 2024; Income Tax Act, 1961

INSERT INTO tax_rules (jurisdiction, assessment_year, section, category, name, body, source_citation, version)
VALUES
('IN', '2025-26', '87A', 'rebate', 'Rebate under Section 87A',
 'For resident individuals with total income up to INR 7,00,000, tax rebate of INR 25,000 or tax payable, whichever is lower.',
 'Income Tax Act, 1961, Section 87A (Finance Act 2024)', '1')
ON CONFLICT (jurisdiction, assessment_year, section, version) DO UPDATE SET body = EXCLUDED.body;

INSERT INTO tax_rules (jurisdiction, assessment_year, section, category, name, body, conditions, source_citation, version)
VALUES
('IN', '2025-26', 'standard_deduction', 'exemption', 'Standard Deduction from Salary',
 'Standard deduction from salary income: INR 50,000 under the old regime; INR 75,000 under the new regime (raised from INR 50,000 by Finance Act 2024, effective AY 2025-26).',
 '{"old_regime_cap": 50000, "new_regime_cap": 75000}'::jsonb,
 'Income Tax Act, 1961, Section 16(ia) (Finance Act 2024)', '1')
ON CONFLICT (jurisdiction, assessment_year, section, version) DO UPDATE SET body = EXCLUDED.body, conditions = EXCLUDED.conditions;

INSERT INTO tax_rules (jurisdiction, assessment_year, section, category, name, body, conditions, source_citation, version)
VALUES
('IN', '2025-26', '80C', 'deduction', 'Deduction for specified investments/expenditure',
 'Aggregate deduction up to INR 1,50,000 per year for eligible investments (PPF, ELSS, LIC, PF, tuition fees, principal repayment of home loan, etc.).',
 '{"max_amount": 150000}'::jsonb,
 'Income Tax Act, 1961, Section 80C (Finance Act 2024)', '1')
ON CONFLICT (jurisdiction, assessment_year, section, version) DO UPDATE SET body = EXCLUDED.body, conditions = EXCLUDED.conditions;

INSERT INTO tax_rules (jurisdiction, assessment_year, section, category, name, body, conditions, source_citation, version)
VALUES
('IN', '2025-26', '80D', 'deduction', 'Deduction for health insurance premium',
 'Deduction up to INR 25,000 for self, spouse and dependent children (INR 50,000 if any insured is senior citizen). Additional INR 25,000 for parents (INR 50,000 if senior citizens).',
 '{"max_self": 25000, "max_self_senior": 50000, "max_parents": 25000, "max_parents_senior": 50000}'::jsonb,
 'Income Tax Act, 1961, Section 80D (Finance Act 2024)', '1')
ON CONFLICT (jurisdiction, assessment_year, section, version) DO UPDATE SET body = EXCLUDED.body, conditions = EXCLUDED.conditions;

INSERT INTO tax_rules (jurisdiction, assessment_year, section, category, name, body, conditions, source_citation, version)
VALUES
('IN', '2025-26', '80CCD(1B)', 'deduction', 'Additional NPS deduction',
 'Additional deduction up to INR 50,000 for contribution to National Pension System (NPS) under Section 80CCD(1B).',
 '{"max_amount": 50000}'::jsonb,
 'Income Tax Act, 1961, Section 80CCD(1B) (Finance Act 2024)', '1')
ON CONFLICT (jurisdiction, assessment_year, section, version) DO UPDATE SET body = EXCLUDED.body, conditions = EXCLUDED.conditions;

INSERT INTO tax_rules (jurisdiction, assessment_year, section, category, name, body, conditions, source_citation, version)
VALUES
('IN', '2025-26', '24', 'deduction', 'Interest on housing loan',
 'Deduction up to INR 2,00,000 per year for interest on loan taken for self-occupied house property.',
 '{"max_amount": 200000}'::jsonb,
 'Income Tax Act, 1961, Section 24(b) (Finance Act 2024)', '1')
ON CONFLICT (jurisdiction, assessment_year, section, version) DO UPDATE SET body = EXCLUDED.body, conditions = EXCLUDED.conditions;

-- Old regime slabs (resident individual < 60 years)
INSERT INTO tax_rates (jurisdiction, assessment_year, regime, income_head, min_amount, max_amount, rate, cess_rate)
VALUES
('IN', '2025-26', 'old', 'salary', 0, 250000, 0, 0.04),
('IN', '2025-26', 'old', 'salary', 250000, 500000, 0.05, 0.04),
('IN', '2025-26', 'old', 'salary', 500000, 1000000, 0.20, 0.04),
('IN', '2025-26', 'old', 'salary', 1000000, NULL, 0.30, 0.04)
ON CONFLICT DO NOTHING;

-- New regime slabs (AY 2025-26)
INSERT INTO tax_rates (jurisdiction, assessment_year, regime, income_head, min_amount, max_amount, rate, cess_rate)
VALUES
('IN', '2025-26', 'new', 'salary', 0, 300000, 0, 0.04),
('IN', '2025-26', 'new', 'salary', 300000, 700000, 0.05, 0.04),
('IN', '2025-26', 'new', 'salary', 700000, 1000000, 0.10, 0.04),
('IN', '2025-26', 'new', 'salary', 1000000, 1200000, 0.15, 0.04),
('IN', '2025-26', 'new', 'salary', 1200000, 1500000, 0.20, 0.04),
('IN', '2025-26', 'new', 'salary', 1500000, NULL, 0.30, 0.04)
ON CONFLICT DO NOTHING;

-- Surcharge rates (common for both regimes in AY 2025-26)
-- Stored in surcharge_rate JSON for reference; calculator will use explicit surcharge brackets.
INSERT INTO tax_rules (jurisdiction, assessment_year, section, category, name, body, conditions, source_citation, version)
VALUES
('IN', '2025-26', 'surcharge', 'rate', 'Surcharge on income tax',
 'Surcharge applies on income tax: 10% if total income > 50L and <= 1Cr; 15% if > 1Cr and <= 2Cr; 25% if > 2Cr and <= 5Cr; 37% if > 5Cr. Marginal relief applies.',
 '{"brackets": [
    {"min": 5000000, "max": 10000000, "rate": 0.10},
    {"min": 10000000, "max": 20000000, "rate": 0.15},
    {"min": 20000000, "max": 50000000, "rate": 0.25},
    {"min": 50000000, "max": null, "rate": 0.37}
  ]}'::jsonb,
 'Income Tax Act, 1961, Section 111A/112 (Finance Act 2024)', '1')
ON CONFLICT (jurisdiction, assessment_year, section, version) DO UPDATE SET body = EXCLUDED.body, conditions = EXCLUDED.conditions;
