import { NextResponse } from 'next/server';
import { gatewayFetch } from '../../gateway';

export const dynamic = 'force-dynamic';

interface VerifyPayload {
  ok?: boolean;
  first_bad_index?: number | null;
  firstBadIndex?: number | null;
  length?: number;
}

export async function GET(): Promise<NextResponse> {
  const result = await gatewayFetch<VerifyPayload>('/v1/audit/verify');
  if (!result.ok || result.data === null) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Audit service unavailable' },
      { status: 502 },
    );
  }

  const payload = result.data;
  return NextResponse.json({
    success: true,
    data: {
      ok: payload.ok === true,
      firstBadIndex: payload.firstBadIndex ?? payload.first_bad_index ?? null,
      length: typeof payload.length === 'number' ? payload.length : null,
    },
    error: null,
  });
}
