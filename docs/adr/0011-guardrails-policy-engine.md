# ADR-0011: OPA/Cedar policy engine + layered guardrails
**Status:** Accepted
## Context
Guardrails must be centrally enforced, declarative, and versioned per tenant/jurisdiction.
## Decision
A **policy engine** (OPA or Cedar) evaluates allow/deny/approval policies; combined with layered
validators (input schema, PII/DLP, injection detection, output/citation validation). Policies are
versioned and testable.
## Consequences
+ Declarative, auditable, per-jurisdiction policy; separation from app code.
− Policy authoring/testing discipline needed.
