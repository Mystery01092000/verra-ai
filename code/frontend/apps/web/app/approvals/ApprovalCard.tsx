'use client';

import { useState } from 'react';
import { formatCreatedAt, type ApprovalRun } from './approvals-types';

export interface ApprovalCardProps {
  run: ApprovalRun;
  approver: string;
  onDecide: (
    run: ApprovalRun,
    action: 'approve' | 'reject',
    note?: string,
  ) => Promise<string | null>;
}

export function ApprovalCard({ run, approver, onDecide }: ApprovalCardProps) {
  const [note, setNote] = useState('');
  const [pending, setPending] = useState<'approve' | 'reject' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const approverMissing = approver.trim().length === 0;

  async function decide(action: 'approve' | 'reject') {
    setPending(action);
    setError(null);
    const failure = await onDecide(run, action, note.trim() || undefined);
    if (failure !== null) {
      setError(failure);
      setPending(null);
    }
  }

  return (
    <div className="rounded-card border border-periwinkle-soft bg-white p-4 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-periwinkle-soft px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-accent-700">
              {run.capability.replace(/_/g, ' ')}
            </span>
            <span className="rounded-full bg-warn/10 px-2 py-0.5 text-[10px] font-semibold text-warn">
              Awaiting approval
            </span>
          </div>
          <p className="mt-1.5 text-xs text-muted">
            Run {run.runId} &middot; created {formatCreatedAt(run.createdAt)}
          </p>
        </div>
      </div>

      {run.summary && <p className="mt-3 text-sm text-ink-secondary">{run.summary}</p>}

      {run.citations.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {run.citations.map((label) => (
            <span
              key={label}
              className="rounded-full bg-cream px-2 py-0.5 text-[10px] text-ink-secondary"
            >
              {label}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4 flex flex-col gap-2 border-t border-line pt-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          type="text"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Optional note for the audit log"
          aria-label={`Note for run ${run.runId}`}
          className="min-w-0 flex-1 rounded-btn border border-line bg-white px-3 py-2 text-xs text-ink outline-none focus:shadow-glow"
        />
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            disabled={pending !== null || approverMissing}
            onClick={() => void decide('reject')}
            className="rounded-btn border border-line px-4 py-2 text-sm font-medium text-ink-secondary transition-colors hover:border-danger hover:text-danger disabled:cursor-not-allowed disabled:opacity-50"
          >
            {pending === 'reject' ? 'Rejecting…' : 'Reject'}
          </button>
          <button
            type="button"
            disabled={pending !== null || approverMissing}
            onClick={() => void decide('approve')}
            className="rounded-btn px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-85 disabled:cursor-not-allowed disabled:opacity-50"
            style={{ background: 'var(--gradient-brand)' }}
          >
            {pending === 'approve' ? 'Approving…' : 'Approve'}
          </button>
        </div>
      </div>

      {approverMissing && (
        <p className="mt-2 text-[11px] text-muted">
          Enter your name above the list — decisions must be attributable to a licensed reviewer.
        </p>
      )}
      {error && (
        <p role="alert" className="mt-2 rounded-btn bg-danger/10 px-3 py-2 text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
