import { NextRequest, NextResponse } from 'next/server';
import { gatewayFetch } from '../../gateway';
import {
  DEMO_CLIENT_ID,
  DEMO_TENANT_ID,
  normalizeConsolidation,
} from '@/components/holdings/holdings-shared';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest): Promise<NextResponse> {
  const params = new URLSearchParams({
    tenantId: DEMO_TENANT_ID,
    clientId: DEMO_CLIENT_ID,
  });

  const rawIncome = request.nextUrl.searchParams.get('annualIncome');
  if (rawIncome !== null && rawIncome.trim() !== '') {
    const income = Number(rawIncome);
    if (!Number.isFinite(income) || income < 0) {
      return NextResponse.json(
        { success: false, data: null, error: 'annualIncome must be a non-negative number' },
        { status: 400 },
      );
    }
    params.set('annualIncome', String(income));
  }

  const result = await gatewayFetch<unknown>(`/v1/holdings/consolidation?${params.toString()}`);
  if (!result.ok) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Consolidation service unavailable' },
      { status: 502 },
    );
  }

  const report = normalizeConsolidation(result.data);
  if (report === null) {
    return NextResponse.json(
      { success: false, data: null, error: 'Consolidation returned an unexpected shape' },
      { status: 502 },
    );
  }
  return NextResponse.json({ success: true, data: report, error: null });
}
