# ADR-0006: Model gateway with provider-agnostic fallback chain
**Status:** Accepted
## Context
We must avoid provider lock-in/outages and control cost/quality centrally.
## Decision
A single **model gateway** abstracts providers. Routing is tier/cost/latency-aware with a fallback
chain: primary frontier (Anthropic Claude, tiered) → secondary provider → self-hosted open model →
degraded/deterministic. Circuit breakers + idempotency. Start from a LiteLLM-style layer or in-house.
## Consequences
+ Resilience, cost control, central token accounting.
− Must normalize capabilities/streaming/tool-calling across providers.
