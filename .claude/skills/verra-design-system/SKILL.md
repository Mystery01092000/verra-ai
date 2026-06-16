---
name: verra-design-system
description: >
  Build Verra UI (web app, marketing, or Figma) that matches the hazel.ai-modeled look. Use when
  creating or editing any screen, component, or style for Verra. Enforces the design tokens.
---

# Verra design system

Source of truth: `design/verra-prototype.html`. Implement in **Next.js** under `code/frontend` (`packages/design-system` consumes `design/design-tokens.*`). Tokens: `design/design-tokens.css` / `.json`.
**Never hardcode colors** — use tokens.

## Tokens
- Accent: `--indigo #5566FF`; gradient `#8A92FF → #4F46E5`; ink `#111114`; secondary `#5B5B66`;
  surfaces white `#FFFFFF` / cream `#F5F5F5`; line `#E8E8EC`.
- Type: display = **Archivo 900** (stand-in for KMR Waldenburg), tight leading; body = **Inter**;
  serif accent = **Fraunces** (pricing titles).
- Radius: cards 16–22px, buttons 8–10px. Shadow: soft, low-opacity.

## Components
Buttons (black pill / solid-periwinkle CTA / ghost), assistant card + mode chips, suggestion row,
nav item, KPI tile, feed/list row, table, tag/pill (live/due/warn/info), calendar cell,
glass insight card, stepper.

## Layout patterns (from hazel.ai)
- Marketing: floating **left vertical nav**, dreamy **sky-gradient hero** with faint grid + rotating
  word, white glassy assistant card, cream "transform your practice" section with tab row +
  product window, indigo **stats band**, **tax dashboard** (KPI tiles + donut + glass insight cards),
  **STEP 1–4** workflow with gradient frames, 3-tier pricing with annual/monthly toggle.
- App: white workspace, black "Ask Verra" sparkle button, left nav, persona switcher
  (firm/company/individual).

## Rules
- Every consequential action shows an approval gate; every AI answer shows citations.
- Keep it calm, premium, high-contrast, generous whitespace. WCAG 2.1 AA.
