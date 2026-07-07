'use client';
import { useCallback, useEffect, useState } from 'react';
import type { ConsolidationReport, Holding } from './holdings-shared';
import { addHolding, deleteHolding, fetchConsolidation, fetchHoldings } from './holdings-api';
import { ConsolidationDashboard } from './ConsolidationDashboard';
import { AddHoldingForm } from './AddHoldingForm';
import { HoldingsList } from './HoldingsList';
import { AnalysisPanel } from './AnalysisPanel';

interface ListState {
  holdings: Holding[];
  loading: boolean;
  error: string | null;
}

interface ConsolidationState {
  report: ConsolidationReport | null;
  loading: boolean;
  error: string | null;
}

export function HoldingsView() {
  const [list, setList] = useState<ListState>({ holdings: [], loading: true, error: null });
  const [consolidation, setConsolidation] = useState<ConsolidationState>({
    report: null,
    loading: true,
    error: null,
  });
  const [annualIncome, setAnnualIncome] = useState<number | undefined>(undefined);

  const loadHoldings = useCallback(async () => {
    setList((prev) => ({ ...prev, loading: true, error: null }));
    const result = await fetchHoldings();
    if (result.ok) {
      setList({ holdings: result.data.holdings, loading: false, error: null });
    } else {
      setList({ holdings: [], loading: false, error: result.error });
    }
  }, []);

  const loadConsolidation = useCallback(async (income: number | undefined) => {
    setConsolidation((prev) => ({ ...prev, loading: true, error: null }));
    const result = await fetchConsolidation(income);
    if (result.ok) {
      setConsolidation({ report: result.data, loading: false, error: null });
    } else {
      setConsolidation({ report: null, loading: false, error: result.error });
    }
  }, []);

  const refreshAll = useCallback(() => {
    void loadHoldings();
    void loadConsolidation(annualIncome);
  }, [loadHoldings, loadConsolidation, annualIncome]);

  useEffect(() => {
    void loadHoldings();
  }, [loadHoldings]);

  useEffect(() => {
    void loadConsolidation(annualIncome);
  }, [loadConsolidation, annualIncome]);

  async function handleAdd(payload: Record<string, unknown>): Promise<string | null> {
    const result = await addHolding(payload);
    if (!result.ok) return result.error;
    refreshAll();
    return null;
  }

  async function handleDelete(id: string): Promise<string | null> {
    const result = await deleteHolding(id);
    if (!result.ok) return result.error;
    refreshAll();
    return null;
  }

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-line bg-white/60 px-6 py-4 backdrop-blur-sm">
        <h1 className="font-display text-lg font-black tracking-tight text-ink">Holdings</h1>
        <p className="text-xs text-muted">
          Investments, deposits, insurance &amp; loans — consolidated into one net-worth view
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-5xl space-y-6">
          {/* Zone A — consolidation dashboard */}
          <ConsolidationDashboard
            report={consolidation.report}
            holdings={list.holdings}
            loading={consolidation.loading}
            error={consolidation.error}
            annualIncome={annualIncome}
            onAnnualIncomeChange={setAnnualIncome}
            onRetry={() => void loadConsolidation(annualIncome)}
          />

          <AnalysisPanel annualIncome={annualIncome} hasHoldings={list.holdings.length > 0} />

          {/* Zone B — holdings manager */}
          <section
            aria-label="Manage holdings"
            className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,4fr)]"
          >
            <AddHoldingForm onAdd={handleAdd} />
            <div>
              <h3 className="mb-3 text-sm font-semibold text-ink-secondary">Your holdings</h3>
              {list.error ? (
                <div className="rounded-card border border-line bg-white p-6 text-center shadow-card">
                  <p className="text-sm font-medium text-ink">Holdings unavailable</p>
                  <p className="mx-auto mt-1 max-w-sm text-xs text-muted">{list.error}</p>
                  <button
                    type="button"
                    onClick={() => void loadHoldings()}
                    className="mt-3 rounded-btn bg-ink px-4 py-2 text-xs font-medium text-white transition-opacity hover:opacity-85"
                  >
                    Retry
                  </button>
                </div>
              ) : list.loading ? (
                <div
                  className="rounded-card border border-line bg-white p-6 text-center shadow-card"
                  role="status"
                  aria-busy="true"
                >
                  <p className="text-sm text-muted">Loading holdings…</p>
                </div>
              ) : (
                <HoldingsList holdings={list.holdings} onDelete={handleDelete} />
              )}
            </div>
          </section>

          <p className="pb-2 text-center text-xs text-muted">
            Verra consolidates what you enter; it never fabricates balances. AI insights are drafts
            for review by a licensed professional.
          </p>
        </div>
      </div>
    </div>
  );
}
