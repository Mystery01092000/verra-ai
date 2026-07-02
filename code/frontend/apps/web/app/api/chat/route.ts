import { NextRequest, NextResponse } from 'next/server';

// ── Types ──────────────────────────────────────────────────────────
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatDocumentKeyField {
  path?: string;
  value?: string;
}

interface ChatDocumentContext {
  docType?: string;
  keyFields?: ChatDocumentKeyField[];
  needsReview?: boolean;
}

interface ChatRequest {
  message: string;
  history?: ChatMessage[];
  agentMode?: string;
  documentText?: string;
  documentName?: string;
  documentContext?: ChatDocumentContext;
}

interface Citation {
  label: string;
  page?: number;
  type: 'document' | 'rule' | 'section';
}

export type ChatProvider = 'bedrock' | 'anthropic' | 'gateway' | 'unconfigured';

interface ChatResponse {
  content: string;
  provider: ChatProvider;
  model?: string;
  citations?: Citation[];
  downloadable?: { filename: string; content: string; mimeType: string };
}

type AttemptReason = 'no-credentials' | 'request-failed' | 'no-answer';

interface ProviderAttempt {
  provider: Exclude<ChatProvider, 'unconfigured'>;
  reason: AttemptReason;
}

// ── Constants ──────────────────────────────────────────────────────
const BEDROCK_MODEL = 'us.amazon.nova-lite-v1:0';
const ANTHROPIC_MODEL = 'claude-3-5-haiku-20241022';
const DEFAULT_GATEWAY_URL = 'http://localhost:8080';
const GATEWAY_TIMEOUT_MS = 25_000;
const GATEWAY_POLL_ATTEMPTS = 5;
const GATEWAY_POLL_INTERVAL_MS = 1_000;

// ── System prompts per agent mode ──────────────────────────────────
const BASE_SYSTEM = `You are Verra, an expert AI tax assistant for India (AY 2025-26 / FY 2024-25).

FORMATTING RULES (follow strictly):
1. Always use markdown tables for comparisons, slabs, and calculations.
2. Show step-by-step arithmetic with clear labels and INR amounts (₹).
3. Cite every tax figure with the relevant section (e.g., Section 80C, Section 87A).
4. When generating a summary the user might want to save, embed it as:
   \`\`\`download:Tax_Summary.csv
   Header1,Header2,Header3
   val1,val2,val3
   \`\`\`
5. Keep responses concise but complete.
6. Always end with: "⚠️ Review with a licensed CA before filing."`;

// Shared regulatory frame for advisory-adjacent modes (portfolio, NRI,
// financial planning). These modes reason under Indian regulatory frameworks
// and never produce anything a client can act on without a licensed human.
const INDIA_REGULATORY_FRAME = `
REGULATORY FRAME (mandatory for this mode):
- Reason under Indian regulatory frameworks: the Income-tax Act 1961, SEBI
  (Investment Advisers) Regulations 2013 suitability requirements, FEMA 1999 and
  RBI master directions for NRI/cross-border matters, and IRDAI regulations for
  insurance adequacy.
- Cite the specific section, regulation, or master direction for EVERY
  regulatory claim (e.g., Section 112A, SEBI IA Regulation 17, FEMA Schedule 3).
- NEVER recommend specific securities, schemes, funds, stocks, or products —
  discuss at asset-class and category level only.
- Everything you produce is a DRAFT for review by a licensed professional
  (SEBI-registered investment adviser, CA, or equivalent). Say so when the user
  asks for a decision.`;

const AGENT_PROMPTS: Record<string, string> = {
  default: BASE_SYSTEM,
  general: BASE_SYSTEM,
  portfolio:
    BASE_SYSTEM +
    INDIA_REGULATORY_FRAME +
    `\n\nSPECIALISATION: Portfolio & holdings analysis.
- Analyse allocation, concentration, debt load, insurance adequacy and the tax
  treatment of gains (Sections 111A, 112, 112A; Section 80C/80D linkages).
- Frame observations as risks/considerations, never buy/sell instructions.`,
  'nri-tax':
    BASE_SYSTEM +
    INDIA_REGULATORY_FRAME +
    `\n\nSPECIALISATION: NRI taxation.
- Cover residency tests (Section 6), NRE/NRO/FCNR account treatment, TDS under
  Section 195, DTAA relief (Sections 90/90A/91), and FEMA/RBI repatriation rules.
- Always state which residency status an answer assumes.`,
  'financial-planning':
    BASE_SYSTEM +
    INDIA_REGULATORY_FRAME +
    `\n\nSPECIALISATION: Financial planning.
- Draft goal-based plans: emergency fund, insurance cover, debt strategy,
  retirement and tax-efficient savings — at asset-class level only.
- Every plan is a draft that MUST be approved by a licensed professional before
  the client relies on it; remind the user of this in the closing line.`,
  'tax-planner':
    BASE_SYSTEM +
    `\n\nSPECIALISATION: Tax Planning.
- Compare at least 2 scenarios side-by-side in a table.
- Compute exact tax savings in INR.
- Suggest investments under 80C, 80D, NPS, HRA with amounts.`,
  'regime-compare':
    BASE_SYSTEM +
    `\n\nSPECIALISATION: Old vs New Tax Regime Comparison.
- ALWAYS output a comparison table: Income Slab | Old Regime Tax | New Regime Tax | Difference.
- Recommend the better regime with the rupee difference.
- Include Section 87A rebate where applicable.`,
  'deduction-finder':
    BASE_SYSTEM +
    `\n\nSPECIALISATION: Deduction Finder.
- Output a table: Section | Description | Max Limit | Eligible? | Est. Saving.
- Cover 80C, 80CCD, 80D, 80E, 80G, 80TTA, HRA, LTA, home loan 24(b).`,
  'advance-tax':
    BASE_SYSTEM +
    `\n\nSPECIALISATION: Advance Tax Calculator.
- Output quarterly instalment table: Due Date | Cumulative % | Amount Due | Status.
- Per Sections 207–209. Include 234B/234C penalty calculation if applicable.`,
};

// ── Parse download blocks from LLM response ─────────────────────────
function parseDownloads(content: string): {
  clean: string;
  downloadable?: ChatResponse['downloadable'];
} {
  const match = content.match(/```download:([^\n]+)\n([\s\S]*?)```/);
  if (!match) return { clean: content };
  const filename = match[1]?.trim() ?? 'download.csv';
  const data = match[2]?.trim() ?? '';
  const clean = content.replace(match[0], `*[📥 Download available: ${filename}]*`);
  return {
    clean,
    downloadable: {
      filename,
      content: data,
      mimeType: filename.endsWith('.csv') ? 'text/csv' : 'text/plain',
    },
  };
}

// ── Default citations from agent mode ─────────────────────────────
function defaultCitations(mode: string): Citation[] {
  const map: Record<string, Citation[]> = {
    default: [
      { label: 'Income Tax Act 1961', type: 'rule' },
      { label: 'Finance Act 2024', type: 'rule' },
    ],
    'tax-planner': [
      { label: 'Section 80C', type: 'section' },
      { label: 'Section 80D', type: 'section' },
    ],
    'regime-compare': [
      { label: 'New Tax Regime — Section 115BAC', type: 'rule' },
      { label: 'Finance Act 2023', type: 'rule' },
    ],
    'deduction-finder': [
      { label: 'Chapter VI-A Deductions', type: 'section' },
      { label: 'Section 24(b)', type: 'section' },
    ],
    'advance-tax': [
      { label: 'Section 207', type: 'section' },
      { label: 'Section 234B/234C', type: 'section' },
    ],
    portfolio: [
      { label: 'SEBI (Investment Advisers) Regulations 2013', type: 'rule' },
      { label: 'Sections 111A/112/112A — capital gains', type: 'section' },
    ],
    'nri-tax': [
      { label: 'Section 6 — residency', type: 'section' },
      { label: 'FEMA 1999 / RBI master directions', type: 'rule' },
    ],
    'financial-planning': [
      { label: 'SEBI (Investment Advisers) Regulations 2013', type: 'rule' },
      { label: 'IRDAI — insurance adequacy', type: 'rule' },
    ],
    general: [
      { label: 'Income Tax Act 1961', type: 'rule' },
      { label: 'Finance Act 2024', type: 'rule' },
    ],
  };
  return map[mode] ?? map.default ?? [];
}

// ── Call Bedrock (Amazon Nova) ─────────────────────────────────────
async function callBedrock(
  system: string,
  messages: ChatMessage[],
  model: string,
): Promise<string> {
  const { BedrockRuntimeClient, InvokeModelCommand } =
    await import('@aws-sdk/client-bedrock-runtime');

  const accessKey = process.env.AWS_ACCESS_KEY_ID ?? process.env.AWS_ACCESS_KEY;
  const secretKey = process.env.AWS_SECRET_ACCESS_KEY ?? process.env.AWS_SECRET_KEY;
  const region = process.env.AWS_REGION ?? 'us-east-1';

  const client = new BedrockRuntimeClient({
    region,
    ...(accessKey && secretKey
      ? { credentials: { accessKeyId: accessKey, secretAccessKey: secretKey } }
      : {}),
  });

  // Nova converse format: system as array, messages with content blocks
  const body = JSON.stringify({
    system: [{ text: system }],
    messages: messages.map((m) => ({
      role: m.role,
      content: [{ text: m.content }],
    })),
    inferenceConfig: { maxTokens: 2048 },
  });

  const cmd = new InvokeModelCommand({
    modelId: model,
    body: new TextEncoder().encode(body),
    contentType: 'application/json',
    accept: 'application/json',
  });

  const res = await client.send(cmd);
  const data = JSON.parse(new TextDecoder().decode(res.body)) as {
    output: { message: { content: Array<{ text: string }> } };
  };
  const text = data.output.message.content[0]?.text;
  if (!text) throw new Error('No text in Nova response');
  return text;
}

// ── Call Anthropic SDK ─────────────────────────────────────────────
async function callAnthropic(system: string, messages: ChatMessage[]): Promise<string> {
  const { default: Anthropic } = await import('@anthropic-ai/sdk');
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  const response = await client.messages.create({
    model: ANTHROPIC_MODEL,
    max_tokens: 2048,
    system,
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
  });
  const block = response.content[0];
  if (!block || block.type !== 'text') throw new Error('No text in Anthropic response');
  return block.text;
}

// ── Call backend gateway (RunRequest → poll RunResult) ─────────────
// Wire format mirrors code/backend/packages/py_shared/verra_shared/models.py
// (camelCase aliases): POST /v1/runs accepts a RunRequest and returns a
// RunAccepted {runId, stream}; GET /v1/runs/{runId} returns a RunResult.
interface GatewayRunAccepted {
  runId?: string;
}

interface GatewayRunResult {
  runId?: string;
  status?: string;
  output?: unknown;
}

function extractRunAnswer(output: unknown): string | null {
  if (typeof output === 'string' && output.trim()) return output;
  if (output && typeof output === 'object') {
    const record = output as Record<string, unknown>;
    // Orchestrator RunResult.output is {steps: [...], final: <last step result>}.
    if ('final' in record) {
      const fromFinal = extractRunAnswer(record.final);
      if (fromFinal) return fromFinal;
    }
    for (const key of ['answer', 'message', 'text', 'content']) {
      const value = record[key];
      if (typeof value === 'string' && value.trim()) return value;
    }
  }
  return null;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Gateway fallback: map chat modes onto orchestrator capabilities/modules.
const MODE_CAPABILITIES: Record<string, { module: string; capability: string }> = {
  portfolio: { module: 'assistant', capability: 'portfolio_analysis' },
  'financial-planning': { module: 'assistant', capability: 'financial_planning' },
};

function gatewayTargetForMode(mode: string): { module: string; capability: string } {
  // general, tax-planner, nri-tax and the tax-page agents all resolve to tax_qa.
  return MODE_CAPABILITIES[mode] ?? { module: 'tax', capability: 'tax_qa' };
}

// ── Fold an ingested-document summary into provider context ────────
function summarizeDocumentContext(ctx: ChatDocumentContext | undefined): string | null {
  if (!ctx || typeof ctx !== 'object') return null;
  const docType = typeof ctx.docType === 'string' && ctx.docType ? ctx.docType : 'document';
  const fields = Array.isArray(ctx.keyFields)
    ? ctx.keyFields
        .filter((f) => f && typeof f.path === 'string' && typeof f.value === 'string')
        .slice(0, 8)
        .map((f) => `${f.path}=${f.value}`)
    : [];
  const extracted = fields.length > 0 ? `extracted: ${fields.join(', ')}` : 'no fields extracted';
  const review = ctx.needsReview
    ? ' Low-confidence fields were flagged for human review — treat these values as unverified.'
    : '';
  return `The client uploaded a ${docType}; ${extracted}.${review}`;
}

/**
 * Returns the run's answer text, or null when the run completed without a
 * usable answer. Throws on transport/HTTP failures.
 */
async function callGateway(request: ChatRequest): Promise<string | null> {
  const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL ?? DEFAULT_GATEWAY_URL;
  const { module, capability } = gatewayTargetForMode(request.agentMode ?? 'default');
  const runRequest = {
    tenantId: 'demo',
    module,
    capability,
    input: {
      message: request.message,
      history: request.history ?? [],
      agentMode: request.agentMode ?? 'default',
      ...(request.documentText ? { documentText: request.documentText } : {}),
      ...(request.documentName ? { documentName: request.documentName } : {}),
      ...(request.documentContext ? { documentContext: request.documentContext } : {}),
    },
    contextRefs: [],
  };

  const createRes = await fetch(`${gatewayUrl}/v1/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(runRequest),
    signal: AbortSignal.timeout(GATEWAY_TIMEOUT_MS),
  });
  if (!createRes.ok) {
    throw new Error(`Gateway POST /v1/runs returned ${createRes.status}`);
  }

  const accepted = (await createRes.json()) as GatewayRunAccepted;
  if (!accepted.runId) return null;

  for (let attempt = 0; attempt < GATEWAY_POLL_ATTEMPTS; attempt++) {
    await sleep(GATEWAY_POLL_INTERVAL_MS);
    const pollRes = await fetch(`${gatewayUrl}/v1/runs/${encodeURIComponent(accepted.runId)}`, {
      signal: AbortSignal.timeout(GATEWAY_TIMEOUT_MS),
    });
    if (!pollRes.ok) {
      throw new Error(`Gateway GET /v1/runs/{id} returned ${pollRes.status}`);
    }
    const result = (await pollRes.json()) as GatewayRunResult;
    const answer = extractRunAnswer(result.output);
    if (answer) return answer;
    if (result.status === 'failed') return null;
    if (result.status === 'done') return null; // done but no answer payload
  }
  return null; // run never completed within the polling window
}

// ── Honest configuration-error reply (never masquerades as an answer) ──
const ATTEMPT_DESCRIPTIONS: Record<ProviderAttempt['provider'], Record<AttemptReason, string>> = {
  bedrock: {
    'no-credentials': 'AWS Bedrock — skipped, no credentials configured',
    'request-failed': 'AWS Bedrock — request failed',
    'no-answer': 'AWS Bedrock — returned no answer',
  },
  anthropic: {
    'no-credentials': 'Anthropic API — skipped, no API key configured',
    'request-failed': 'Anthropic API — request failed',
    'no-answer': 'Anthropic API — returned no answer',
  },
  gateway: {
    'no-credentials': 'Verra backend gateway — skipped, not configured',
    'request-failed': 'Verra backend gateway — unreachable or returned an error',
    'no-answer': 'Verra backend gateway — run completed without an answer',
  },
};

function buildUnconfiguredReply(attempts: ProviderAttempt[]): string {
  const attemptLines = attempts
    .map((a) => `- ${ATTEMPT_DESCRIPTIONS[a.provider][a.reason]}`)
    .join('\n');

  return `**I can't answer this yet — no AI provider is configured.**

This is a setup notice, not an answer to your question. Every provider was tried and none could serve the request:

${attemptLines}

**To fix this**, add credentials to \`apps/web/.env.local\` (see \`.env.example\`):

- \`AWS_BEARER_TOKEN_BEDROCK\`, or \`AWS_ACCESS_KEY_ID\` + \`AWS_SECRET_ACCESS_KEY\` — for AWS Bedrock, **or**
- \`ANTHROPIC_API_KEY\` — for the Anthropic API

…or start the backend gateway:

\`\`\`
cd code/backend && docker compose up -d
\`\`\`

Then restart the dev server and ask again.`;
}

// ── Main handler ───────────────────────────────────────────────────
export async function POST(
  req: NextRequest,
): Promise<NextResponse<ChatResponse | { error: string }>> {
  let body: ChatRequest;
  try {
    body = (await req.json()) as ChatRequest;
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }

  const {
    message,
    history = [],
    agentMode = 'default',
    documentText,
    documentName,
    documentContext,
  } = body;
  if (!message?.trim()) return NextResponse.json({ error: 'Message is required' }, { status: 400 });

  // Build system prompt
  let system = AGENT_PROMPTS[agentMode] ?? AGENT_PROMPTS.default ?? BASE_SYSTEM;
  const docSummary = summarizeDocumentContext(documentContext);
  if (docSummary) {
    system += `\n\n═══ INGESTED DOCUMENT CONTEXT ═══\n${docSummary}\n═══ END CONTEXT ═══`;
  }
  if (documentText) {
    system += `\n\n═══ ATTACHED DOCUMENT: ${documentName ?? 'Uploaded file'} ═══\n${documentText.slice(0, 8000)}\n═══ END DOCUMENT ═══\nAnalyse the user's questions in the context of this document.`;
  }

  // Build message history
  const claudeMessages: ChatMessage[] = [
    ...history.map((m) => ({ role: m.role, content: m.content })),
    { role: 'user', content: message },
  ];

  const hasBedrockCreds =
    !!process.env.AWS_BEARER_TOKEN_BEDROCK ||
    !!(process.env.AWS_ACCESS_KEY_ID || process.env.AWS_ACCESS_KEY);
  const hasAnthropicKey = !!process.env.ANTHROPIC_API_KEY;

  const attempts: ProviderAttempt[] = [];
  let rawText: string | null = null;
  let provider: ChatProvider = 'unconfigured';
  let model: string | undefined;

  // 1. Try Bedrock
  if (!hasBedrockCreds) {
    attempts.push({ provider: 'bedrock', reason: 'no-credentials' });
  } else {
    try {
      rawText = await callBedrock(system, claudeMessages, BEDROCK_MODEL);
      provider = 'bedrock';
      model = BEDROCK_MODEL;
    } catch (err) {
      attempts.push({ provider: 'bedrock', reason: 'request-failed' });
      console.warn('[Verra chat] Bedrock failed, falling through:', err);
    }
  }

  // 2. Try Anthropic SDK
  if (!rawText) {
    if (!hasAnthropicKey) {
      attempts.push({ provider: 'anthropic', reason: 'no-credentials' });
    } else {
      try {
        rawText = await callAnthropic(system, claudeMessages);
        provider = 'anthropic';
        model = ANTHROPIC_MODEL;
      } catch (err) {
        attempts.push({ provider: 'anthropic', reason: 'request-failed' });
        console.warn('[Verra chat] Anthropic failed, falling through:', err);
      }
    }
  }

  // 3. Try backend gateway
  if (!rawText) {
    try {
      rawText = await callGateway(body);
      if (rawText) {
        provider = 'gateway';
      } else {
        attempts.push({ provider: 'gateway', reason: 'no-answer' });
        console.warn('[Verra chat] Gateway run produced no answer, falling through');
      }
    } catch (err) {
      attempts.push({ provider: 'gateway', reason: 'request-failed' });
      console.warn('[Verra chat] Gateway failed, falling through:', err);
    }
  }

  // 4. No provider available — return an explicit configuration notice
  if (!rawText) {
    console.warn(
      '[Verra chat] No provider could serve the request:',
      attempts.map((a) => `${a.provider}=${a.reason}`).join(', '),
    );
    return NextResponse.json({
      content: buildUnconfiguredReply(attempts),
      provider: 'unconfigured' as const,
    });
  }

  console.warn(`[Verra chat] Served by provider=${provider}${model ? ` model=${model}` : ''}`);

  const { clean, downloadable } = parseDownloads(rawText);
  const citations = defaultCitations(agentMode);

  return NextResponse.json({
    content: clean,
    provider,
    ...(model ? { model } : {}),
    citations,
    ...(downloadable ? { downloadable } : {}),
  });
}
