# ADR-0009: Shared-DB multi-tenancy with tenant_id + RLS
**Status:** Accepted
## Context
Firms, companies and individuals are tenants needing strict isolation at reasonable cost.
## Decision
Shared database with a mandatory `tenant_id` on every row and **PostgreSQL Row-Level Security**.
Per-tenant encryption keys and optional dedicated schemas/DB for enterprise/data-residency needs.
## Consequences
+ Cost-efficient; strong isolation via RLS; enterprise can upgrade to isolation.
− RLS discipline required; every query is tenant-scoped and tested.
