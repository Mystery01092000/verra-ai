---
name: verra-tax-analysis
description: >
  Run a Verra-style tax analysis for a client: ingest documents, compute the current position,
  surface opportunities, model scenarios, and produce a client-ready, cited, human-approved plan.
  Use when the task involves analyzing a 1040/return/statements, finding tax savings, or building a
  tax plan/scenario comparison.
---

# Verra tax analysis

Follow this workflow. **Never** present a tax figure without a citation, and **never** send or file
anything without a human approval step.

## 1. Ingest & understand
- Accept uploads (1040, W-2, 1099, K-1, brokerage statements, prior returns, GST/VAT returns) or pull
  from connected ledger/bank/CRM/email.
- Extract structured line items **with page-level source references and confidence scores**.
- Flag missing or inconsistent data; build a client tax profile keyed by **tax year + jurisdiction**.

## 2. Analyze current position
- Compute total tax, marginal & effective rate, income breakdown, withholdings — using **deterministic
  calculators**, not free-form LLM math.
- Cite the governing bracket/rule for the selected year and jurisdiction.

## 3. Find opportunities
- Roth conversion headroom, tax-loss harvesting, withholding/estimate gaps, credits/deductions,
  tax-advantaged accounts. Quantify estimated annual + lifetime impact for each. Cite the source.

## 4. Model scenarios
- Roth conversions/ladders, income changes, asset sales, withdrawals, life events.
- Compare ≥ 2 scenarios side by side; mark a recommended option; respect bracket thresholds/phase-outs.
- Separate **facts** from **assumptions**; let the user challenge or swap a source and re-run.

## 5. Review, approve, share
- Route for human review; capture sign-off. Only then generate the **client letter + interactive
  report + advisor talking points**. Log the action (sources + approver) to the audit trail.

## Guardrails
- Output is **analysis and drafts**, not advice. A licensed professional is responsible.
- Respect zero-retention and privacy settings; minimize PII in prompts.
