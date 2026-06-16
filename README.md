# Verra — AI engine for accounting, tax, audit & compliance

> Working name. UI/UX modeled on **hazel.ai**. Multi-tenant (firms · companies · individuals),
> multi-jurisdiction (US MVP · UK · India). MVP = **Tax** (planning + filing prep).
> Backend: **Python/FastAPI microservices** (ADR-0016/0017). Frontend: **Next.js** (ADR-0004).

## Top-level layout (code separated from everything else)
```
verra/
├─ code/                     ← all source + code-related things
│  ├─ frontend/              ← Next.js app + TS packages (design-system, shared)
│  │  └─ apps/web · packages/* · pnpm/turbo/tsconfig
│  ├─ backend/               ← Python microservices
│  │  ├─ services/           ← gateway · orchestrator · model_gateway · ingestion · guardrails · registry · audit
│  │  ├─ packages/py_shared  ← shared pydantic models
│  │  ├─ api/openapi.yaml · infra/ · docker-compose.yml · pyproject.toml
│  ├─ .github/workflows/     ← CI (frontend + backend jobs)
│  └─ Makefile · CONTRIBUTING.md · SECURITY.md
├─ docs/                     ← BRD · PRD · Execution Plan · System Design · Orchestrator Plan · ADRs · backlog · test/eval
├─ design/                   ← prototype · tokens · diagrams · figma spec
└─ .claude/                  ← skills · hooks · commands · agents · connectors
```

## Quick start
```bash
cd code/frontend && pnpm install          # frontend deps
cd code/backend  && docker compose up -d   # data plane + 7 microservices
make dev                                    # (from code/) backend stack + frontend
```
Copy `code/backend/.env.example` → `.env`. Never commit secrets (guarded by `.claude/hooks`).

## Architecture (see docs/adr)
- **Microservices** behind one **gateway**; all agentic work via the **orchestrator** (ADR-0001/0017).
- **Python/FastAPI** backend (ADR-0016); **Next.js** frontend (ADR-0004); **PostgreSQL+pgvector**, **Redis**.
- Guardrails + human-in-the-loop + immutable audit on every consequential action.

_Concept project. Verra outputs are analysis and drafts; a licensed professional reviews and is
responsible for all advice and filings._
