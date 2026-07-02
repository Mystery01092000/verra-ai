import { NextResponse } from 'next/server';
import { gatewayFetch, gatewayPostJson } from '../gateway';

export const dynamic = 'force-dynamic';

/** GET — list runs awaiting human approval (PRD FR-TR-2). */
export async function GET(): Promise<NextResponse> {
  const result = await gatewayFetch<unknown>('/v1/runs?status=needs_approval');
  if (!result.ok || result.data === null) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Orchestrator unavailable' },
      { status: 502 },
    );
  }

  // Tolerant: gateway may return {runs: [...]} or a bare array.
  const payload = result.data as { runs?: unknown[] } | unknown[];
  const runs = Array.isArray(payload) ? payload : (payload.runs ?? []);

  return NextResponse.json({ success: true, data: { runs }, error: null });
}

interface DecisionRequest {
  runId: string;
  action: 'approve' | 'reject';
  approver: string;
  note?: string;
}

const RUN_ID_PATTERN = /^[A-Za-z0-9_.:-]{1,128}$/;

function parseDecisionRequest(raw: unknown): DecisionRequest | string {
  if (typeof raw !== 'object' || raw === null) return 'Request body must be a JSON object';
  const body = raw as Record<string, unknown>;

  if (typeof body.runId !== 'string' || !RUN_ID_PATTERN.test(body.runId)) {
    return 'runId is required';
  }
  if (body.action !== 'approve' && body.action !== 'reject') {
    return 'action must be "approve" or "reject"';
  }
  if (typeof body.approver !== 'string' || body.approver.trim().length === 0) {
    return 'approver name is required — a licensed human must sign off';
  }
  const note =
    typeof body.note === 'string' && body.note.trim().length > 0
      ? body.note.trim().slice(0, 2000)
      : undefined;

  return {
    runId: body.runId,
    action: body.action,
    approver: body.approver.trim().slice(0, 200),
    note,
  };
}

/** POST — record a human approve/reject decision for a run. */
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

  const parsed = parseDecisionRequest(raw);
  if (typeof parsed === 'string') {
    return NextResponse.json({ success: false, data: null, error: parsed }, { status: 400 });
  }

  const result = await gatewayPostJson<Record<string, unknown>>(
    `/v1/runs/${encodeURIComponent(parsed.runId)}/${parsed.action}`,
    { approver: parsed.approver, ...(parsed.note ? { note: parsed.note } : {}) },
  );

  if (!result.ok) {
    const status = result.status === 502 ? 502 : result.status;
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Decision could not be recorded' },
      { status },
    );
  }

  return NextResponse.json({ success: true, data: result.data ?? {}, error: null });
}
