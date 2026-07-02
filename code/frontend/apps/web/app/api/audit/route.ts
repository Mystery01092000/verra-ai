import { NextResponse } from 'next/server';
import { gatewayFetch } from '../gateway';

export const dynamic = 'force-dynamic';

const DEFAULT_LIMIT = 50;
const MAX_LIMIT = 200;

export async function GET(request: Request): Promise<NextResponse> {
  const url = new URL(request.url);
  const rawLimit = Number(url.searchParams.get('limit') ?? DEFAULT_LIMIT);
  const limit =
    Number.isFinite(rawLimit) && rawLimit >= 1 && rawLimit <= MAX_LIMIT
      ? Math.floor(rawLimit)
      : DEFAULT_LIMIT;

  const result = await gatewayFetch<unknown>(`/v1/audit/events?limit=${limit}`);
  if (!result.ok || result.data === null) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Audit service unavailable' },
      { status: 502 },
    );
  }

  // Tolerant: gateway may return {events: [...]} or a bare array.
  const payload = result.data as { events?: unknown[] } | unknown[];
  const events = Array.isArray(payload) ? payload : (payload.events ?? []);

  return NextResponse.json({ success: true, data: { events }, error: null });
}
