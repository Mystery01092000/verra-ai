---
name: verra-figma-build
description: >
  Build the Verra design in Figma from the prototype, matching hazel.ai. Use when the user wants to
  create/update Figma frames, components, variables, or a design library for Verra. Requires the Figma
  desktop Dev Mode MCP (see .claude/connectors/README.md).
---

# Verra Figma build

Source of truth: `design/verra-prototype.html`; tokens: `design/design-tokens.json`.
**Always load the Figma plugin skills (`figma-use`, `figma-generate-library`/`figma-generate-design`)
before calling Figma tools.**

## Build order (see Execution Plan §7)
1. **Variables/foundations:** colors (accent `#5566FF`, gradient `#8A92FF→#4F46E5`, ink `#111114`,
   cream `#F5F5F5`), type scale (Archivo 900 display, Inter body, Fraunces serif), radius, spacing, shadows.
2. **Core components:** buttons (black pill / periwinkle CTA / ghost), assistant card + mode chips,
   suggestion row, nav item, KPI tile, feed row, table, tag/pill, calendar cell, glass insight card, stepper.
3. **Marketing frames:** hero (sky gradient + grid + rotating word), transform/digest section,
   stats band, tax dashboard, STEP 1–4 workflow, personas, security, pricing (3 tiers).
4. **App frames:** Home/Digest, Assistant, Clients/Entities, Tax Planning, Books & Close, Audit,
   Compliance, Trust & Audit Log, Settings.
5. **Variants & states:** hover/active/disabled; persona variants (firm/company/individual); prototype links.
6. **Handoff:** annotate tokens + props; export with the design-handoff spec.

## Rules
- Bind color/type to **variables** (no raw values) so rebrand/theming is one switch.
- Use **auto-layout** to match the prototype's responsive behavior.
- Mirror the calm, premium, high-contrast hazel.ai feel; WCAG 2.1 AA contrast.
