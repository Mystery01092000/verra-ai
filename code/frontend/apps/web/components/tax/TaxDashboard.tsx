'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { KpiTile } from './KpiTile';
import { IncomeBreakdown } from './IncomeBreakdown';
import { AssumptionsEditor } from './AssumptionsEditor';
import { ComputationCard } from './ComputationCard';
import { RegimeComparisonCard } from './RegimeComparisonCard';
import {
  ASSUMPTION_CITATION,
  SAMPLE_ASSUMPTIONS,
  SAMPLE_DATA,
  normalizeComparison,
  normalizeComputation,
  ruleCitation,
  type TaxAssumptions,
  type TaxDashboardData,
} from './tax-data';

export interface TaxDashboardProps {
  assessmentYear: string;
}

type Source = 'loading' | 'live' | 'sample';

const DEBOUNCE_MS = 400;

interface ComputeEnvelope {
  success: boolean;
  data: { liability: Record<string, unknown>; comparison: Record<string, unknown> | null } | null;
  error: string | null;
}

function SourceBadge({ source, onRetry }: { source: Source; onRetry: () => void }) {
  if (source === 'loading') {
    return (
      <span
        role="status"
        className="rounded-full bg-cream px-3 py-1 text-xs font-semibold text-muted"
      >
        Computing&hellip;
      </span>
    );
  }
  if (source === 'live') {
    return (
      <span className="rounded-full bg-ok/10 px-3 py-1 text-xs font-semibold text-ok">
        Live calculator &middot; cited
      </span>
    );
  }
  return (
    <span className="flex items-center gap-2">
      <span
        role="status"
        className="rounded-full bg-warn/10 px-3 py-1 text-xs font-semibold text-warn"
      >
        Sample data &mdash; backend offline
      </span>
      <button
        type="button"
        onClick={onRetry}
        className="rounded-btn border border-line px-3 py-1 text-xs font-medium text-ink-secondary transition-colors hover:border-accent hover:text-accent"
      >
        Retry
      </button>
    </span>
  );
}

export function TaxDashboard({ assessmentYear }: TaxDashboardProps) {
  const [assumptions, setAssumptions] = useState<TaxAssumptions>(SAMPLE_ASSUMPTIONS);
  const [data, setData] = useState<TaxDashboardData | null>(null);
  const [source, setSource] = useState<Source>('loading');
  const [inputError, setInputError] = useState<string | null>(null);
  const requestSeq = useRef(0);

  const compute = useCallback(
    async (current: TaxAssumptions) => {
      const seq = ++requestSeq.current;
      try {
        const res = await fetch('/api/tax/compute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ assessmentYear, ...current }),
        });
        if (seq !== requestSeq.current) return; // stale response
        const envelope = (await res.json()) as ComputeEnvelope;
        if (res.status === 400) {
          setInputError(envelope.error ?? 'Invalid assumptions');
          return;
        }
        if (!res.ok || !envelope.success || envelope.data === null) {
          setData(SAMPLE_DATA);
          setSource('sample');
          setInputError(null);
          return;
        }
        setData({
          liability: normalizeComputation(envelope.data.liability),
          comparison: normalizeComparison(envelope.data.comparison),
        });
        setSource('live');
        setInputError(null);
      } catch {
        if (seq !== requestSeq.current) return;
        setData(SAMPLE_DATA);
        setSource('sample');
        setInputError(null);
      }
    },
    [assessmentYear],
  );

  useEffect(() => {
    const timer = setTimeout(() => void compute(assumptions), DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [assumptions, compute]);

  const shown = data ?? SAMPLE_DATA;
  const isSample = source === 'sample';
  const liability = shown.liability;
  const citations = liability.citations;
  const refundDue = liability.netTaxRefundDue < 0;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl font-black tracking-tight text-ink">
            Tax Workspace
          </h2>
          <p className="text-sm text-ink-secondary">Assessment Year {assessmentYear} · India</p>
        </div>
        <SourceBadge source={source} onRetry={() => void compute(assumptions)} />
      </div>

      <AssumptionsEditor
        value={isSample ? SAMPLE_ASSUMPTIONS : assumptions}
        onChange={(next) => {
          setAssumptions(next);
          if (source !== 'loading') setSource('loading');
        }}
        disabled={isSample}
      />
      {isSample && (
        <p className="text-xs text-muted">
          Assumptions are locked to the sample profile while the backend is offline. Retry to resume
          live, editable computation.
        </p>
      )}
      {inputError && (
        <p role="alert" className="rounded-btn bg-danger/10 px-3 py-2 text-xs text-danger">
          {inputError}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiTile
          title="Taxable Income"
          amount={liability.taxableIncome}
          caption="After deductions"
          citation={ruleCitation(citations, '16(ia)')}
        />
        <KpiTile
          title="Total Tax"
          amount={liability.totalTax}
          caption={`${liability.regime === 'new' ? 'New' : 'Old'} regime, incl. cess`}
          citation={ruleCitation(citations, 'cess')}
          tone="negative"
        />
        <KpiTile
          title="Rebate u/s 87A"
          amount={liability.rebate87a}
          citation={ruleCitation(citations, 'rebate_87a')}
          tone="positive"
        />
        <KpiTile
          title={refundDue ? 'Refund Due' : 'Net Payable'}
          amount={Math.abs(liability.netTaxRefundDue)}
          caption="After TDS & credits"
          citation={ruleCitation(citations, 'slabs')}
          tone={refundDue ? 'positive' : 'negative'}
        />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <IncomeBreakdown
          rows={[
            {
              head: 'salary',
              amount: liability.grossTotalIncome,
              citation: ASSUMPTION_CITATION,
            },
          ]}
          total={liability.grossTotalIncome}
        />
        <ComputationCard computation={liability} />
      </div>

      {shown.comparison && <RegimeComparisonCard comparison={shown.comparison} />}

      <p className="text-xs text-muted">
        Figures are computed by Verra&rsquo;s deterministic tax calculators with rule citations
        &mdash; hover any amount to see its source. A licensed professional must review and approve
        before anything is filed.
      </p>
    </div>
  );
}
