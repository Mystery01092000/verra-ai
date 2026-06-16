# Contributing
- Conventional commits; trunk-based with short-lived branches; PRs require green CI + 1 review.
- Definition of Done: tests + types pass, guardrails respected, citations on tax figures, audit events emitted, eval suite green for touched agents. See docs/Verra_Test_and_Eval_Strategy.
- Never hardcode colors (use @verra/design-system tokens). Never call models/tools outside the orchestrator (ADR-0001).
