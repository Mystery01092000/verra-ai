'use client';
import { useState } from 'react';
import type { ConsolidationFlag, ConsolidationReport, Holding } from './holdings-shared';
import { formatMoney, formatPercent, isInsuranceType } from './holding-fields';

interface ConsolidationDashboardProps {
  report: ConsolidationReport | null;
  holdings: Holding[];
  loading: boolean;
  error: string | null;
  annualIncome: number | undefined;
  onAnnualIncomeChange: (income: number | undefined) => void;
  onRetry: () => void;
}

const WARN_FLAG_TYPES = new Set([
  'concentration',
  'underinsured',
  'under_insured',
  'high-debt',
  'high_debt',
  'warn',
  'warning',
]);

function isWarnFlag(flag: ConsolidationFlag): boolean {
  const type = flag.type.toLowerCase();
  return WARN_FLAG_TYPES.has(type) || [...WARN_FLAG_TYPES].some((t) => type.includes(t));
}

function FlagCard({ flag }: { flag: ConsolidationFlag }) {
  const warn = isWarnFlag(flag);
  return (
    <div
      className="rounded-2xl border p-4"
      style={{
        borderColor: warn ? 'var(--color-warn)' : 'var(--color-line)',
        background: warn
          ? 'color-mix(in srgb, var(--color-warn) 8%, transparent)'
          : 'var(--color-surface)',
      }}
    >
      <p className="text-[11px] font-semibold uppercase tracking-widest text-muted">
        {flag.type.replace(/[_-]/g, ' ')}
      </p>
      <p className="mt-1 text-sm leading-relaxed text-ink">{flag.message}</p>
      {flag.citation && (
        <p className="mt-2 text-[11px] font-medium text-accent">
          <span aria-hidden="true">§ </span>
          {flag.citation}
        </p>
      )}
    </div>
  );
}

function AllocationBar({
  category,
  amount,
  percentage,
}: {
  category: string;
  amount: number;
  percentage: number;
}) {
  const width = Math.max(0, Math.min(100, percentage));
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3 text-sm">
        <span className="font-medium capitalize text-ink">{category.replace(/_/g, ' ')}</span>
        <span className="shrink-0 text-ink-secondary">
          {formatMoney(amount)}
          <span className="ml-2 text-xs text-muted">{formatPercent(percentage)}</span>
        </span>
      </div>
      <div
        className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-cream"
        role="progressbar"
        aria-valuenow={Math.round(width)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${category}: ${formatPercent(percentage)} of assets`}
      >
        <div
          className="h-full rounded-full"
          style={{ width: `${width}%`, background: 'var(--gradient-brand)' }}
        />
      </div>
    </div>
  );
}

function InsuranceSummary({ holdings }: { holdings: Holding[] }) {
  const insurance = holdings.filter((h) => isInsuranceType(h.type));
  const lifeCover = insurance
    .filter((h) => h.type === 'insurance_life' || h.type === 'insurance_ulip')
    .reduce((sum, h) => sum + (h.sumAssured ?? 0), 0);
  const healthCover = insurance
    .filter((h) => h.type === 'insurance_health')
    .reduce((sum, h) => sum + (h.sumAssured ?? 0), 0);
  const annualPremium = insurance.reduce((sum, h) => sum + (h.premiumAnnual ?? 0), 0);

  return (
    <div className="rounded-card border border-line bg-white p-5 shadow-card">
      <h3 className="text-sm font-semibold text-ink">Insurance cover</h3>
      {insurance.length === 0 ? (
        <p className="mt-2 text-sm text-muted">No insurance policies added yet.</p>
      ) : (
        <dl className="mt-3 space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-ink-secondary">Life cover (sum assured)</dt>
            <dd className="font-semibold text-ink">{formatMoney(lifeCover)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-ink-secondary">Health cover (sum assured)</dt>
            <dd className="font-semibold text-ink">{formatMoney(healthCover)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-ink-secondary">Total annual premium</dt>
            <dd className="font-semibold text-ink">{formatMoney(annualPremium)}</dd>
          </div>
        </dl>
      )}
      <p className="mt-3 text-[11px] text-muted">
        Computed from the sum assured you entered for each policy.
      </p>
    </div>
  );
}

export function ConsolidationDashboard({
  report,
  holdings,
  loading,
  error,
  annualIncome,
  onAnnualIncomeChange,
  onRetry,
}: ConsolidationDashboardProps) {
  const [incomeDraft, setIncomeDraft] = useState(
    annualIncome !== undefined ? String(annualIncome) : '',
  );

  function applyIncome() {
    const trimmed = incomeDraft.trim();
    if (trimmed === '') {
      onAnnualIncomeChange(undefined);
      return;
    }
    const parsed = Number(trimmed);
    if (Number.isFinite(parsed) && parsed >= 0) {
      onAnnualIncomeChange(parsed);
    }
  }

  if (error) {
    return (
      <section
        aria-label="Consolidation"
        className="rounded-card border border-line bg-white p-8 text-center shadow-card"
      >
        <h2 className="font-display text-lg font-black text-ink">Consolidation unavailable</h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted">{error}</p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-btn bg-ink px-5 py-2 text-sm font-medium text-white transition-opacity hover:opacity-85"
        >
          Retry
        </button>
      </section>
    );
  }

  if (loading && report === null) {
    return (
      <section
        aria-label="Consolidation"
        aria-busy="true"
        className="rounded-card border border-line bg-white p-8 shadow-card"
      >
        <p className="text-sm text-muted">Consolidating your holdings…</p>
      </section>
    );
  }

  if (report === null) return null;

  return (
    <section aria-label="Consolidation" className="space-y-4">
      {/* Net worth hero */}
      <div className="rounded-card-lg border border-line bg-white p-6 shadow-card">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-widest text-muted">
              Net worth
            </p>
            <p className="mt-1 font-display text-[40px] font-black leading-none tracking-tight text-ink">
              {formatMoney(report.netWorth)}
            </p>
            <div className="mt-4 flex gap-8 text-sm">
              <div>
                <p className="text-muted">Assets</p>
                <p className="font-semibold" style={{ color: 'var(--color-ok)' }}>
                  {formatMoney(report.totalAssets)}
                </p>
              </div>
              <div>
                <p className="text-muted">Liabilities</p>
                <p className="font-semibold" style={{ color: 'var(--color-danger)' }}>
                  {formatMoney(report.totalLiabilities)}
                </p>
              </div>
            </div>
          </div>

          <div className="w-full max-w-[220px]">
            <label
              htmlFor="annual-income"
              className="text-[11px] font-semibold uppercase tracking-widest text-muted"
            >
              Annual income (optional)
            </label>
            <div className="mt-1.5 flex gap-2">
              <input
                id="annual-income"
                type="number"
                min={0}
                inputMode="numeric"
                value={incomeDraft}
                onChange={(e) => setIncomeDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') applyIncome();
                }}
                placeholder="e.g. 2400000"
                className="w-full rounded-btn border border-line bg-white px-3 py-2 text-sm text-ink placeholder:text-muted focus:border-accent focus:outline-none"
              />
              <button
                type="button"
                onClick={applyIncome}
                className="shrink-0 rounded-btn border border-line px-3 py-2 text-sm font-medium text-ink-secondary transition-colors hover:border-accent hover:text-accent"
              >
                Apply
              </button>
            </div>
            <p className="mt-1.5 text-[11px] text-muted">
              Used for adequacy checks (insurance, debt load).
            </p>
          </div>
        </div>

        <p className="mt-5 border-t border-line pt-3 text-[11px] text-muted">
          Computed by Verra&apos;s deterministic consolidation engine from your {holdings.length}{' '}
          holding{holdings.length === 1 ? '' : 's'} — not an AI estimate.
          {report.citations.length > 0 && (
            <span className="mt-1 block text-accent">Sources: {report.citations.join(' · ')}</span>
          )}
        </p>
      </div>

      {/* Allocation + insurance */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-card border border-line bg-white p-5 shadow-card">
          <h3 className="text-sm font-semibold text-ink">Asset allocation</h3>
          {report.breakdown.length === 0 ? (
            <p className="mt-2 text-sm text-muted">
              Add holdings to see your allocation across categories.
            </p>
          ) : (
            <div className="mt-4 space-y-4">
              {report.breakdown.map((item) => (
                <AllocationBar key={item.category} {...item} />
              ))}
            </div>
          )}
        </div>
        <InsuranceSummary holdings={holdings} />
      </div>

      {/* Advisory flags */}
      {report.flags.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-ink-secondary">Advisory flags</h3>
          <div className="grid gap-3 md:grid-cols-2">
            {report.flags.map((flag, i) => (
              <FlagCard key={`${flag.type}-${i}`} flag={flag} />
            ))}
          </div>
          <p className="text-[11px] text-muted">
            Flags are rule-based observations, not advice. Review them with a licensed adviser or CA
            before acting.
          </p>
        </div>
      )}
    </section>
  );
}
