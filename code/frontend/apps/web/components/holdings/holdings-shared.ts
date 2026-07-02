/**
 * Shared holdings types, demo tenant constants, and shape-tolerant
 * normalizers. Imported by both the /holdings client components and the
 * app/api/holdings server routes (no 'use client' directive on purpose).
 */

export const DEMO_TENANT_ID = 'demo';
export const DEMO_CLIENT_ID = 'demo-client';

export type HoldingType =
  | 'mutual_fund'
  | 'stock'
  | 'bond'
  | 'fixed_deposit'
  | 'recurring_deposit'
  | 'ppf'
  | 'epf'
  | 'nps'
  | 'insurance_life'
  | 'insurance_health'
  | 'insurance_ulip'
  | 'loan_home'
  | 'loan_personal'
  | 'loan_vehicle'
  | 'loan_education'
  | 'real_estate'
  | 'gold'
  | 'cash'
  | 'other';

export interface Holding {
  id: string;
  type: HoldingType | string;
  name: string;
  institution?: string;
  currentValue: number;
  investedValue?: number;
  units?: number;
  currency: string;
  premiumAnnual?: number;
  sumAssured?: number;
  outstandingAmount?: number;
  interestRate?: number;
  emi?: number;
  maturityDate?: string;
}

export interface ConsolidationBreakdownItem {
  category: string;
  amount: number;
  percentage: number;
}

export interface ConsolidationFlag {
  type: string;
  message: string;
  citation?: string;
}

export interface ConsolidationReport {
  totalAssets: number;
  totalLiabilities: number;
  netWorth: number;
  breakdown: ConsolidationBreakdownItem[];
  flags: ConsolidationFlag[];
  citations: string[];
}

export type RunStatus = 'planned' | 'executing' | 'done' | 'awaiting_approval' | 'failed';

export interface PlanningRunResult {
  runId: string;
  status: RunStatus | string;
  content: string | null;
  citations: string[];
}

// ── Tolerant field pickers (camelCase / snake_case) ─────────────────

function asRecord(raw: unknown): Record<string, unknown> | null {
  if (typeof raw === 'object' && raw !== null && !Array.isArray(raw)) {
    return raw as Record<string, unknown>;
  }
  return null;
}

function pickNumber(raw: Record<string, unknown>, ...keys: string[]): number | undefined {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    if (typeof value === 'string' && value.trim() !== '' && Number.isFinite(Number(value))) {
      return Number(value);
    }
  }
  return undefined;
}

function pickString(raw: Record<string, unknown>, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === 'string' && value.length > 0) return value;
  }
  return undefined;
}

function citationToLabel(raw: unknown): string | null {
  if (typeof raw === 'string' && raw.trim()) return raw;
  const record = asRecord(raw);
  if (record) {
    const label = pickString(
      record,
      'label',
      'source',
      'title',
      'section',
      'sourceId',
      'source_id',
    );
    if (label) return label;
  }
  return null;
}

export function normalizeCitations(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  return raw.map(citationToLabel).filter((c): c is string => c !== null);
}

// ── Holdings ─────────────────────────────────────────────────────────

export function normalizeHolding(raw: unknown): Holding | null {
  const record = asRecord(raw);
  if (!record) return null;
  const id = pickString(record, 'id', 'holdingId', 'holding_id');
  const type = pickString(record, 'type');
  const name = pickString(record, 'name');
  if (!id || !type || !name) return null;
  return {
    id,
    type,
    name,
    institution: pickString(record, 'institution'),
    currentValue: pickNumber(record, 'currentValue', 'current_value') ?? 0,
    investedValue: pickNumber(record, 'investedValue', 'invested_value'),
    units: pickNumber(record, 'units'),
    currency: pickString(record, 'currency') ?? 'INR',
    premiumAnnual: pickNumber(record, 'premiumAnnual', 'premium_annual'),
    sumAssured: pickNumber(record, 'sumAssured', 'sum_assured'),
    outstandingAmount: pickNumber(record, 'outstandingAmount', 'outstanding_amount'),
    interestRate: pickNumber(record, 'interestRate', 'interest_rate'),
    emi: pickNumber(record, 'emi'),
    maturityDate: pickString(record, 'maturityDate', 'maturity_date'),
  };
}

/** Accepts `{holdings: [...]}` or a bare array. */
export function normalizeHoldingsResponse(raw: unknown): Holding[] {
  const list = Array.isArray(raw) ? raw : (asRecord(raw)?.holdings ?? null);
  if (!Array.isArray(list)) return [];
  return list.map(normalizeHolding).filter((h): h is Holding => h !== null);
}

// ── Consolidation ────────────────────────────────────────────────────

function normalizeBreakdownItem(raw: unknown): ConsolidationBreakdownItem | null {
  const record = asRecord(raw);
  if (!record) return null;
  const category = pickString(record, 'category', 'label') ?? 'other';
  return {
    category,
    amount: pickNumber(record, 'amount', 'value') ?? 0,
    percentage: pickNumber(record, 'percentage', 'percent', 'pct') ?? 0,
  };
}

function normalizeFlag(raw: unknown): ConsolidationFlag | null {
  const record = asRecord(raw);
  if (!record) return null;
  const message = pickString(record, 'message', 'detail', 'description');
  if (!message) return null;
  return {
    type: pickString(record, 'type', 'code', 'severity') ?? 'advisory',
    message,
    citation: citationToLabel(record.citation) ?? undefined,
  };
}

export function normalizeConsolidation(raw: unknown): ConsolidationReport | null {
  const record = asRecord(raw);
  if (!record) return null;
  const breakdownRaw = record.breakdown;
  const flagsRaw = record.flags;
  return {
    totalAssets: pickNumber(record, 'totalAssets', 'total_assets') ?? 0,
    totalLiabilities: pickNumber(record, 'totalLiabilities', 'total_liabilities') ?? 0,
    netWorth: pickNumber(record, 'netWorth', 'net_worth') ?? 0,
    breakdown: Array.isArray(breakdownRaw)
      ? breakdownRaw
          .map(normalizeBreakdownItem)
          .filter((b): b is ConsolidationBreakdownItem => b !== null)
      : [],
    flags: Array.isArray(flagsRaw)
      ? flagsRaw.map(normalizeFlag).filter((f): f is ConsolidationFlag => f !== null)
      : [],
    citations: normalizeCitations(record.citations),
  };
}

// ── Planning runs (portfolio_analysis / financial_planning) ─────────

function extractRunContent(output: unknown): string | null {
  if (typeof output === 'string' && output.trim()) return output;
  const record = asRecord(output);
  if (!record) return null;
  if ('final' in record) {
    const fromFinal = extractRunContent(record.final);
    if (fromFinal) return fromFinal;
  }
  for (const key of ['content', 'answer', 'message', 'text', 'summary']) {
    const value = record[key];
    if (typeof value === 'string' && value.trim()) return value;
  }
  return null;
}

export function normalizeRunResult(raw: unknown): PlanningRunResult | null {
  const record = asRecord(raw);
  if (!record) return null;
  const runId = pickString(record, 'runId', 'run_id') ?? '';
  const status = pickString(record, 'status') ?? 'executing';
  return {
    runId,
    status,
    content: extractRunContent(record.output),
    citations: normalizeCitations(record.citations),
  };
}
