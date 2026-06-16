---
name: verra-frontend
description: >
  Build the Verra frontend (Next.js) under code/frontend. Use for screens/components/routing/state.
  Pairs with verra-design-system. Next.js chosen for SSR/streaming + SEO (ADR-0004).
---

# Verra frontend (Next.js)

- App Router + React Server Components; stream the assistant responses (SSE from the gateway).
- UI from `design/verra-prototype.html`; build with `@verra/design-system` (tokens only, no hardcoded colors).
- Call the backend **only** via the gateway API (`/v1/...`); generate the client from `code/backend/api/openapi.yaml`.
- Marketing pages SSR for SEO; app pages behind auth (OIDC).
- Tailwind theme generated from tokens (keep in sync). WCAG 2.1 AA.
- Location: `code/frontend/apps/web`; shared UI in `code/frontend/packages/*`.
