'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  formatTimestamp,
  normalizeAuditEvent,
  shortHash,
  type AuditEvent,
  type VerifyResult,
} from './audit-types';

type LoadState = 'loading' | 'ready' | 'error';

function EventCard({ event }: { event: AuditEvent }) {
  return (
    <div className="rounded-card border border-periwinkle-soft bg-white p-4 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-periwinkle-soft px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-accent-700">
              {event.type}
            </span>
            <span className="text-xs text-ink-secondary">
              Agent: <span className="font-medium text-ink">{event.agent}</span>
            </span>
            {event.tenantId && <span className="text-xs text-muted">Tenant {event.tenantId}</span>}
          </div>
          <p className="mt-1.5 text-xs text-muted">{formatTimestamp(event.ts)}</p>
        </div>
        <div className="shrink-0 text-right">
          <div className="rounded-full bg-cream px-2 py-0.5 font-mono text-[10px] text-ink-secondary">
            #{shortHash(event.hash)}
          </div>
          <div
            className="mt-1 flex items-center justify-end gap-1 font-mono text-[10px] text-muted"
            title={`Chained to previous event hash ${event.prevHash}`}
          >
            <span aria-hidden="true">{'🔗'}</span>
            <span>prev {shortHash(event.prevHash)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [state, setState] = useState<LoadState>('loading');
  const [verify, setVerify] = useState<VerifyResult | null>(null);
  const [verifyState, setVerifyState] = useState<'idle' | 'checking' | 'error'>('idle');

  const load = useCallback(async () => {
    setState('loading');
    try {
      const res = await fetch('/api/audit?limit=50');
      const envelope = (await res.json()) as {
        success: boolean;
        data: { events: unknown[] } | null;
      };
      if (!res.ok || !envelope.success || envelope.data === null) {
        setState('error');
        return;
      }
      setEvents(envelope.data.events.map(normalizeAuditEvent));
      setState('ready');
    } catch {
      setState('error');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function runVerify() {
    setVerifyState('checking');
    setVerify(null);
    try {
      const res = await fetch('/api/audit/verify');
      const envelope = (await res.json()) as { success: boolean; data: VerifyResult | null };
      if (!res.ok || !envelope.success || envelope.data === null) {
        setVerifyState('error');
        return;
      }
      setVerify(envelope.data);
      setVerifyState('idle');
    } catch {
      setVerifyState('error');
    }
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between gap-4 border-b border-line bg-white/60 px-6 py-4 backdrop-blur-sm">
        <div>
          <h1 className="font-display text-lg font-black tracking-tight text-ink">Audit Trail</h1>
          <p className="text-xs text-muted">Immutable, hash-chained log of every action</p>
        </div>
        <button
          type="button"
          onClick={() => void runVerify()}
          disabled={verifyState === 'checking'}
          className="rounded-btn border border-line px-4 py-2 text-sm font-medium text-ink-secondary transition-colors hover:border-accent hover:text-accent disabled:cursor-wait disabled:opacity-60"
        >
          {verifyState === 'checking' ? 'Verifying…' : 'Verify chain'}
        </button>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl space-y-3">
          {verify && (
            <p
              role="status"
              className={[
                'rounded-btn px-3 py-2 text-sm',
                verify.ok ? 'bg-ok/10 text-ok' : 'bg-danger/10 text-danger',
              ].join(' ')}
            >
              {verify.ok
                ? `Chain intact — ${verify.length ?? events.length} event(s) verified.`
                : `Chain integrity FAILED${verify.firstBadIndex !== null ? ` at index ${verify.firstBadIndex}` : ''}. Investigate immediately.`}
            </p>
          )}
          {verifyState === 'error' && (
            <p role="alert" className="rounded-btn bg-warn/10 px-3 py-2 text-sm text-warn">
              Could not verify — the audit service is unreachable.
            </p>
          )}

          {state === 'loading' && (
            <div role="status" className="rounded-card bg-white/70 p-6 text-center shadow-card">
              <p className="text-sm text-muted">Loading audit events&hellip;</p>
            </div>
          )}

          {state === 'error' && (
            <div className="rounded-card bg-white/70 p-8 text-center shadow-card">
              <p className="text-sm font-medium text-ink-secondary">Backend unreachable</p>
              <p className="mt-1 text-xs text-muted">
                The audit service could not be contacted. No events are shown — Verra never fakes
                audit data.
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

          {state === 'ready' && events.length === 0 && (
            <div className="rounded-card bg-white/70 p-8 text-center shadow-card">
              <p className="text-sm font-medium text-ink-secondary">No audit events yet</p>
              <p className="mt-1 text-xs text-muted">
                Every run, ingestion and approval will appear here with a hash-chain receipt.
              </p>
            </div>
          )}

          {state === 'ready' &&
            events.map((event) => <EventCard key={event.eventId} event={event} />)}
        </div>
      </div>
    </div>
  );
}
