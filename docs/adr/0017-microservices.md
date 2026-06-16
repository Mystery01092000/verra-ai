# ADR-0017: Microservices from day one
**Status:** Accepted · 2026-06-16
## Context
Components have very different scaling, failure, and iteration profiles (e.g., ingestion is bursty and
CPU-heavy; the orchestrator is the critical path; the model gateway must isolate provider outages).
We want independent scaling, blast-radius isolation, and the freedom to drop in a Go service later.
## Decision
Adopt a **microservices architecture** with a small set of coarse-grained services (not nano-services):
`gateway`, `orchestrator`, `model_gateway`, `ingestion`, `guardrails`, `registry`, `audit`.
- Communication: HTTP/JSON internally (gRPC later if needed); **mTLS** between services.
- Public traffic enters only through `gateway`. Modules never call models/tools directly (ADR-0001).
- Data: shared PostgreSQL with **per-service schemas + RLS** initially; split to per-service databases
  when ownership/scale demands (revisit via ADR-0000).
- Each service: own pyproject, Dockerfile, tests, and independent deploy.
## Consequences
+ Independent scaling (e.g., scale ingestion in tax season), fault isolation, polyglot freedom.
+ Clear ownership and contracts; aligns with the orchestrator-as-service decision.
− Higher operational complexity (deploys, networking, distributed tracing). Mitigate with: managed
  Kubernetes (ADR-0014), shared OpenTelemetry (ADR-0012), contract tests against `api/openapi.yaml`,
  a service template, and starting coarse (7 services) rather than fragmenting prematurely.
