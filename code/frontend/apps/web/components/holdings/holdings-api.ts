/** Client-side fetch helpers for the /api/holdings routes. */
import type { ConsolidationReport, Holding, PlanningRunResult } from './holdings-shared';

export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

export type ApiOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

const UNREACHABLE = 'Backend unreachable — the holdings service could not be contacted.';

async function requestJson<T>(input: string, init?: RequestInit): Promise<ApiOutcome<T>> {
  try {
    const res = await fetch(input, init);
    const envelope = (await res.json()) as ApiEnvelope<T>;
    if (!res.ok || !envelope.success || envelope.data === null) {
      return { ok: false, error: envelope.error ?? UNREACHABLE };
    }
    return { ok: true, data: envelope.data };
  } catch {
    return { ok: false, error: UNREACHABLE };
  }
}

export function fetchHoldings(): Promise<ApiOutcome<{ holdings: Holding[] }>> {
  return requestJson<{ holdings: Holding[] }>('/api/holdings');
}

export function addHolding(
  payload: Record<string, unknown>,
): Promise<ApiOutcome<{ holding: Holding | null }>> {
  return requestJson<{ holding: Holding | null }>('/api/holdings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export function deleteHolding(id: string): Promise<ApiOutcome<{ id: string }>> {
  return requestJson<{ id: string }>(`/api/holdings/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}

export function fetchConsolidation(
  annualIncome?: number,
): Promise<ApiOutcome<ConsolidationReport>> {
  const query =
    annualIncome !== undefined && Number.isFinite(annualIncome)
      ? `?annualIncome=${encodeURIComponent(String(annualIncome))}`
      : '';
  return requestJson<ConsolidationReport>(`/api/holdings/consolidation${query}`);
}

export function startPlanningRun(
  capability: 'portfolio_analysis' | 'financial_planning',
  annualIncome?: number,
): Promise<ApiOutcome<{ runId: string }>> {
  return requestJson<{ runId: string }>('/api/holdings/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      capability,
      ...(annualIncome !== undefined ? { annualIncome } : {}),
    }),
  });
}

export function pollPlanningRun(runId: string): Promise<ApiOutcome<PlanningRunResult>> {
  return requestJson<PlanningRunResult>(`/api/holdings/analyze/${encodeURIComponent(runId)}`);
}
