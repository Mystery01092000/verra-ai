# Architecture Decision Records (ADRs)

Immutable, numbered records. Supersede rather than edit (see ADR-0000).

| # | Decision | Status |
|---|----------|--------|
| 0000 | Record architecture decisions | Accepted |
| 0001 | Orchestrator as a single common service | Accepted |
| 0002 | TypeScript for the frontend | Superseded by 0016 (backend) / amended |
| 0003 | Polyglot monorepo (frontend + backend split) | Accepted (amended) |
| 0004 | Next.js + Tailwind for the frontend | Accepted (amended) |
| 0005 | Custom DAG orchestration + Temporal for durability | Accepted |
| 0006 | Model gateway with provider-agnostic fallback chain | Accepted |
| 0007 | PostgreSQL + pgvector as primary datastore | Accepted |
| 0008 | Redis Streams for async/queueing (v1) | Accepted |
| 0009 | Shared-DB multi-tenancy with tenant_id + RLS | Accepted |
| 0010 | OIDC + RBAC, mTLS service-to-service | Accepted |
| 0011 | OPA/Cedar policy engine + layered guardrails | Accepted |
| 0012 | OpenTelemetry + LLM-trace tooling | Accepted |
| 0013 | pgvector RAG + chunk/rerank + OCR ingestion | Accepted |
| 0014 | Docker + Kubernetes + Terraform + GitHub Actions | Accepted |
| 0015 | Human-in-the-loop gates + immutable audit log | Accepted |
| 0016 | **Python (FastAPI) for the backend** | Accepted |
| 0017 | **Microservices from day one** | Accepted |

> Key language decision: **ADR-0016** (backend = Python/FastAPI; frontend = TypeScript/Next.js).
> Architecture style: **ADR-0017** (microservices). Folder split: **ADR-0003**.
