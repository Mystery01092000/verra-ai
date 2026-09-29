'use client';

import { useState, useId, useTransition } from 'react';
import Link from 'next/link';
import {
  BASELINE_ASSUMPTIONS,
  SCENARIO_PRESETS,
  evaluateScenario,
  type ScenarioAssumptions,
  type ScenarioEvaluation,
} from './scenario-data';
import { computeScenarioTax } from './scenario-calculator';
import { CitedAmount, type Citation } from './CitedAmount';

interface AmountInputProps {
  label: string;
  sublabel?: string;
  value: number;
  max?: number;
  disabled?: boolean;
  onChange: (val: number) => void;
}

function AmountInput({ label, sublabel, value, max, disabled = false, onChange }: AmountInputProps) {
  const inputId = useId();
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <label htmlFor={inputId} className="font-semibold text-ink">
          {label}
        </label>
        {max !== undefined && (
          <span className="text-[11px] text-muted">
            Max: ₹{max.toLocaleString('en-IN')}
          </span>
        )}
      </div>
      <div className="flex items-center rounded-btn border border-line bg-white px-3 py-1.5 focus-within:border-accent focus-within:shadow-glow transition-all">
        <span className="text-sm font-medium text-muted mr-1.5" aria-hidden="true">
          ₹
        </span>
        <input
          id={inputId}
          type="number"
          min={0}
          step={5000}
          disabled={disabled}
          value={value === 0 ? '' : value}
          placeholder="0"
          onChange={(e) => {
            const raw = Number(e.target.value);
            const clamped = max !== undefined ? Math.min(raw, max) : raw;
            onChange(Number.isFinite(clamped) && clamped >= 0 ? clamped : 0);
          }}
          className="w-full bg-transparent text-sm font-medium text-ink outline-none placeholder:text-muted/60 disabled:cursor-not-allowed disabled:text-muted"
        />
      </div>
      {sublabel && <p className="text-[11px] text-muted leading-tight">{sublabel}</p>}
    </div>
  );
}

export function ScenarioBuilder({ assessmentYear }: { assessmentYear: string }) {
  const [baseline, setBaseline] = useState<ScenarioAssumptions>(BASELINE_ASSUMPTIONS);
  const [activeScenario, setActiveScenario] = useState<ScenarioAssumptions>({
    ...BASELINE_ASSUMPTIONS,
    id: 'scenario-a',
    name: 'Maximize 80C + NPS (Old Regime)',
    tagline: 'Claim maximum eligible deductions under Section 80C and 80CCD(1B)',
    isBaseline: false,
    regime: 'old',
    section80c: 150_000,
    section80d: 25_000,
    section80ccd1b: 50_000,
  });

  const [promotedNotice, setPromotedNotice] = useState<string | null>(null);
  const [, startTransition] = useTransition();

  // Deterministic computations
  const baselineComp = computeScenarioTax(baseline);
  const scenarioEval: ScenarioEvaluation = evaluateScenario(activeScenario, baselineComp);

  function applyPreset(presetId: string) {
    const preset = SCENARIO_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;
    startTransition(() => {
      setActiveScenario((prev) => ({
        ...prev,
        ...preset.apply(baseline),
        name: preset.title,
        tagline: preset.description,
      }));
      setPromotedNotice(null);
    });
  }

  function handlePromoteToBaseline() {
    setBaseline({
      ...activeScenario,
      id: 'baseline',
      name: `Promoted: ${activeScenario.name}`,
      tagline: 'Adopted as workspace baseline profile',
      isBaseline: true,
    });
    setPromotedNotice(`Successfully promoted "${activeScenario.name}" to the baseline tax posture!`);
    setTimeout(() => setPromotedNotice(null), 6000);
  }

  function handleResetScenario() {
    setActiveScenario({
      ...baseline,
      id: 'scenario-custom',
      name: 'Custom Alternate Scenario',
      tagline: 'Side-by-side variation of baseline assumptions',
      isBaseline: false,
    });
    setPromotedNotice(null);
  }

  const taxDelta = scenarioEval.taxDeltaVsBaseline;
  const isSaving = taxDelta > 0;
  const isNeutral = taxDelta === 0;

  const stdDedCitation: Citation = {
    type: 'rule',
    label:
      activeScenario.regime === 'new'
        ? 'Section 16(ia) — Standard deduction ₹75,000 (Finance Act 2024)'
        : 'Section 16(ia) — Standard deduction ₹50,000 (Old regime)',
  };

  const regimeCitation: Citation = {
    type: 'rule',
    label: 'Section 115BAC — Default tax regime for Individuals (Finance Act 2024)',
  };

  return (
    <div className="space-y-6">
      {/* Header & Title */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-black tracking-tight text-ink">
            Scenario Modeling Studio
          </h2>
          <p className="text-sm text-ink-secondary">
            Simulate alternate investment, deduction, and income strategies against your baseline.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleResetScenario}
            className="rounded-btn border border-line bg-white/80 px-3.5 py-1.5 text-xs font-semibold text-ink-secondary hover:border-ink hover:text-ink transition-colors shadow-sm"
          >
            Reset to Baseline
          </button>
          <button
            type="button"
            onClick={handlePromoteToBaseline}
            className="rounded-btn px-4 py-1.5 text-xs font-semibold text-white shadow-sm transition-opacity hover:opacity-90"
            style={{ background: 'var(--gradient-brand)' }}
          >
            Promote to Baseline ✓
          </button>
        </div>
      </div>

      {/* Promoted Toast Notice */}
      {promotedNotice && (
        <div
          role="status"
          className="flex items-center justify-between rounded-card border border-ok/20 bg-ok/10 px-4 py-3 text-xs font-medium text-ok shadow-sm"
        >
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm">✓</span>
            <span>{promotedNotice}</span>
          </div>
          <button
            type="button"
            onClick={() => setPromotedNotice(null)}
            className="text-ok font-bold hover:opacity-75"
          >
            ✕
          </button>
        </div>
      )}

      {/* Quick Presets Strip */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-muted">
            Quick Strategy Presets
          </span>
          <span className="text-[11px] text-muted">Click to apply instant model</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
          {SCENARIO_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => applyPreset(preset.id)}
              className="group flex flex-col items-start rounded-card border border-line bg-white/80 p-3 text-left shadow-card hover:border-accent hover:shadow-glow transition-all"
            >
              <div className="flex w-full items-center justify-between gap-1 mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider rounded px-1.5 py-0.5 bg-periwinkle-soft text-accent group-hover:bg-accent group-hover:text-white transition-colors">
                  {preset.badge}
                </span>
                <span className="text-xs text-muted group-hover:text-accent font-bold">→</span>
              </div>
              <p className="text-xs font-bold text-ink group-hover:text-accent line-clamp-1">
                {preset.title}
              </p>
              <p className="mt-0.5 text-[11px] text-muted line-clamp-2 leading-relaxed">
                {preset.description}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Side-by-Side Hero Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Baseline Card */}
        <div className="relative rounded-card border border-line bg-white p-5 shadow-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-line pb-3 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full bg-ink-secondary" />
                <h3 className="font-display text-sm font-bold text-ink">{baseline.name}</h3>
                <span className="rounded-full bg-cream px-2 py-0.5 text-[10px] font-semibold text-ink-secondary">
                  Baseline
                </span>
              </div>
              <p className="text-[11px] text-muted mt-0.5">{baseline.tagline}</p>
            </div>
            <span className="rounded-full border border-line bg-cream px-2.5 py-1 text-xs font-semibold text-ink uppercase">
              {baseline.regime} Regime
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="rounded-btn bg-cream/60 p-3">
              <span className="text-[11px] text-muted font-medium">Total Tax Liability</span>
              <div className="text-xl font-display font-black text-ink mt-0.5">
                ₹{baselineComp.totalTax.toLocaleString('en-IN')}
              </div>
              <span className="text-[10px] text-muted">Effective: {(baselineComp.effectiveTaxRate * 100).toFixed(1)}%</span>
            </div>

            <div className="rounded-btn bg-cream/60 p-3">
              <span className="text-[11px] text-muted font-medium">Annual In-Hand</span>
              <div className="text-xl font-display font-black text-ink mt-0.5">
                ₹{(baselineComp.grossTotalIncome - baselineComp.totalTax).toLocaleString('en-IN')}
              </div>
              <span className="text-[10px] text-muted">From ₹{baselineComp.grossTotalIncome.toLocaleString('en-IN')} gross</span>
            </div>
          </div>

          <div className="text-xs space-y-1.5 pt-2 border-t border-line text-ink-secondary">
            <div className="flex justify-between">
              <span>Gross Total Income:</span>
              <span className="font-semibold text-ink">₹{baselineComp.grossTotalIncome.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between">
              <span>Total Deductions:</span>
              <span className="font-semibold text-ink">₹{baselineComp.totalDeductions.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between">
              <span>Taxable Income:</span>
              <span className="font-semibold text-ink">₹{baselineComp.taxableIncome.toLocaleString('en-IN')}</span>
            </div>
          </div>
        </div>

        {/* Modeled Scenario Card */}
        <div className="relative rounded-card border-2 border-accent bg-white p-5 shadow-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-line pb-3 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full bg-accent animate-ping" />
                <h3 className="font-display text-sm font-bold text-ink">{activeScenario.name}</h3>
                <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] font-bold text-accent">
                  Active Scenario
                </span>
              </div>
              <p className="text-[11px] text-muted mt-0.5">{activeScenario.tagline}</p>
            </div>
            <span
              className={[
                'rounded-full px-2.5 py-1 text-xs font-semibold uppercase',
                activeScenario.regime === 'new' ? 'bg-periwinkle-soft text-accent' : 'bg-cream text-ink',
              ].join(' ')}
            >
              {activeScenario.regime} Regime
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="rounded-btn bg-accent/5 border border-accent/20 p-3">
              <span className="text-[11px] text-ink-secondary font-medium">Scenario Tax</span>
              <div className="text-xl font-display font-black text-ink mt-0.5">
                ₹{scenarioEval.computation.totalTax.toLocaleString('en-IN')}
              </div>
              <div className="mt-1 flex items-center gap-1.5">
                <span
                  className={[
                    'rounded-full px-2 py-0.5 text-[11px] font-bold',
                    isSaving
                      ? 'bg-ok/15 text-ok'
                      : isNeutral
                      ? 'bg-cream text-muted'
                      : 'bg-danger/15 text-danger',
                  ].join(' ')}
                >
                  {isSaving && `−₹${Math.abs(taxDelta).toLocaleString('en-IN')} Saving`}
                  {!isSaving && !isNeutral && `+₹${Math.abs(taxDelta).toLocaleString('en-IN')} Increase`}
                  {isNeutral && '±₹0 Neutral'}
                </span>
              </div>
            </div>

            <div className="rounded-btn bg-cream/60 p-3">
              <span className="text-[11px] text-muted font-medium">Annual In-Hand</span>
              <div className="text-xl font-display font-black text-ink mt-0.5">
                ₹{scenarioEval.inHandIncome.toLocaleString('en-IN')}
              </div>
              <div className="mt-1">
                <span
                  className={[
                    'text-[11px] font-bold',
                    scenarioEval.inHandDeltaVsBaseline > 0 ? 'text-ok' : scenarioEval.inHandDeltaVsBaseline < 0 ? 'text-danger' : 'text-muted',
                  ].join(' ')}
                >
                  {scenarioEval.inHandDeltaVsBaseline > 0 ? `+₹${scenarioEval.inHandDeltaVsBaseline.toLocaleString('en-IN')}` : `₹${scenarioEval.inHandDeltaVsBaseline.toLocaleString('en-IN')}`} vs baseline
                </span>
              </div>
            </div>
          </div>

          <div className="text-xs space-y-1.5 pt-2 border-t border-line text-ink-secondary">
            <div className="flex justify-between">
              <span>Gross Total Income:</span>
              <span className="font-semibold text-ink">₹{scenarioEval.computation.grossTotalIncome.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between">
              <span>Total Deductions:</span>
              <span className="font-semibold text-ink">₹{scenarioEval.computation.totalDeductions.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between">
              <span>Effective Tax Rate:</span>
              <span className="font-semibold text-ink">
                {(scenarioEval.computation.effectiveTaxRate * 100).toFixed(1)}%{' '}
                <span className="text-[11px] text-muted">
                  ({(scenarioEval.effectiveRateDeltaVsBaseline * 100).toFixed(1)}% delta)
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Side-by-Side Parameter Controls & Adjustments */}
      <div className="rounded-card border border-line bg-white/85 p-5 shadow-card backdrop-blur-sm space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3">
          <div>
            <h3 className="font-display text-base font-bold text-ink">
              Adjust Scenario Assumptions
            </h3>
            <p className="text-xs text-muted">
              Edit values in real-time. Calculations update deterministically per Section 115BAC &amp; Chapter VI-A.
            </p>
          </div>

          {/* Regime Switcher Button Group */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-ink-secondary">Modeled Regime:</span>
            <div className="flex rounded-btn border border-line p-0.5 bg-cream/70">
              <button
                type="button"
                onClick={() => setActiveScenario((prev) => ({ ...prev, regime: 'new' }))}
                className={[
                  'rounded-[7px] px-3 py-1 text-xs font-semibold transition-colors',
                  activeScenario.regime === 'new'
                    ? 'bg-ink text-white shadow-sm'
                    : 'text-ink-secondary hover:text-ink',
                ].join(' ')}
              >
                New Regime (115BAC)
              </button>
              <button
                type="button"
                onClick={() => setActiveScenario((prev) => ({ ...prev, regime: 'old' }))}
                className={[
                  'rounded-[7px] px-3 py-1 text-xs font-semibold transition-colors',
                  activeScenario.regime === 'old'
                    ? 'bg-ink text-white shadow-sm'
                    : 'text-ink-secondary hover:text-ink',
                ].join(' ')}
              >
                Old Regime
              </button>
            </div>
          </div>
        </div>

        {/* Inputs Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Income Heads Column */}
          <div className="space-y-3.5 rounded-card bg-cream/40 p-4 border border-line/70">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-ink">
                Income Heads (AY {assessmentYear})
              </h4>
              <span className="text-[11px] text-muted">Annual gross figures</span>
            </div>

            <AmountInput
              label="Gross Salary"
              sublabel="Before standard deduction and allowances"
              value={activeScenario.salary}
              onChange={(salary) => setActiveScenario((prev) => ({ ...prev, salary }))}
            />

            <AmountInput
              label="Capital Gains"
              sublabel="STCG (111A) / LTCG (112A) or real estate realization"
              value={activeScenario.capitalGains}
              onChange={(capitalGains) => setActiveScenario((prev) => ({ ...prev, capitalGains }))}
            />

            <AmountInput
              label="House Property Income / (Loss)"
              sublabel="Net rental income received"
              value={activeScenario.houseProperty}
              onChange={(houseProperty) => setActiveScenario((prev) => ({ ...prev, houseProperty }))}
            />

            <AmountInput
              label="Income from Other Sources"
              sublabel="Savings account interest, fixed deposits, dividends"
              value={activeScenario.otherSources}
              onChange={(otherSources) => setActiveScenario((prev) => ({ ...prev, otherSources }))}
            />
          </div>

          {/* Deductions Column */}
          <div className="space-y-3.5 rounded-card bg-cream/40 p-4 border border-line/70">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-ink">
                Deductions &amp; Exemptions
              </h4>
              <span className="text-[11px] font-medium text-accent">
                {activeScenario.regime === 'new'
                  ? 'Standard deduction only under New Regime'
                  : 'Chapter VI-A Deductions Active'}
              </span>
            </div>

            {/* Standard deduction indicator */}
            <div className="rounded-btn border border-periwinkle-soft bg-accent/5 p-3 flex items-center justify-between">
              <div>
                <div className="text-xs font-bold text-ink">Standard Deduction u/s 16(ia)</div>
                <div className="text-[11px] text-muted">
                  {activeScenario.regime === 'new'
                    ? 'Raised to ₹75,000 in Finance Act 2024 (New Regime)'
                    : '₹50,000 eligible on salary income (Old Regime)'}
                </div>
              </div>
              <CitedAmount
                amount={activeScenario.regime === 'new' ? 75_000 : 50_000}
                citation={stdDedCitation}
              />
            </div>

            <AmountInput
              label="Section 80C (PPF, ELSS, EPF, LIC, Tuition)"
              sublabel={activeScenario.regime === 'new' ? 'Not eligible under New Regime' : 'Old regime only — max cap ₹1,50,000'}
              value={activeScenario.section80c}
              max={150_000}
              disabled={activeScenario.regime === 'new'}
              onChange={(section80c) => setActiveScenario((prev) => ({ ...prev, section80c }))}
            />

            <AmountInput
              label="Section 80D (Health Insurance Premium)"
              sublabel={activeScenario.regime === 'new' ? 'Not eligible under New Regime' : 'Self, spouse & dependent children'}
              value={activeScenario.section80d}
              max={25_000}
              disabled={activeScenario.regime === 'new'}
              onChange={(section80d) => setActiveScenario((prev) => ({ ...prev, section80d }))}
            />

            <AmountInput
              label="Section 80CCD(1B) (Additional NPS)"
              sublabel={activeScenario.regime === 'new' ? 'Not eligible under New Regime' : 'Exclusive NPS deduction over and above 80C'}
              value={activeScenario.section80ccd1b}
              max={50_000}
              disabled={activeScenario.regime === 'new'}
              onChange={(section80ccd1b) => setActiveScenario((prev) => ({ ...prev, section80ccd1b }))}
            />

            <AmountInput
              label="Section 24(b) (Home Loan Interest)"
              sublabel={activeScenario.regime === 'new' ? 'Not eligible on self-occupied property in New Regime' : 'Interest on housing loan for self-occupied house'}
              value={activeScenario.section24}
              max={200_000}
              disabled={activeScenario.regime === 'new'}
              onChange={(section24) => setActiveScenario((prev) => ({ ...prev, section24 }))}
            />
          </div>
        </div>

        {/* Pre-paid Taxes Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-line">
          <AmountInput
            label="TDS / TCS Credit Claimed"
            sublabel="Tax deducted at source per Form 26AS / AIS"
            value={activeScenario.tdsCredit}
            onChange={(tdsCredit) => setActiveScenario((prev) => ({ ...prev, tdsCredit }))}
          />
          <AmountInput
            label="Advance Tax Paid"
            sublabel="Quarterly advance tax challans u/s 211"
            value={activeScenario.advanceTaxPaid}
            onChange={(advanceTaxPaid) => setActiveScenario((prev) => ({ ...prev, advanceTaxPaid }))}
          />
        </div>
      </div>

      {/* Side-by-Side Detailed Breakdown Matrix */}
      <div className="rounded-card border border-line bg-white shadow-card overflow-hidden">
        <div className="border-b border-line bg-cream/50 px-5 py-3.5 flex items-center justify-between">
          <div>
            <h3 className="font-display text-sm font-bold text-ink">
              Detailed Line-by-Line Comparison
            </h3>
            <p className="text-[11px] text-muted">
              Full statutory reconciliation between Baseline and {activeScenario.name}
            </p>
          </div>
          <span className="text-xs text-muted font-medium">All figures in INR (₹)</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-line bg-cream/30 text-ink-secondary">
                <th className="py-2.5 px-4 font-semibold">Statutory Line Item</th>
                <th className="py-2.5 px-4 font-semibold text-right">Baseline ({baseline.regime})</th>
                <th className="py-2.5 px-4 font-semibold text-right">Scenario ({activeScenario.regime})</th>
                <th className="py-2.5 px-4 font-semibold text-right">Delta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/60">
              <tr>
                <td className="py-2.5 px-4 font-medium text-ink">Gross Total Income</td>
                <td className="py-2.5 px-4 text-right font-medium text-ink">₹{baselineComp.grossTotalIncome.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right font-medium text-ink">₹{scenarioEval.computation.grossTotalIncome.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right font-semibold">
                  {scenarioEval.computation.grossTotalIncome - baselineComp.grossTotalIncome !== 0 ? (
                    <span className="text-ink">
                      {scenarioEval.computation.grossTotalIncome - baselineComp.grossTotalIncome > 0 ? '+' : ''}
                      ₹{(scenarioEval.computation.grossTotalIncome - baselineComp.grossTotalIncome).toLocaleString('en-IN')}
                    </span>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
              </tr>

              <tr>
                <td className="py-2.5 px-4 font-medium text-ink">Total Deductions (Std Ded + Ch VI-A)</td>
                <td className="py-2.5 px-4 text-right font-medium text-ink">₹{baselineComp.totalDeductions.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right font-medium text-ink">₹{scenarioEval.computation.totalDeductions.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right font-semibold">
                  {scenarioEval.computation.totalDeductions - baselineComp.totalDeductions > 0 ? (
                    <span className="text-ok">+₹{(scenarioEval.computation.totalDeductions - baselineComp.totalDeductions).toLocaleString('en-IN')}</span>
                  ) : scenarioEval.computation.totalDeductions - baselineComp.totalDeductions < 0 ? (
                    <span className="text-danger">−₹{Math.abs(scenarioEval.computation.totalDeductions - baselineComp.totalDeductions).toLocaleString('en-IN')}</span>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
              </tr>

              <tr className="bg-cream/20 font-semibold text-ink">
                <td className="py-2.5 px-4">Net Taxable Income</td>
                <td className="py-2.5 px-4 text-right">₹{baselineComp.taxableIncome.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right">₹{scenarioEval.computation.taxableIncome.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right">
                  {scenarioEval.computation.taxableIncome - baselineComp.taxableIncome !== 0 ? (
                    <span>₹{(scenarioEval.computation.taxableIncome - baselineComp.taxableIncome).toLocaleString('en-IN')}</span>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
              </tr>

              <tr>
                <td className="py-2.5 px-4 text-ink">Tax Computed (Slab Rates)</td>
                <td className="py-2.5 px-4 text-right text-ink">₹{baselineComp.taxBeforeRebate.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right text-ink">₹{scenarioEval.computation.taxBeforeRebate.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right text-muted">—</td>
              </tr>

              <tr>
                <td className="py-2.5 px-4 text-ink">Rebate u/s 87A</td>
                <td className="py-2.5 px-4 text-right text-ok font-medium">
                  {baselineComp.rebate87a > 0 ? `−₹${baselineComp.rebate87a.toLocaleString('en-IN')}` : '₹0'}
                </td>
                <td className="py-2.5 px-4 text-right text-ok font-medium">
                  {scenarioEval.computation.rebate87a > 0 ? `−₹${scenarioEval.computation.rebate87a.toLocaleString('en-IN')}` : '₹0'}
                </td>
                <td className="py-2.5 px-4 text-right text-muted">—</td>
              </tr>

              <tr>
                <td className="py-2.5 px-4 text-ink">Health &amp; Education Cess (4%)</td>
                <td className="py-2.5 px-4 text-right text-ink">₹{baselineComp.cess.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right text-ink">₹{scenarioEval.computation.cess.toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right text-muted">—</td>
              </tr>

              <tr className="bg-cream/40 font-bold text-ink">
                <td className="py-3 px-4 text-sm">Total Tax Liability</td>
                <td className="py-3 px-4 text-right text-sm">₹{baselineComp.totalTax.toLocaleString('en-IN')}</td>
                <td className="py-3 px-4 text-right text-sm">₹{scenarioEval.computation.totalTax.toLocaleString('en-IN')}</td>
                <td className="py-3 px-4 text-right text-sm font-black">
                  {isSaving ? (
                    <span className="text-ok">−₹{Math.abs(taxDelta).toLocaleString('en-IN')} (Saving)</span>
                  ) : !isNeutral ? (
                    <span className="text-danger">+₹{Math.abs(taxDelta).toLocaleString('en-IN')} (Increase)</span>
                  ) : (
                    <span className="text-muted">₹0</span>
                  )}
                </td>
              </tr>

              <tr>
                <td className="py-2.5 px-4 text-ink">TDS / Advance Tax Credits</td>
                <td className="py-2.5 px-4 text-right text-ink">₹{(baseline.tdsCredit + baseline.advanceTaxPaid).toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right text-ink">₹{(activeScenario.tdsCredit + activeScenario.advanceTaxPaid).toLocaleString('en-IN')}</td>
                <td className="py-2.5 px-4 text-right text-muted">—</td>
              </tr>

              <tr className="font-semibold text-ink">
                <td className="py-2.5 px-4">
                  {scenarioEval.computation.netTaxRefundDue < 0 ? 'Refund Claimable' : 'Net Tax Payable'}
                </td>
                <td className="py-2.5 px-4 text-right">
                  ₹{Math.abs(baselineComp.netTaxRefundDue).toLocaleString('en-IN')}
                </td>
                <td className="py-2.5 px-4 text-right">
                  ₹{Math.abs(scenarioEval.computation.netTaxRefundDue).toLocaleString('en-IN')}
                </td>
                <td className="py-2.5 px-4 text-right">
                  {isSaving ? (
                    <span className="text-ok font-bold">−₹{Math.abs(taxDelta).toLocaleString('en-IN')}</span>
                  ) : !isNeutral ? (
                    <span className="text-danger font-bold">+₹{Math.abs(taxDelta).toLocaleString('en-IN')}</span>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Strategic Synthesis & AI Call to Action */}
      <div className="rounded-card border border-periwinkle-soft bg-white p-5 shadow-card space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-accent font-bold">✦</span>
            <h4 className="font-display text-sm font-bold text-ink">
              Strategic Takeaways &amp; Breakeven Analysis
            </h4>
          </div>
          <CitedAmount
            amount={scenarioEval.comparison.taxSaving}
            citation={regimeCitation}
          />
        </div>

        <p className="text-xs text-ink-secondary leading-relaxed">
          {scenarioEval.comparison.summary} For gross salary of ₹{scenarioEval.computation.grossTotalIncome.toLocaleString('en-IN')}, 
          the Old Regime requires substantial deductions (Standard Deduction + 80C + 80D + Section 24 exceeding the breakeven threshold of ₹3,75,000) 
          to outperform the New Regime&rsquo;s lowered slab structure and ₹75,000 standard deduction under Finance Act 2024.
        </p>

        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-line/60">
          <div className="flex items-center gap-2 text-[11px] text-muted">
            <span>Deterministic engine</span>
            <span>&middot;</span>
            <span>Regime-aware</span>
            <span>&middot;</span>
            <span>Citations attached</span>
          </div>

          <Link
            href={`/chat?q=${encodeURIComponent(
              `Analyze this tax scenario for AY ${assessmentYear}: comparing baseline (${baseline.regime} regime, tax ₹${baselineComp.totalTax}) against scenario (${activeScenario.regime} regime, tax ₹${scenarioEval.computation.totalTax}). What are the key planning opportunities?`
            )}`}
            className="flex items-center gap-1.5 rounded-btn border border-periwinkle-soft bg-accent/5 px-3 py-1.5 text-xs font-semibold text-accent hover:bg-accent hover:text-white transition-all shadow-sm"
          >
            <span>Ask Verra about this Scenario</span>
            <span>→</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
