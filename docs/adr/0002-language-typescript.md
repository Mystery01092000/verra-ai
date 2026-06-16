# ADR-0002: TypeScript for the frontend
**Status:** Superseded by ADR-0016 (backend) · Amended 2026-06-16
## Context
Originally we proposed TypeScript across web *and* services. After re-evaluating with an AI-heavy
backend and an explicit option to use Python or Go, we split the decision.
## Decision
**TypeScript remains the frontend language** (Next.js, design system, shared UI types).
The **backend language is decided in ADR-0016 (Python/FastAPI)** — this ADR no longer governs services.
## Consequences
+ Frontend keeps one cohesive TS toolchain and shared UI types.
+ Backend is free to use the best ecosystem for AI/agents (see ADR-0016).
− Types are no longer shared in-process across the FE/BE boundary → use the OpenAPI contract
  (`code/backend/api/openapi.yaml`) to generate clients.
