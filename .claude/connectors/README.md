# Connectors — how to wire up execution

## 1. Claude in Chrome (for capturing references / web research)
1. In the Claude desktop app: Settings → Connectors → enable **Claude in Chrome**.
2. Install the **Claude for Chrome** extension from the Chrome Web Store; pin it.
3. Open Chrome and sign into the extension with the same account. Requires a paid plan.

## 2. Figma (to build the design from the prototype)
Two layers are required to **write** frames into a file:
1. **Connector auth (Cowork):** authorize the Figma connector.
2. **Desktop Dev Mode MCP:** open the **Figma desktop app** → open/create the file →
   with nothing selected, switch to **Dev Mode** → enable the **MCP server** in the right sidebar.
   Keep that file open and focused. Requires a **Dev/Full seat** on a paid Figma plan.
   The local server is referenced in `../../.mcp.json` (`http://127.0.0.1:3845/sse`).

Build order is in `docs/Verra_Execution_Plan.docx` §7 (Foundations → components → marketing frames →
app frames → variants → handoff).

## 3. Optional product integrations (roadmap)
QuickBooks / Xero (ledger), Plaid (bank/custodial), Google Workspace / Microsoft 365 (email+calendar),
CRM (Wealthbox), filing gateways (IRS MeF, GSTN, Companies House), SSO/SCIM (Okta/Entra/Google).
