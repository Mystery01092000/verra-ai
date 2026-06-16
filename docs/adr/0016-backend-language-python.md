# ADR-0016: Python (FastAPI) for the backend
**Status:** Accepted · 2026-06-16
## Context
Verra's backend is dominated by AI/agent work: orchestration, retrieval/RAG, document parsing/OCR,
tool use, evals. We were open to **Python**, **Go**, or TypeScript-everywhere. The choice drives
hiring, velocity, and how easily we integrate the AI ecosystem.
## Options considered
| Option | Pros | Cons |
|--------|------|------|
| **Python (FastAPI)** | Richest AI/agent ecosystem (LangGraph, LangChain, provider SDKs, OCR/ML, eval tools); fast iteration; large AI talent pool; async FastAPI is performant enough | Lower raw throughput/CPU efficiency than Go; packaging discipline needed |
| **Go** | Excellent concurrency, low latency, single static binary, low memory; great for a high-RPS gateway | Sparse first-party AI tooling → much glue; slower agent iteration; smaller AI talent pool |
| **TS everywhere** | One language FE+BE; shared types | Weaker AI/ML ecosystem than Python; not where agent tooling lives |
## Decision
Use **Python 3.12 + FastAPI** for all backend microservices; **TypeScript/Next.js** for the frontend
(ADR-0002, ADR-0004). Tooling: **uv/pip**, **ruff** (lint+format), **mypy --strict**, **pytest**.
## Consequences
+ Fastest path to a high-quality AI core; directly uses the agent/eval ecosystem; easy hiring.
+ Clear FE/BE separation via the OpenAPI contract.
− Watch CPU-bound throughput: mitigate with async I/O, worker pools, caching, and (if a hot path needs
  it) a targeted **Go** service behind the same gateway — allowed under the microservices model (ADR-0017).
