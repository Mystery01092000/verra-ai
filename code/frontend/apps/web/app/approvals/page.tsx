'use client';

import { useCallback, useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { ApprovalCard } from './ApprovalCard';
import { normalizeRun, type ApprovalRun } from './approvals-types';

type LoadState = 'loading' | 'ready' | 'error';

interface DecisionEnvelope {
  success: boolean;
  data: Record<string, unknown> | null;
  error: string | null;
}

export default function ApprovalsPage() {
  const { data: session } = useSession();
  const [runs, setRuns] = useState<ApprovalRun[]>([]);
  const [state, setState] = useState<LoadState>('loading');
  const [approver, setApprover] = useState('');
  const [approverTouched, setApproverTouched] = useState(false);
  const [decided, setDecided] = useState<Array<{ runId: string; action: string }>>([]);

  // Prefill from the signed-in session once, unless the reviewer typed a name.
  useEffect(() => {
    const sessionName = session?.user?.name ?? session?.user?.email ?? '';
    if (!approverTouched && approver === '' && sessionName !== '') {
      setApprover(sessionName);
    }
  }, [session, approver, approverTouched]);

  const load = useCallback(async () => {
    setState('loading');
    try {
      const res = await fetch('/api/approvals');
      const envelope = (await res.json()) as { success: boolean; data: { runs: unknown[] } | null };
      if (!res.ok || !envelope.success || envelope.data === null) {
        setState('error');
        return;
      }
      setRuns(envelope.data.runs.map(normalizeRun));
      setState('ready');
    } catch {
      setState('error');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function decide(
    run: ApprovalRun,
    action: 'approve' | 'reject',
    note?: string,
  ): Promise<string | null> {
    try {
      const res = await fetch('/api/approvals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ runId: run.runId, action, approver: approver.trim(), note }),
      });
      const envelope = (await res.json()) as DecisionEnvelope;
      if (!res.ok || !envelope.success) {
        return res.status === 502
          ? 'Backend unreachable — the decision was NOT recorded. Try again.'
          : (envelope.error ?? 'The decision could not be recorded.');
      }
      setRuns((prev) => prev.filter((r) => r.runId !== run.runId));
      setDecided((prev) => [{ runId: run.runId, action }, ...prev].slice(0, 5));
      return null;
    } catch {
      return 'Backend unreachable — the decision was NOT recorded. Try again.';
    }
  }

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-line bg-white/60 px-6 py-4 backdrop-blur-sm">
        <h1 className="font-display text-lg font-black tracking-tight text-ink">Approvals</h1>
        <p className="text-xs text-muted">
          Human-in-the-loop gate &mdash; a licensed professional must review and approve before
          anything is filed or sent
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl space-y-4">
          <div className="rounded-card border border-periwinkle-soft bg-white p-4 shadow-card">
            <label
              htmlFor="approver-name"
              className="block text-xs font-semibold text-ink-secondary"
            >
              Reviewing as
            </label>
            <input
              id="approver-name"
              type="text"
              value={approver}
              onChange={(e) => {
                setApproverTouched(true);
                setApprover(e.target.value);
              }}
              placeholder="Your full name (licensed reviewer)"
              className="mt-1 w-full rounded-btn border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:shadow-glow"
            />
            <p className="mt-1 text-[11px] text-muted">
              Every decision is written to the immutable audit log with your name attached.
            </p>
          </div>

          {decided.map(({ runId, action }) => (
            <p
              key={runId}
              role="status"
              className={[
                'rounded-btn px-3 py-2 text-xs',
                action === 'approve' ? 'bg-ok/10 text-ok' : 'bg-danger/10 text-danger',
              ].join(' ')}
            >
              Run {runId} {action === 'approve' ? 'approved' : 'rejected'} &middot; audit receipt
              recorded.
            </p>
          ))}

          {state === 'loading' && (
            <div role="status" className="rounded-card bg-white/70 p-6 text-center shadow-card">
              <p className="text-sm text-muted">Loading runs awaiting approval&hellip;</p>
            </div>
          )}

          {state === 'error' && (
            <div className="rounded-card bg-white/70 p-8 text-center shadow-card">
              <p className="text-sm font-medium text-ink-secondary">Backend unreachable</p>
              <p className="mt-1 text-xs text-muted">
                The orchestrator could not be contacted, so the approval queue cannot be shown.
              </p>
              <button
                type="button"
                onClick={() => void load()}
                className="mt-4 rounded-btn border border-line px-4 py-2 text-sm font-medium text-ink-secondary transition-colors hover:border-accent hover:text-accent"
              >
                Retry
              </button>
            </div>
          )}

          {state === 'ready' && runs.length === 0 && (
            <div className="rounded-card bg-white/70 p-8 text-center shadow-card">
              <p className="text-sm font-medium text-ink-secondary">Nothing awaiting approval</p>
              <p className="mt-1 text-xs text-muted">
                When an AI-prepared analysis needs sign-off, it will appear here. Nothing is filed
                or sent without a human decision.
              </p>
            </div>
          )}

          {state === 'ready' &&
            runs.map((run) => (
              <ApprovalCard key={run.runId} run={run} approver={approver} onDecide={decide} />
            ))}
        </div>
      </div>
    </div>
  );
}
