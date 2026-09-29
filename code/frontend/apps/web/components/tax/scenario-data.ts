import type { TaxComputation, RegimeComparisonView } from './tax-data';
import { computeScenarioTax, compareScenarioRegimes } from './scenario-calculator';

export interface ScenarioAssumptions {
  id: string;
  name: string;
  tagline: string;
  isBaseline: boolean;
  regime: 'old' | 'new';
  salary: number;
  capitalGains: number;
  houseProperty: number;
  otherSources: number;
  section80c: number;
  section80d: number;
  section80ccd1b: number; // NPS
  section24: number; // Home loan interest
  tdsCredit: number;
  advanceTaxPaid: number;
}

export interface ScenarioEvaluation {
  assumptions: ScenarioAssumptions;
  computation: TaxComputation;
  comparison: RegimeComparisonView;
  taxDeltaVsBaseline: number; // baseline.totalTax - scenario.totalTax (positive = saving)
  taxDeltaPercentVsBaseline: number;
  effectiveRateDeltaVsBaseline: number;
  inHandIncome: number; // gross - totalTax
  inHandDeltaVsBaseline: number;
}

export interface ScenarioPreset {
  id: string;
  title: string;
  description: string;
  badge: string;
  apply: (base: ScenarioAssumptions) => Partial<ScenarioAssumptions>;
}

export const BASELINE_ASSUMPTIONS: ScenarioAssumptions = {
  id: 'baseline',
  name: 'Baseline Assessment',
  tagline: 'Current financial profile & default tax posture',
  isBaseline: true,
  regime: 'new',
  salary: 1_400_000,
  capitalGains: 0,
  houseProperty: 0,
  otherSources: 50_000,
  section80c: 120_000,
  section80d: 15_000,
  section80ccd1b: 0,
  section24: 0,
  tdsCredit: 95_000,
  advanceTaxPaid: 0,
};

export const SCENARIO_PRESETS: ScenarioPreset[] = [
  {
    id: 'maximize-80c-nps',
    title: 'Maximize 80C + NPS (Old Regime)',
    description: 'Max out ₹1.5L in 80C (ELSS/PPF) + ₹50k in Section 80CCD(1B) NPS in Old Regime',
    badge: 'Deduction Max',
    apply: () => ({
      regime: 'old',
      section80c: 150_000,
      section80ccd1b: 50_000,
      section80d: 25_000,
    }),
  },
  {
    id: 'switch-regime',
    title: 'Switch Regime (New vs Old)',
    description: 'Toggle between Old and New regimes to compare pure slab and 87A rebate efficiency',
    badge: 'Regime Switch',
    apply: (base) => ({
      regime: base.regime === 'new' ? 'old' : 'new',
    }),
  },
  {
    id: 'home-loan-interest',
    title: 'Home Loan Section 24(b)',
    description: 'Claim ₹2,00,000 deduction on self-occupied housing loan interest under Old Regime',
    badge: 'Housing Loan',
    apply: () => ({
      regime: 'old',
      section24: 200_000,
      section80c: 150_000,
    }),
  },
  {
    id: 'capital-gains-liquidation',
    title: 'Realize Capital Gains',
    description: 'Model ₹3,00,000 equity liquidation / capital gains inflow on total tax brackets',
    badge: 'Investment Sale',
    apply: (base) => ({
      capitalGains: base.capitalGains + 300_000,
    }),
  },
  {
    id: 'comprehensive-family-health',
    title: 'Full Health Cover (80D)',
    description: 'Increase health insurance premium deduction for self and senior parents',
    badge: 'Health Cover',
    apply: () => ({
      regime: 'old',
      section80d: 25_000, // Self cap (v1 engine cap)
    }),
  },
];

export function evaluateScenario(
  scenario: ScenarioAssumptions,
  baselineComp: TaxComputation,
): ScenarioEvaluation {
  const computation = computeScenarioTax(scenario);
  const comparison = compareScenarioRegimes(scenario);

  const taxDelta = baselineComp.totalTax - computation.totalTax;
  const taxDeltaPercent =
    baselineComp.totalTax > 0 ? (taxDelta / baselineComp.totalTax) * 100 : 0;
  const effectiveRateDelta = baselineComp.effectiveTaxRate - computation.effectiveTaxRate;

  const inHandIncome = computation.grossTotalIncome - computation.totalTax;
  const baselineInHand = baselineComp.grossTotalIncome - baselineComp.totalTax;
  const inHandDelta = inHandIncome - baselineInHand;

  return {
    assumptions: scenario,
    computation,
    comparison,
    taxDeltaVsBaseline: taxDelta,
    taxDeltaPercentVsBaseline: taxDeltaPercent,
    effectiveRateDeltaVsBaseline: effectiveRateDelta,
    inHandIncome,
    inHandDeltaVsBaseline: inHandDelta,
  };
}
