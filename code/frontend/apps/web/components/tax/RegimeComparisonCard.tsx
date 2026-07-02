'use client';

import { CitedAmount } from './CitedAmount';
import { ruleCitation, type RegimeComparisonView, type TaxComputation } from './tax-data';

interface RegimePanelProps {
  title: string;
  computation: TaxComputation;
  recommended: boolean;
}

function RegimePanel({ title, computation, recommended }: RegimePanelProps) {
  return (
    <div
      className={[
        'flex-1 rounded-[12px] border p-3',
        recommended ? 'border-accent bg-periwinkle-soft/40' : 'border-line bg-cream',
      ].join(' ')}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-ink-secondary">
          {title}
        </span>
        {recommended && (
          <span className="rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold text-white">
            Recommended
          </span>
        )}
      </div>
      <div className="mt-1 font-display text-xl font-black text-ink">
        <CitedAmount
          amount={computation.totalTax}
          citation={ruleCitation(computation.citations, 'slabs')}
        />
      </div>
      <p className="mt-0.5 text-[11px] text-muted">
        Effective rate {(computation.effectiveTaxRate * 100).toFixed(1)}%
      </p>
    </div>
  );
}

export interface RegimeComparisonCardProps {
  comparison: RegimeComparisonView;
}

export function RegimeComparisonCard({ comparison }: RegimeComparisonCardProps) {
  const regimeChoice = ruleCitation(comparison.citations, 'regime_choice');

  return (
    <div className="rounded-card border border-periwinkle-soft bg-white p-4 shadow-card">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-ink">Old vs New Regime</h3>
        <span className="text-xs text-muted">Section 115BAC</span>
      </div>

      <div className="mt-3 flex flex-col gap-3 sm:flex-row">
        <RegimePanel
          title="Old regime"
          computation={comparison.oldRegime}
          recommended={comparison.recommendedRegime === 'old'}
        />
        <RegimePanel
          title="New regime"
          computation={comparison.newRegime}
          recommended={comparison.recommendedRegime === 'new'}
        />
      </div>

      <p className="mt-3 text-sm text-ink-secondary">
        {comparison.summary || 'Comparison computed by the deterministic regime calculator.'}
      </p>
      <p className="mt-1 flex items-center gap-1 text-sm font-medium text-ink">
        Estimated saving with the recommended regime:{' '}
        <CitedAmount amount={comparison.taxSaving} citation={regimeChoice} />
      </p>
    </div>
  );
}
