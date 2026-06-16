#!/usr/bin/env bash
# SessionStart: inject Verra guardrails into context.
cat <<'TXT'
[Verra project guardrails]
- Backend = Python/FastAPI microservices (ADR-0016/0017) under code/backend; Frontend = Next.js under code/frontend.
- Modules never call models/tools directly — always via the orchestrator (ADR-0001). Public traffic only via the gateway.
- Human-in-the-loop: a licensed human approves anything sent, filed, or relied upon.
- Cited & auditable: every figure shows its source; every action writes to the audit service.
- Use design tokens (design/design-tokens.css) — never hardcode colors. UI follows hazel.ai.
- Money/brackets/thresholds come from deterministic calculators, not the LLM.
TXT
exit 0
