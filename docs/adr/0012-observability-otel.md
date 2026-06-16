# ADR-0012: OpenTelemetry + LLM-trace tooling
**Status:** Accepted
## Context
We need end-to-end traces (gateway→layers→tools→providers), metrics, and LLM-specific evals/replay.
## Decision
**OpenTelemetry** for traces/metrics/logs; an LLM-trace tool (Langfuse/Arize-style) for prompt/response
traces, evals and replay. One trace per run, correlation IDs throughout.
## Consequences
+ Deep debuggability; eval-gated releases; SLO monitoring.
− Telemetry volume/cost management required; PII-safe logging.
