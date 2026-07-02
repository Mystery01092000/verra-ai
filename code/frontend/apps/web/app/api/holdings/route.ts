import { NextResponse } from 'next/server';
import { gatewayFetch, gatewayPostJson } from '../gateway';
import {
  DEMO_CLIENT_ID,
  DEMO_TENANT_ID,
  normalizeHolding,
  normalizeHoldingsResponse,
} from '@/components/holdings/holdings-shared';

export const dynamic = 'force-dynamic';

const DEMO_QUERY = `tenantId=${DEMO_TENANT_ID}&clientId=${DEMO_CLIENT_ID}`;

const STRING_FIELDS = ['type', 'name', 'institution', 'currency', 'maturityDate'] as const;
const NUMBER_FIELDS = [
  'currentValue',
  'investedValue',
  'units',
  'premiumAnnual',
  'sumAssured',
  'outstandingAmount',
  'interestRate',
  'emi',
] as const;

/** Whitelists and validates the add-holding payload. Returns an error string on failure. */
function parseAddHolding(raw: unknown): Record<string, unknown> | string {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    return 'Request body must be a JSON object';
  }
  const body = raw as Record<string, unknown>;
  if (typeof body.type !== 'string' || body.type.trim() === '') {
    return 'type is required';
  }
  if (typeof body.name !== 'string' || body.name.trim() === '') {
    return 'name is required';
  }

  const payload: Record<string, unknown> = {
    tenantId: DEMO_TENANT_ID,
    clientId: DEMO_CLIENT_ID,
  };
  for (const key of STRING_FIELDS) {
    const value = body[key];
    if (value === undefined) continue;
    if (typeof value !== 'string') return `${key} must be a string`;
    if (value.trim() !== '') payload[key] = value.trim();
  }
  for (const key of NUMBER_FIELDS) {
    const value = body[key];
    if (value === undefined || value === null) continue;
    if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) {
      return `${key} must be a non-negative number`;
    }
    payload[key] = value;
  }
  if (payload.currentValue === undefined) payload.currentValue = 0;
  if (payload.currency === undefined) payload.currency = 'INR';
  return payload;
}

export async function GET(): Promise<NextResponse> {
  const result = await gatewayFetch<unknown>(`/v1/holdings?${DEMO_QUERY}`);
  if (!result.ok) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Holdings service unavailable' },
      { status: 502 },
    );
  }
  return NextResponse.json({
    success: true,
    data: { holdings: normalizeHoldingsResponse(result.data) },
    error: null,
  });
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

  const payload = parseAddHolding(raw);
  if (typeof payload === 'string') {
    return NextResponse.json({ success: false, data: null, error: payload }, { status: 400 });
  }

  const result = await gatewayPostJson<unknown>('/v1/holdings', payload);
  if (!result.ok) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Holdings service unavailable' },
      { status: 502 },
    );
  }
  return NextResponse.json({
    success: true,
    data: { holding: normalizeHolding(result.data) },
    error: null,
  });
}
