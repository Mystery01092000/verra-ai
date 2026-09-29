/**
 * Pure deterministic Indian income-tax calculator (AY 2025-26) in TypeScript.
 * Matches backend `verra_shared.tax.liability` and `compare` logic exactly.
 * Used for instant, zero-latency scenario modeling and offline fallback.
 */

import type { TaxComputation, RawCitation, RegimeComparisonView } from './tax-data';

export interface ScenarioInput {
  assessmentYear?: string;
  regime: 'old' | 'new';
  salary: number;
  houseProperty?: number;
  capitalGains?: number;
  otherSources?: number;
  section80c?: number;
  section80d?: number;
  section80ccd1b?: number;
  section24?: number;
  tdsCredit?: number;
  advanceTaxPaid?: number;
  age?: number;
}

const OLD_SLABS: Array<[number, number | null, number]> = [
  [0, 250_000, 0.0],
  [250_000, 500_000, 0.05],
  [500_000, 1_000_000, 0.20],
  [1_000_000, null, 0.30],
];

const NEW_SLABS: Array<[number, number | null, number]> = [
  [0, 300_000, 0.0],
  [300_000, 700_000, 0.05],
  [700_000, 1_000_000, 0.10],
  [1_000_000, 1_200_000, 0.15],
  [1_200_000, 1_500_000, 0.20],
  [1_500_000, null, 0.30],
];

const SURCHARGE_BRACKETS: Array<[number, number | null, number]> = [
  [5_000_000, 10_000_000, 0.10],
  [10_000_000, 20_000_000, 0.15],
  [20_000_000, 50_000_000, 0.25],
  [50_000_000, null, 0.37],
];

export function computeScenarioTax(input: ScenarioInput): TaxComputation {
  const regime = input.regime;
  const salary = Math.max(0, input.salary || 0);
  const houseProperty = input.houseProperty || 0;
  const capitalGains = Math.max(0, input.capitalGains || 0);
  const otherSources = Math.max(0, input.otherSources || 0);

  const grossTotalIncome = salary + houseProperty + capitalGains + otherSources;

  let totalDeductions = 0;
  const citations: RawCitation[] = [];

  if (regime === 'new') {
    // Under New Regime: only standard deduction on salary allowed (Finance Act 2024: ₹75,000)
    const stdDed = Math.min(salary, 75_000);
    totalDeductions = stdDed;
    citations.push({
      section: '16(ia)',
      field: 'standard_deduction',
      capped_amount: stdDed,
      source: 'Finance Act 2024 — standard deduction ₹75,000 under new regime',
    });
  } else {
    // Under Old Regime
    const stdDed = Math.min(salary, 50_000);
    const s80c = Math.min(Math.max(0, input.section80c || 0), 150_000);
    const s80d = Math.min(Math.max(0, input.section80d || 0), 25_000);
    const s80ccd1b = Math.min(Math.max(0, input.section80ccd1b || 0), 50_000);
    const s24 = Math.min(Math.max(0, input.section24 || 0), 200_000);

    totalDeductions = stdDed + s80c + s80d + s80ccd1b + s24;

    citations.push({
      section: '16(ia)',
      field: 'standard_deduction',
      capped_amount: stdDed,
      source: 'Section 16(ia) — standard deduction ₹50,000 under old regime',
    });
    if (s80c > 0) {
      citations.push({ section: '80C', field: 'section_80c', capped_amount: s80c });
    }
    if (s80d > 0) {
      citations.push({ section: '80D', field: 'section_80d', capped_amount: s80d });
    }
    if (s80ccd1b > 0) {
      citations.push({ section: '80CCD(1B)', field: 'section_80ccd1b', capped_amount: s80ccd1b });
    }
    if (s24 > 0) {
      citations.push({ section: '24(b)', field: 'section_24', capped_amount: s24 });
    }
  }

  const taxableIncome = Math.max(0, grossTotalIncome - totalDeductions);

  // Apply slabs
  const slabs = regime === 'new' ? NEW_SLABS : OLD_SLABS;
  let tax = 0;
  for (const [min, max, rate] of slabs) {
    if (taxableIncome <= min) break;
    const slabTop = max !== null ? max : Infinity;
    const taxableInSlab = Math.min(taxableIncome, slabTop) - min;
    if (taxableInSlab > 0) {
      tax += taxableInSlab * rate;
    }
  }
  const taxBeforeRebate = Math.max(0, tax);
  citations.push({ type: 'rule', section: 'slabs', regime });

  // Rebate 87A
  let rebate87a = 0;
  if (regime === 'new' && taxableIncome <= 700_000) {
    rebate87a = Math.min(taxBeforeRebate, 25_000);
    citations.push({
      type: 'rule',
      section: 'rebate_87a',
      amount: rebate87a,
      source: 'Section 87A — zero tax up to ₹7,00,000 under new regime',
    });
  } else if (regime === 'old' && taxableIncome <= 500_000) {
    rebate87a = Math.min(taxBeforeRebate, 12_500);
    citations.push({
      type: 'rule',
      section: 'rebate_87a',
      amount: rebate87a,
      source: 'Section 87A — rebate up to ₹12,500 under old regime',
    });
  }

  const taxAfterRebate = Math.max(0, taxBeforeRebate - rebate87a);

  // Surcharge
  let surchargeRate = 0;
  for (const [min, max, rate] of SURCHARGE_BRACKETS) {
    if (taxableIncome > min && (max === null || taxableIncome <= max)) {
      surchargeRate = rate;
      break;
    }
  }
  // Cap surcharge at 25% under new regime per Finance Act 2023/24
  if (regime === 'new' && surchargeRate > 0.25) {
    surchargeRate = 0.25;
  }
  const surcharge = taxAfterRebate * surchargeRate;

  // Cess 4%
  const cess = Math.round((taxAfterRebate + surcharge) * 0.04);
  citations.push({ type: 'rule', section: 'cess', rate: 0.04 });

  const totalTax = taxAfterRebate + surcharge + cess;
  const tdsCredit = Math.max(0, input.tdsCredit || 0);
  const advanceTax = Math.max(0, input.advanceTaxPaid || 0);
  const netTaxRefundDue = totalTax - tdsCredit - advanceTax;
  const effectiveTaxRate = grossTotalIncome > 0 ? totalTax / grossTotalIncome : 0;

  return {
    regime,
    grossTotalIncome,
    totalDeductions,
    taxableIncome,
    taxBeforeRebate,
    rebate87a,
    surcharge,
    cess,
    totalTax,
    tdsCredit,
    netTaxRefundDue,
    effectiveTaxRate,
    citations,
  };
}

export function compareScenarioRegimes(input: Omit<ScenarioInput, 'regime'>): RegimeComparisonView {
  const oldComp = computeScenarioTax({ ...input, regime: 'old' });
  const newComp = computeScenarioTax({ ...input, regime: 'new' });

  const recommendedRegime = newComp.totalTax <= oldComp.totalTax ? 'new' : 'old';
  const taxSaving = Math.abs(oldComp.totalTax - newComp.totalTax);

  const summary =
    recommendedRegime === 'new'
      ? `New regime saves ₹${taxSaving.toLocaleString('en-IN')} in total tax (₹${newComp.totalTax.toLocaleString('en-IN')} vs ₹${oldComp.totalTax.toLocaleString('en-IN')} under old regime).`
      : `Old regime saves ₹${taxSaving.toLocaleString('en-IN')} due to deductions (₹${oldComp.totalTax.toLocaleString('en-IN')} vs ₹${newComp.totalTax.toLocaleString('en-IN')} under new regime).`;

  return {
    oldRegime: oldComp,
    newRegime: newComp,
    recommendedRegime,
    taxSaving,
    summary,
    citations: [{ type: 'rule', section: 'regime_choice' }],
  };
}
