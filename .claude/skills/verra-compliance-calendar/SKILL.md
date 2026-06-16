---
name: verra-compliance-calendar
description: >
  Build/maintain Verra's multi-jurisdiction compliance calendar of filing obligations, deadlines,
  reminders, and auto-prepared drafts. Use for obligations, deadlines, or e-invoicing mandates.
---

# Verra compliance calendar

## Model
- An **Obligation** = {entity, jurisdiction, form, period, due date, status, owner, rule version}.
- Rules/deadlines are **configurable** and **versioned by year**.

## Coverage (initial)
- **US:** Form 941/1040/1120, state filings (IRS MeF export, phased).
- **UK:** VAT returns, corporation tax, statutory accounts (Companies House).
- **India:** GSTR-3B/2B, TDS, ROC/MCA filings, tax audit.
- **EU framework:** e-invoicing/e-reporting (ViDA; France 2026; Germany 2027; Poland/Belgium 2026).

## Rules
- Surface risk flags for near/overdue items; auto-prepare drafts for human approval.
- Never file without sign-off; log filing actions to the audit trail.
- Keep a jurisdiction rules pack updatable without code changes.
