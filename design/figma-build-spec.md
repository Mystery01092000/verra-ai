# Verra — Figma build spec

Build the Figma file from `design/verra-prototype.html` (source of truth) using the tokens in
`design/design-tokens.json`. Use the `verra-figma-build` skill + the Figma plugin skills.
Requires the Figma desktop **Dev Mode MCP** connected (see `.claude/connectors/README.md`).

## Pages (in the Figma file)
1. **01 · Foundations** — variables (color/type/radius/spacing/shadow), grids.
2. **02 · Components** — the component library.
3. **03 · Marketing** — landing frames.
4. **04 · App** — product frames.
5. **05 · Prototype** — wired flows.

## Variables (bind everything; no raw values)
- Color: accent `#5566FF`, accent600 `#4F46E5`, accent700 `#3A33C9`, periwinkle `#8A92FF`,
  periwinkleSoft `#E6E8FF`, ink `#111114`, inkSecondary `#5B5B66`, line `#E8E8EC`, surface `#FFFFFF`,
  cream `#F5F5F5`, ok `#1FBF75`, warn `#E5A33B`, danger `#E5484D`; brand gradient `#8A92FF→#4F46E5`.
- Type: Display = Archivo 900 (KMR Waldenburg stand-in); Body = Inter; Serif accent = Fraunces.
- Radius: button 9, card 18, cardLg 22. Shadow: base / lg / glow.

## Components (variants + states: default/hover/active/disabled; persona where relevant)
Button (dark pill / periwinkle CTA / ghost) · Assistant card + Mode chip · Suggestion row · Nav item ·
KPI tile · Feed/list row · Table · Tag/Pill (live/due/warn/info/hnw) · Calendar cell · Glass insight card ·
Stepper · Persona switcher · Top bar · Sidebar.

## Marketing frames (from prototype)
Hero (sky gradient + grid + rotating word + assistant card) · "Transform your practice" + tab row +
"Your day, prioritized" window · Stats band · Tax dashboard (KPI tiles + Income Breakdown donut +
glass insight cards) · STEP 1–4 workflow · Personas (3) · Security (toggles + badges) · Pricing (3 tiers + toggle).

## App frames (from prototype)
Home/Digest · Assistant (cited chat) · Clients/Entities table · Tax Planning (stepper + scenario compare) ·
Books & Close (exception queue) · Audit (evidence tie-out + risk) · Compliance calendar ·
Trust & Audit Log · Settings. Persona variants: firm / company / individual.

## Build order
Foundations → Components → Marketing frames → App frames → variants/states → prototype links → handoff
(annotate tokens + props; export via design-handoff). Use auto-layout throughout; WCAG 2.1 AA contrast.
