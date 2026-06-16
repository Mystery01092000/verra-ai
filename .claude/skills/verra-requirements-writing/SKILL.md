---
name: verra-requirements-writing
description: >
  Author or update Verra requirements documents (BRD, PRD, specs) with consistent structure and IDs.
  Use when writing/editing business or product requirements, success metrics, or acceptance criteria.
---

# Verra requirements writing

## Conventions
- **BRD** answers *why* (business): vision, market, competitors, stakeholders/personas, scope,
  business requirements (`BR-n`), success metrics, risks, regulatory, roadmap, business model.
- **PRD** answers *what* (product): overview, goals/non-goals, personas/JTBD, journeys, IA,
  functional requirements by module (`FR-XX-n`), AI/agent design, data model, integrations, NFRs,
  metrics, release plan, acceptance criteria.
- **Plan** answers *how/when*: phases, workstreams, team, architecture, Figma build, risks, checklist.

## Rules
- Every requirement: unique ID, single testable statement, MoSCoW priority (Must/Should/Could/Won't).
- Acceptance criteria in Given/When/Then form for MVP features.
- Reflect the product principles: human-in-the-loop, cited & auditable, security-first, jurisdiction-aware.
- Keep figures directional and cite sources (`docs/research-sources.md`); mark "Verra = analysis+drafts".
- Generate `.docx` with the docx tooling; keep cover + TOC + headers/footers consistent across docs.
