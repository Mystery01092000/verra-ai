import type { Citation } from './CitedAmount';

/** Editable dashboard assumptions (PRD FR-TX-12). */
export interface TaxAssumptions {
  grossSalary: number;
  section80c: number;
  section80d: number;
  regime: 'old' | 'new';
}

/** A raw citation object as emitted by the deterministic calculators. */
export type RawCitation = Record<string, unknown>;

export interface TaxComputation {
  regime: 'old' | 'new';
  grossTotalIncome: number;
  totalDeductions: number;
  taxableIncome: number;
  taxBeforeRebate: number;
  rebate87a: number;
  surcharge: number;
  cess: number;
  totalTax: number;
  tdsCredit: number;
  netTaxRefundDue: number;
  effectiveTaxRate: number;
  citations: RawCitation[];
}

export interface RegimeComparisonView {
  oldRegime: TaxComputation;
  newRegime: TaxComputation;
  recommendedRegime: 'old' | 'new';
  taxSaving: number;
  summary: string;
  citations: RawCitation[];
}

export interface TaxDashboardData {
  liability: TaxComputation;
  comparison: RegimeComparisonView | null;
}

/* ── Tolerant normalizers (accept camelCase or snake_case wire keys) ── */

function pickNumber(raw: Record<string, unknown>, ...keys: string[]): number {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === 'number' && Number.isFinite(value)) return value;
  }
  return 0;
}

function pickCitations(raw: Record<string, unknown>): RawCitation[] {
  const value = raw.citations;
  if (!Array.isArray(value)) return [];
  return value.filter((c): c is RawCitation => typeof c === 'object' && c !== null);
}

export function normalizeComputation(raw: Record<string, unknown>): TaxComputation {
  return {
    regime: raw.regime === 'old' ? 'old' : 'new',
    grossTotalIncome: pickNumber(raw, 'grossTotalIncome', 'gross_total_income'),
    totalDeductions: pickNumber(raw, 'totalDeductions', 'total_deductions'),
    taxableIncome: pickNumber(raw, 'taxableIncome', 'taxable_income'),
    taxBeforeRebate: pickNumber(raw, 'taxLiability', 'tax_liability'),
    rebate87a: pickNumber(raw, 'rebate87A', 'rebate_87a', 'rebate87a'),
    surcharge: pickNumber(raw, 'surcharge'),
    cess: pickNumber(raw, 'cess'),
    totalTax: pickNumber(raw, 'totalTax', 'total_tax'),
    tdsCredit: pickNumber(raw, 'tdsTcsCredit', 'tds_tcs_credit'),
    netTaxRefundDue: pickNumber(raw, 'netTaxRefundDue', 'net_tax_refund_due'),
    effectiveTaxRate: pickNumber(raw, 'effectiveTaxRate', 'effective_tax_rate'),
    citations: pickCitations(raw),
  };
}

export function normalizeComparison(
  raw: Record<string, unknown> | null,
): RegimeComparisonView | null {
  if (raw === null) return null;
  const oldRaw = raw.oldRegime ?? raw.old_regime;
  const newRaw = raw.newRegime ?? raw.new_regime;
  if (typeof oldRaw !== 'object' || oldRaw === null) return null;
  if (typeof newRaw !== 'object' || newRaw === null) return null;
  const recommended = raw.recommendedRegime ?? raw.recommended_regime;
  return {
    oldRegime: normalizeComputation(oldRaw as Record<string, unknown>),
    newRegime: normalizeComputation(newRaw as Record<string, unknown>),
    recommendedRegime: recommended === 'old' ? 'old' : 'new',
    taxSaving: pickNumber(raw, 'taxSaving', 'tax_saving'),
    summary: typeof raw.summary === 'string' ? raw.summary : '',
    citations: pickCitations(raw),
  };
}

/* ── Citation mapping for CitedAmount ── */

const SECTION_LABELS: Record<string, string> = {
  slabs: 'Income-tax slab rates (Income-tax Act, 1961)',
  rebate_87a: 'Rebate u/s 87A, Income-tax Act, 1961',
  cess: 'Health & Education Cess @ 4% (Finance Act)',
  '16(ia)': 'Standard deduction u/s 16(ia)',
  '80C': 'Deduction u/s 80C (capped at ₹1,50,000)',
  '80D': 'Deduction u/s 80D',
  regime_choice: 'Section 115BAC — regime choice (Finance Act 2023/24)',
};

/** Find the calculator citation for a rule section and adapt it for CitedAmount. */
export function ruleCitation(citations: RawCitation[], section: string): Citation | undefined {
  const found = citations.find((c) => c.section === section);
  if (!found) return undefined;
  const source = typeof found.source === 'string' ? found.source : undefined;
  const regime = typeof found.regime === 'string' ? ` — ${found.regime} regime` : '';
  return {
    type: 'rule',
    label: source ?? `${SECTION_LABELS[section] ?? `Section ${section}`}${regime}`,
  };
}

/** Citation for user-entered assumption figures (kept honest — not a document). */
export const ASSUMPTION_CITATION: Citation = {
  type: 'rule',
  label: 'User-entered assumption (editable above) — verify against Form 16',
};

/* ── Labeled sample data — shown ONLY when the backend is unreachable ── */

export const SAMPLE_ASSUMPTIONS: TaxAssumptions = {
  grossSalary: 1_200_000,
  section80c: 150_000,
  section80d: 25_000,
  regime: 'new',
};

const SAMPLE_RULE_CITATIONS: RawCitation[] = [
  { type: 'rule', section: 'slabs', regime: 'new' },
  { type: 'rule', section: 'rebate_87a', amount: 0 },
  { type: 'rule', section: 'cess', rate: 0.04 },
  { section: '16(ia)', field: 'standard_deduction', capped_amount: 75_000 },
];

const SAMPLE_NEW: TaxComputation = {
  regime: 'new',
  grossTotalIncome: 1_200_000,
  totalDeductions: 75_000,
  taxableIncome: 1_125_000,
  taxBeforeRebate: 68_750,
  rebate87a: 0,
  surcharge: 0,
  cess: 2_750,
  totalTax: 71_500,
  tdsCredit: 0,
  netTaxRefundDue: 71_500,
  effectiveTaxRate: 0.0636,
  citations: SAMPLE_RULE_CITATIONS,
};

const SAMPLE_OLD: TaxComputation = {
  regime: 'old',
  grossTotalIncome: 1_200_000,
  totalDeductions: 225_000,
  taxableIncome: 975_000,
  taxBeforeRebate: 107_500,
  rebate87a: 0,
  surcharge: 0,
  cess: 4_300,
  totalTax: 111_800,
  tdsCredit: 0,
  netTaxRefundDue: 111_800,
  effectiveTaxRate: 0.1147,
  citations: SAMPLE_RULE_CITATIONS,
};

export const SAMPLE_DATA: TaxDashboardData = {
  liability: SAMPLE_NEW,
  comparison: {
    oldRegime: SAMPLE_OLD,
    newRegime: SAMPLE_NEW,
    recommendedRegime: 'new',
    taxSaving: 40_300,
    summary:
      'New regime saves ₹40,300 in total tax (₹71,500 vs ₹1,11,800 under old regime). Sample figures for AY 2025-26.',
    citations: [{ type: 'rule', section: 'regime_choice' }],
  },
};
