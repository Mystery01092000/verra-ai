# CLAUDE.md — Verra project context

Verra is a concept for an **AI engine across accounting, tax, audit & compliance**, delivered as a
**multi-tenant** platform (firms · companies · individuals) for **multiple jurisdictions**
(US is the MVP; UK and India next). The **MVP focus is Tax** (planning + filing preparation).
The UI/UX is modeled on **ideation**.

## Non-negotiable product principles (apply to all code, copy, and designs)
- **Human-in-the-loop:** AI prepares; a licensed human approves anything sent, filed, or relied upon.
- **Cited & auditable:** every answer shows inline source citations; every action writes to an
  immutable audit log with an action receipt (what changed, sources, agent, time, rollback).
- **Security & privacy first:** zero-retention with model providers; no training on customer data;
  encryption; RBAC; tenant isolation.
- **One ingestion, many uses:** documents/data are parsed once and reused across modules.
- **Jurisdiction-aware:** rules, forms, deadlines are configurable and versioned by tax year.

## Design system (source of truth: design/verra-prototype.html)
- Accent **#5566FF** (indigo/periwinkle); gradient **#8A92FF → #4F46E5**; ink **#111114**; cream **#F5F5F5**.
- Display type: ultra-bold grotesque (KMR Waldenburg → **Archivo 900**). Body: **Inter**. Serif accent: **Fraunces**.
- Buttons: black pill, solid-periwinkle CTA, black "Ask Verra" sparkle. Radius: cards 16–22px, buttons 8–10px.
- Use design tokens from `design/design-tokens.css` / `.json` — **never hardcode colors**.

## Conventions
- Keep marketing + app surfaces visually consistent with the prototype.
- Money, brackets, and thresholds are computed by **deterministic calculators**, not the LLM.
- Any user-facing tax figure must carry a citation to its source document/rule.

## Where things are
- Requirements: `docs/Verra_BRD.docx`, `docs/Verra_PRD.docx`
- Plan & Figma build order: `docs/Verra_Execution_Plan.docx`
- Skills: `.claude/skills/` · Hooks: `.claude/hooks/` · Connectors: `.claude/connectors/`


## .claude scaffold (this project)
- **Skills** (`.claude/skills/`): verra-tax-analysis, verra-design-system, verra-figma-build,
  verra-requirements-writing, verra-document-ingestion, verra-audit-assurance,
  verra-compliance-calendar, verra-security-governance, verra-agent-orchestrator, verra-backend-service, verra-frontend.
- **Commands** (`.claude/commands/`): /tax-analysis, /new-screen, /figma-build, /brd-prd, /security-review.
- **Agents** (`.claude/agents/`): tax-analyst, design-engineer, compliance-reviewer.
- **Hooks** (`.claude/hooks/`): session-start, pii-guard, guard-bash, protect-paths, validate-design, format-code.
- **Connectors**: `.mcp.json` (Figma Dev Mode SSE) + `.claude/connectors/README.md`.

## Repo & build (ADR-0003/0016/0017)
- **code/frontend** — Next.js + TS (pnpm/turbo). UI from design/verra-prototype.html, tokens only.
- **code/backend** — Python 3.12 / FastAPI **microservices**: gateway · orchestrator
  (Supervisor[Planner/Router/Executor/Critic]) · model_gateway · ingestion · guardrails · registry · audit.
  Tooling: uv/ruff/mypy/pytest. API: code/backend/api/openapi.yaml. DB: code/backend/infra/db/schema.sql.
- Run: `cd code/frontend && pnpm dev` · `cd code/backend && docker compose up -d` (or `make dev`).
- Golden rules: modules never call models/tools directly — always via the orchestrator (ADR-0001);
  public traffic only through the gateway; FE↔BE contract is the OpenAPI spec.
