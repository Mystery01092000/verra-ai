import { NextResponse } from 'next/server';
import { gatewayPostJson } from '../../gateway';

export const dynamic = 'force-dynamic';

/** Editable assumptions sent by the tax dashboard (PRD FR-TX-12). */
interface ComputeRequest {
  assessmentYear: string;
  regime: 'old' | 'new';
  grossSalary: number;
  section80c: number;
  section80d: number;
  section80ccd1b?: number;
  section24?: number;
  capitalGains?: number;
  houseProperty?: number;
  otherSources?: number;
  age?: number;
  tdsCredit?: number;
  advanceTaxPaid?: number;
}

const MAX_AMOUNT = 1_000_000_000_0; // guard against absurd inputs (₹1,000 crore)

function parseAmount(val: unknown, fallback: number = 0): number | string {
  if (val === undefined || val === null) return fallback;
  if (typeof val !== 'number' || !Number.isFinite(val) || val < 0 || val > MAX_AMOUNT) {
    return 'amounts must be non-negative finite numbers';
  }
  return val;
}

function parseComputeRequest(raw: unknown): ComputeRequest | string {
  if (typeof raw !== 'object' || raw === null) return 'Request body must be a JSON object';
  const body = raw as Record<string, unknown>;

  const assessmentYear = body.assessmentYear;
  if (typeof assessmentYear !== 'string' || !/^\d{4}-\d{2}$/.test(assessmentYear)) {
    return 'assessmentYear must look like "2025-26"';
  }
  const regime = body.regime;
  if (regime !== 'old' && regime !== 'new') return 'regime must be "old" or "new"';

  // Support both top-level and nested income / deductions
  const rawIncome = typeof body.income === 'object' && body.income !== null ? (body.income as Record<string, unknown>) : {};
  const rawDeductions = typeof body.deductions === 'object' && body.deductions !== null ? (body.deductions as Record<string, unknown>) : {};

  const grossSalary = parseAmount(body.grossSalary ?? rawIncome.salary, 0);
  if (typeof grossSalary === 'string') return `grossSalary: ${grossSalary}`;

  const capitalGains = parseAmount(body.capitalGains ?? rawIncome.capitalGains ?? rawIncome.capital_gains, 0);
  if (typeof capitalGains === 'string') return `capitalGains: ${capitalGains}`;

  const houseProperty = parseAmount(body.houseProperty ?? rawIncome.houseProperty ?? rawIncome.house_property, 0);
  if (typeof houseProperty === 'string') return `houseProperty: ${houseProperty}`;

  const otherSources = parseAmount(body.otherSources ?? rawIncome.otherSources ?? rawIncome.other_sources, 0);
  if (typeof otherSources === 'string') return `otherSources: ${otherSources}`;

  const s80c = parseAmount(body.section80c ?? rawDeductions.section80C ?? rawDeductions.section_80c, 0);
  if (typeof s80c === 'string') return `section80c: ${s80c}`;

  const s80d = parseAmount(body.section80d ?? rawDeductions.section80D ?? rawDeductions.section_80d, 0);
  if (typeof s80d === 'string') return `section80d: ${s80d}`;

  const s80ccd1b = parseAmount(body.section80ccd1b ?? rawDeductions.section80ccd1b ?? rawDeductions.section_80ccd1b, 0);
  if (typeof s80ccd1b === 'string') return `section80ccd1b: ${s80ccd1b}`;

  const s24 = parseAmount(body.section24 ?? rawDeductions.section24 ?? rawDeductions.section_24, 0);
  if (typeof s24 === 'string') return `section24: ${s24}`;

  const age = typeof body.age === 'number' && body.age >= 0 && body.age <= 120 ? body.age : 30;
  const tdsCredit = parseAmount(body.tdsCredit, 0);
  if (typeof tdsCredit === 'string') return `tdsCredit: ${tdsCredit}`;

  const advanceTaxPaid = parseAmount(body.advanceTaxPaid, 0);
  if (typeof advanceTaxPaid === 'string') return `advanceTaxPaid: ${advanceTaxPaid}`;

  return {
    assessmentYear,
    regime,
    grossSalary,
    capitalGains,
    houseProperty,
    otherSources,
    section80c: s80c,
    section80d: s80d,
    section80ccd1b: s80ccd1b,
    section24: s24,
    age,
    tdsCredit,
    advanceTaxPaid,
  };
}

/** Wire format matches verra_shared.tax.models.TaxInput (camelCase aliases). */
function toWirePayload(req: ComputeRequest, regime: 'old' | 'new'): Record<string, unknown> {
  return {
    assessmentYear: req.assessmentYear,
    taxpayerType: 'resident_ordinarily',
    regime,
    age: req.age,
    income: {
      salary: req.grossSalary,
      houseProperty: req.houseProperty ?? 0,
      capitalGains: req.capitalGains ?? 0,
      otherSources: req.otherSources ?? 0,
    },
    deductions: {
      // Backend caps this per regime (₹75k new / ₹50k old — Finance Act 2024).
      standardDeduction: 75_000,
      section80c: req.section80c,
      section80d: req.section80d,
      section80ccd1b: req.section80ccd1b ?? 0,
      section24: req.section24 ?? 0,
    },
    tdsTcsCredit: req.tdsCredit,
    advanceTaxPaid: req.advanceTaxPaid ?? 0,
  };
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

  const parsed = parseComputeRequest(raw);
  if (typeof parsed === 'string') {
    return NextResponse.json({ success: false, data: null, error: parsed }, { status: 400 });
  }

  const [liability, comparison] = await Promise.all([
    gatewayPostJson<Record<string, unknown>>(
      '/v1/tools/tax/compute_tax_liability',
      toWirePayload(parsed, parsed.regime),
    ),
    gatewayPostJson<Record<string, unknown>>(
      '/v1/tools/tax/compare_regimes',
      toWirePayload(parsed, parsed.regime),
    ),
  ]);

  if (!liability.ok || liability.data === null) {
    return NextResponse.json(
      { success: false, data: null, error: liability.error ?? 'Tax calculator unavailable' },
      { status: 502 },
    );
  }

  return NextResponse.json({
    success: true,
    data: {
      liability: liability.data,
      // Comparison is optional — dashboard degrades gracefully without it.
      comparison: comparison.ok ? comparison.data : null,
    },
    error: null,
  });
}
