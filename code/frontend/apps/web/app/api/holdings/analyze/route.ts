import { NextResponse } from 'next/server';
import { gatewayPostJson } from '../../gateway';
import { DEMO_CLIENT_ID, DEMO_TENANT_ID } from '@/components/holdings/holdings-shared';

export const dynamic = 'force-dynamic';

type PlanningCapability = 'portfolio_analysis' | 'financial_planning';

interface AnalyzeRequest {
  capability: PlanningCapability;
  annualIncome?: number;
}

interface RunAccepted {
  runId?: string;
  run_id?: string;
}

function parseAnalyzeRequest(raw: unknown): AnalyzeRequest | string {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    return 'Request body must be a JSON object';
  }
  const body = raw as Record<string, unknown>;
  if (body.capability !== 'portfolio_analysis' && body.capability !== 'financial_planning') {
    return 'capability must be "portfolio_analysis" or "financial_planning"';
  }
  let annualIncome: number | undefined;
  if (body.annualIncome !== undefined && body.annualIncome !== null) {
    if (
      typeof body.annualIncome !== 'number' ||
      !Number.isFinite(body.annualIncome) ||
      body.annualIncome < 0
    ) {
      return 'annualIncome must be a non-negative number';
    }
    annualIncome = body.annualIncome;
  }
  return { capability: body.capability, annualIncome };
}

export async function POST(request: Request): Promise<NextResponse> {
  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return NextResponse.json(
      { success: false, data: null, error: 'Invalid JSON body' },
      { status: 400 },
    );
  }

  const parsed = parseAnalyzeRequest(raw);
  if (typeof parsed === 'string') {
    return NextResponse.json({ success: false, data: null, error: parsed }, { status: 400 });
  }

  const runRequest = {
    tenantId: DEMO_TENANT_ID,
    module: 'assistant',
    capability: parsed.capability,
    input: {
      clientId: DEMO_CLIENT_ID,
      ...(parsed.annualIncome !== undefined ? { annualIncome: parsed.annualIncome } : {}),
    },
    contextRefs: [],
  };

  const result = await gatewayPostJson<RunAccepted>('/v1/runs', runRequest);
  if (!result.ok || result.data === null) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Orchestrator unavailable' },
      { status: 502 },
    );
  }

  const runId = result.data.runId ?? result.data.run_id;
  if (!runId) {
    return NextResponse.json(
      { success: false, data: null, error: 'Orchestrator did not return a run id' },
      { status: 502 },
    );
  }
  return NextResponse.json({ success: true, data: { runId }, error: null });
}
