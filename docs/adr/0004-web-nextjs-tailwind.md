# ADR-0004: Next.js + Tailwind for the frontend
**Status:** Accepted · Amended 2026-06-16
## Context
Frontend could be plain React (Vite/CRA) or Next.js. The product has a marketing site (SEO) and an
app with a streaming AI assistant and auth.
## Options
| Option | Notes |
|--------|-------|
| **Next.js** | SSR/streaming (ideal for assistant token streaming), React Server Components, file-based routing, image/SEO optimization, mature auth patterns |
| React + Vite/CRA | Lighter SPA; but we'd hand-roll SSR/streaming/routing/SEO |
## Decision
Use **Next.js (App Router) + React + Tailwind**, with the design system in
`code/frontend/packages/design-system` consuming `design/design-tokens.*`. No hardcoded colors.
## Consequences
+ Fast UI delivery; great fit for streaming assistant + marketing SEO; consistent with the prototype.
− Tailwind theme must be generated from tokens to stay in sync.
