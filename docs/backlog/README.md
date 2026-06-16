# Sprint-0 backlog

`sprint-0-backlog.csv` is import-ready for Jira/Linear (Epic, StoryID, Title, Type, Priority,
Estimate, AcceptanceCriteria, DependsOn). Points are relative (Fibonacci). Sprint 0 = foundations +
orchestrator + guardrails + audit + eval harness; Sprint 1 = ingestion/RAG + Tax MVP agent + web shell.

## Epics
- **E1 Foundations** · **E2 Orchestrator** · **E3 Guardrails & Audit** · **E4 Cost/Token**
- **E5 Ingestion & RAG** · **E6 Tax MVP** · **E7 Web & Design System** · **E8 Data & Multi-tenancy**
- **E9 Eval & Test** · **E10 Security & Compliance**

## Suggested Sprint 0 goal
"A request flows end-to-end through the guardrailed orchestrator (plan→route→execute→critic), with a
model fallback, a human approval gate, an audit receipt, budgets enforced, and the eval harness gating CI."
