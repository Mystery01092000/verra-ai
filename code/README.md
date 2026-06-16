# Verra — code

Monorepo for the Verra platform. Full product overview & showcase: see the **[root README](../README.md)**.

## Structure
- `frontend/` — Next.js app + `packages/design-system` + `packages/shared` (TypeScript)
- `backend/` — Python/FastAPI microservices: `gateway · orchestrator · model_gateway · ingestion · guardrails · registry · audit`, plus `packages/py_shared`, `api/openapi.yaml`, `infra/`, `docker-compose.yml`
- `.github/workflows/` — CI (frontend + backend + AI eval gate)

## Run
```bash
cd frontend && pnpm install        # frontend deps
cd backend  && docker compose up -d # data plane + 7 microservices
make dev                            # run everything (from code/)
```
Copy `backend/.env.example` → `.env`. Decisions: see [`../docs/adr`](../docs/adr).
