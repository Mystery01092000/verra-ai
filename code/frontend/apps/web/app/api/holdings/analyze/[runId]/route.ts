import { NextResponse } from 'next/server';
import { gatewayFetch } from '../../../gateway';
import { normalizeRunResult } from '@/components/holdings/holdings-shared';

export const dynamic = 'force-dynamic';

interface RouteParams {
  params: { runId: string };
}

export async function GET(_request: Request, { params }: RouteParams): Promise<NextResponse> {
  const runId = params.runId?.trim();
  if (!runId) {
    return NextResponse.json(
      { success: false, data: null, error: 'Run id is required' },
      { status: 400 },
    );
  }

  const result = await gatewayFetch<unknown>(`/v1/runs/${encodeURIComponent(runId)}`);
  if (result.status === 404) {
    return NextResponse.json(
      { success: false, data: null, error: 'Run not found' },
      { status: 404 },
    );
  }
  if (!result.ok) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Orchestrator unavailable' },
      { status: 502 },
    );
  }

  const run = normalizeRunResult(result.data);
  if (run === null) {
    return NextResponse.json(
      { success: false, data: null, error: 'Run result had an unexpected shape' },
      { status: 502 },
    );
  }
  return NextResponse.json({
    success: true,
    data: { ...run, runId: run.runId || runId },
    error: null,
  });
}
