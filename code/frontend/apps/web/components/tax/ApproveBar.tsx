'use client';
import { useState } from 'react';

type ApprovalStatus = 'idle' | 'approved' | 'rejected';

interface Props {
  year: string;
}

export function ApproveBar({ year }: Props) {
  const [status, setStatus] = useState<ApprovalStatus>('idle');

  if (status === 'approved') {
    return (
      <div className="border-t border-line bg-ok/10 px-6 py-3">
        <p className="text-center text-sm font-medium text-ok">
          {'✓'} Analysis approved &middot; Audit receipt generated &middot; AY {year}
        </p>
      </div>
    );
  }

  if (status === 'rejected') {
    return (
      <div className="border-t border-line bg-danger/10 px-6 py-3">
        <p className="text-center text-sm font-medium text-danger">
          Analysis returned for revision. A new analysis will be queued.
        </p>
      </div>
    );
  }

  return (
    <div className="border-t border-line bg-white px-6 py-3">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-ink">Ready for licensed review</p>
          <p className="text-xs text-muted">
            A qualified professional must approve before this analysis is used for filing.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setStatus('rejected')}
            className="rounded-btn border border-line px-4 py-2 text-sm font-medium text-ink-secondary transition-colors hover:border-danger hover:text-danger"
          >
            Return for revision
          </button>
          <button
            onClick={() => setStatus('approved')}
            className="rounded-btn px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-80"
            style={{ background: 'var(--gradient-brand)' }}
          >
            Approve analysis {'✓'}
          </button>
        </div>
      </div>
    </div>
  );
}
