# Changelog

All notable changes to Verra. Format follows [Keep a Changelog](https://keepachangelog.com/);
versioning follows [SemVer](https://semver.org/) (pre‑1.0: minor bumps may include breaking changes).

## [0.2.0] — 2026-07-03

### Added
- **Deterministic India tax engine** (`verra_shared.tax`, AY 2025‑26): liability with slabs/87A/
  surcharge/marginal relief/cess, old‑vs‑new regime comparison, HRA/LTA salary exemptions,
  Form 16↔26AS↔AIS TDS reconciliation, advance‑tax instalments with 234B/234C interest — all
  outputs cited to their governing sections.
- **Holdings consolidation engine** (`verra_shared.holdings` + new `holdings` service, port 8083):
  19 holding types, net‑worth/allocation/insurance analytics, advisory flags with honest sourcing,
  JSONL persistence, account‑number masking at storage.
- **Regulatory rules corpus** (`verra_shared.rules`): 41 rules across Income‑tax Act, NRI/FEMA,
  SEBI, IRDAI, GST with deterministic resident/NRI‑filtered search.
- **Orchestrator run lifecycle**: planner templates (tax analysis/QA/scenario, portfolio analysis,
  financial planning, general QA), guardrails check per step, audit event per step, signal‑based
  critic confidence, `needs_approval` gating, approve/reject endpoints with approver receipts.
- **Model gateway providers**: Claude on Bedrock, **Amazon Nova** (boto3 converse — works on
  free‑tier accounts), OpenAI; ordered fallback chain with graceful degradation.
- **Audit service**: SHA‑256 hash‑chained append‑only log, tamper‑detecting `/verify`, resume on
  restart.
- **Guardrails service**: PAN/Aadhaar/SSN/email/phone detection with masking, prompt‑injection
  blocking, citation enforcement for money‑bearing outputs.
- **Ingestion service**: Form 16 / 26AS / AIS classification + regex field extraction with
  per‑field confidence, section provenance, and needs‑review gating; tolerant of narrative and
  official layouts (Rs./INR/₹ prefixes, inline labels).
- **Frontend**: chat agent modes (Ask/Tax planner/Portfolio/NRI taxes/Financial planning) with
  regulator‑aware prompts and attach‑document grounding; live Tax Workspace with deterministic
  recompute; Holdings dashboard + manager + AI analysis; Documents upload with confidence tables;
  hash‑chain Audit viewer; human‑in‑the‑loop Approvals inbox; salted (scrypt) credentials auth.
- **Gateway**: path‑prefix routing (orchestrator/ingestion/audit/holdings), query‑string and
  non‑JSON upstream passthrough.
- **Docs**: BRD/PRD verification report, Platform Plan v2, consolidated Implementation Summary.

### Fixed
- Orchestrator called non‑existent registry/model‑gateway endpoints; run status was hardcoded.
- Frontend chat returned an identical hardcoded reply when no provider was configured — now an
  honest setup notice with provider metadata.
- Circuit breaker crashed requests when Redis was unavailable — now fails open with a warning.
- Gateway dropped query strings and crashed on non‑JSON upstream bodies.
- Unsalted SHA‑256 password hashes replaced with per‑user‑salted scrypt; dev user store gitignored.
- CI mypy resolved `verra_shared` as untyped (`py.typed` added, MYPYPATH corrected); 15 ruff
  errors and a stale model‑tier test fixed.

### Security
- Hardcoded AWS credentials removed from the untracked Bedrock probe script (never committed);
  key rotation recommended. Repo‑wide secret scan added to the release checklist.

## [0.1.0] — 2026-06-28

Initial concept + scaffold: BRD/PRD/system design/ADRs, interactive design prototypes and token
system, 7‑service FastAPI scaffold behind a gateway, Next.js frontend shell, docker‑compose dev
stack, CI skeleton.
