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
  age?: number;
  tdsCredit?: number;
}

const MAX_AMOUNT = 1_000_000_000_0; // guard against absurd inputs (₹1,000 crore)

function parseComputeRequest(raw: unknown): ComputeRequest | string {
  if (typeof raw !== 'object' || raw === null) return 'Request body must be a JSON object';
  const body = raw as Record<string, unknown>;

  const assessmentYear = body.assessmentYear;
  if (typeof assessmentYear !== 'string' || !/^\d{4}-\d{2}$/.test(assessmentYear)) {
    return 'assessmentYear must look like "2025-26"';
  }
  const regime = body.regime;
  if (regime !== 'old' && regime !== 'new') return 'regime must be "old" or "new"';

  const amounts = {} as Record<'grossSalary' | 'section80c' | 'section80d', number>;
  for (const key of ['grossSalary', 'section80c', 'section80d'] as const) {
    const value = body[key];
    if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > MAX_AMOUNT) {
      return `${key} must be a non-negative number`;
    }
    amounts[key] = value;
  }

  const age = typeof body.age === 'number' && body.age >= 0 && body.age <= 120 ? body.age : 30;
  const tdsCredit =
    typeof body.tdsCredit === 'number' && body.tdsCredit >= 0 && body.tdsCredit <= MAX_AMOUNT
      ? body.tdsCredit
      : 0;

  return {
    assessmentYear,
    regime,
    grossSalary: amounts.grossSalary,
    section80c: amounts.section80c,
    section80d: amounts.section80d,
    age,
    tdsCredit,
  };
}

/** Wire format matches verra_shared.tax.models.TaxInput (camelCase aliases). */
function toWirePayload(req: ComputeRequest, regime: 'old' | 'new'): Record<string, unknown> {
  return {
    assessmentYear: req.assessmentYear,
    taxpayerType: 'resident_ordinarily',
    regime,
    age: req.age,
    income: { salary: req.grossSalary },
    deductions: {
      // Backend caps this per regime (₹75k new / ₹50k old — Finance Act 2024).
      standardDeduction: 75_000,
      section80C: req.section80c,
      section80D: req.section80d,
    },
    tdsTcsCredit: req.tdsCredit,
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
