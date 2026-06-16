# Verra — Test & Evaluation Strategy

Verra ships AI in a regulated domain, so quality gating combines classic software testing with
**AI evaluations**. Releases are eval-gated (ADR-0012; CI `evals` job).

## 1. Test pyramid (software)
- **Unit** (Vitest) — calculators, guardrail validators, routing/cost logic. Target ≥ 80% on core packages.
- **Integration** — orchestrator layers with real Postgres/Redis (docker-compose); RLS tenant-isolation tests.
- **Contract** — every API validated against `api/openapi.yaml`; provider/consumer contract tests.
- **E2E** (Playwright) — key journeys (tax run → approval → report) against a seeded env.
- **Load/perf** (k6) — seasonal-peak profiles; assert SLOs (first-token p95 < 3s).
- **Security** — SAST/DAST, dependency scanning, secrets scanning, RLS/authz tests.

## 2. AI evaluation harness
- **Golden datasets** per agent × jurisdiction × tax year (anonymized). Versioned; grow from real corrections.
- **Metrics:** task accuracy; **citation/grounding accuracy** (every figure traceable); hallucination rate;
  numeric correctness (vs deterministic calculators); refusal/escalation correctness; cost & latency.
- **Offline regression** — runs in CI on every PR touching agents/prompts/models; **blocks merge** on regression.
- **Online evals** — sampled production traffic scored continuously; canary compares candidate vs baseline.
- **Red-teaming** — prompt-injection, data-exfiltration, PII-leak, jailbreak suites for guardrails (ADR-0011).
- **Replay** — any production trace replayable for debugging and to author new eval cases.

## 3. Definition of Done
Tests + types pass · guardrails respected · citations on all tax figures · audit events emitted ·
eval suite green for touched agents · docs/ADRs updated if a decision changed.

## 4. Tooling
Vitest · Playwright · k6 · OpenAPI contract tests · eval runner (Promptfoo/Langfuse-style) · OTel traces.
