# ADR-0008: Redis Streams for async/queueing (v1)
**Status:** Accepted
## Context
Async jobs (ingestion, batch analysis), backpressure, and rate limiting are needed.
## Decision
Use **Redis** (Streams + structures) for queues, caching and rate-limit counters in v1. Move hot paths
to a managed broker (NATS/Kafka) if throughput/ordering demands grow (ADR revisit).
## Consequences
+ Simple, fast, multipurpose; fewer services early.
− Not a full durable broker → durable workflow state lives in Temporal/Postgres.
