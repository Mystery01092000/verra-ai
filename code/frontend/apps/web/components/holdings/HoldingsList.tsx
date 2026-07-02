'use client';
import { useState } from 'react';
import type { Holding } from './holdings-shared';
import {
  CATEGORY_ORDER,
  categoryForType,
  formatMoney,
  isInsuranceType,
  isLoanType,
  typeLabel,
} from './holding-fields';

interface HoldingsListProps {
  holdings: Holding[];
  onDelete: (id: string) => Promise<string | null>;
}

function primaryAmount(holding: Holding): { label: string; value: number } {
  if (isLoanType(holding.type)) {
    return { label: 'Outstanding', value: holding.outstandingAmount ?? 0 };
  }
  if (isInsuranceType(holding.type)) {
    return { label: 'Sum assured', value: holding.sumAssured ?? holding.currentValue };
  }
  return { label: 'Current value', value: holding.currentValue };
}

function secondaryLine(holding: Holding): string {
  const parts: string[] = [typeLabel(holding.type)];
  if (holding.institution) parts.push(holding.institution);
  if (isLoanType(holding.type) && holding.emi) {
    parts.push(`EMI ${formatMoney(holding.emi, holding.currency)}/mo`);
  }
  if (isInsuranceType(holding.type) && holding.premiumAnnual) {
    parts.push(`Premium ${formatMoney(holding.premiumAnnual, holding.currency)}/yr`);
  }
  if (holding.interestRate) parts.push(`${holding.interestRate}%`);
  return parts.join(' · ');
}

function HoldingRow({
  holding,
  onDelete,
}: {
  holding: Holding;
  onDelete: HoldingsListProps['onDelete'];
}) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const amount = primaryAmount(holding);
  const loan = isLoanType(holding.type);

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    const deleteError = await onDelete(holding.id);
    setDeleting(false);
    setConfirming(false);
    if (deleteError) setError(deleteError);
  }

  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-line px-4 py-3 last:border-b-0">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-ink">{holding.name}</p>
        <p className="truncate text-xs text-muted">{secondaryLine(holding)}</p>
        {error && (
          <p role="alert" className="mt-1 text-xs" style={{ color: 'var(--color-danger)' }}>
            {error}
          </p>
        )}
      </div>
      <div className="text-right">
        <p
          className="text-sm font-semibold"
          style={{ color: loan ? 'var(--color-danger)' : 'var(--color-ink)' }}
        >
          {loan ? '−' : ''}
          {formatMoney(amount.value, holding.currency)}
        </p>
        <p className="text-[10px] text-muted">{amount.label} · as entered</p>
      </div>
      <div className="flex items-center gap-2">
        {confirming ? (
          <>
            <button
              type="button"
              onClick={() => void handleDelete()}
              disabled={deleting}
              className="rounded-btn px-2.5 py-1 text-xs font-semibold text-white disabled:opacity-50"
              style={{ background: 'var(--color-danger)' }}
            >
              {deleting ? 'Removing…' : 'Confirm'}
            </button>
            <button
              type="button"
              onClick={() => setConfirming(false)}
              disabled={deleting}
              className="rounded-btn border border-line px-2.5 py-1 text-xs text-ink-secondary"
            >
              Cancel
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            aria-label={`Delete ${holding.name}`}
            className="rounded-btn px-2.5 py-1 text-xs text-muted transition-colors hover:bg-cream hover:text-ink"
          >
            Delete
          </button>
        )}
      </div>
    </li>
  );
}

export function HoldingsList({ holdings, onDelete }: HoldingsListProps) {
  if (holdings.length === 0) {
    return (
      <div className="rounded-card border border-dashed border-line bg-white p-6 text-center">
        <p className="text-sm font-medium text-ink">No holdings yet</p>
        <p className="mt-1 text-xs text-muted">
          Add your investments, deposits, insurance and loans to see a consolidated picture.
        </p>
      </div>
    );
  }

  const grouped = new Map<string, Holding[]>();
  for (const holding of holdings) {
    const category = categoryForType(holding.type);
    grouped.set(category, [...(grouped.get(category) ?? []), holding]);
  }
  const categories = [
    ...CATEGORY_ORDER.filter((c) => grouped.has(c)),
    ...[...grouped.keys()].filter((c) => !CATEGORY_ORDER.includes(c)),
  ];

  return (
    <div className="space-y-4">
      {categories.map((category) => {
        const items = grouped.get(category) ?? [];
        return (
          <section key={category} aria-label={category}>
            <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-muted">
              {category}
            </h4>
            <ul className="overflow-hidden rounded-card border border-line bg-white shadow-card">
              {items.map((holding) => (
                <HoldingRow key={holding.id} holding={holding} onDelete={onDelete} />
              ))}
            </ul>
          </section>
        );
      })}
      <p className="text-[11px] text-muted">
        Values shown are as you entered them — Verra does not fetch live market prices yet.
      </p>
    </div>
  );
}
