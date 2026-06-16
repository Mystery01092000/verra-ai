---
name: verra-security-governance
description: >
  Apply Verra's security, privacy and AI-governance guardrails. Use when reviewing features, prompts,
  data flows, or releases for HITL gates, citations, audit logging, zero-retention, and compliance.
---

# Verra security & governance

## Checklist (apply to every feature/PR)
- [ ] **Human-in-the-loop:** consequential actions (send/file/post) require explicit approval.
- [ ] **Citations:** every user-facing figure/claim shows its source; facts vs assumptions separated.
- [ ] **Audit log:** action receipt written (actor, action, sources, time, approval, rollback).
- [ ] **Zero-retention AI:** no training on customer data; provider contracts enforce no retention.
- [ ] **Access:** RBAC + tenant isolation; SSO/SCIM; least privilege.
- [ ] **Privacy:** PII minimized; data residency honored (GDPR / India DPDP).
- [ ] **Encryption:** in transit + at rest.
- [ ] **Evals:** accuracy regression suite passes before release.

## Standards
SOC 2 Type II, ISO 27001; professional-responsibility & unauthorized-practice limits
(Verra = analysis + drafts, licensed human owns advice/filings).
