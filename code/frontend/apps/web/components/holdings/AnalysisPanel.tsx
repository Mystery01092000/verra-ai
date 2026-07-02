'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { pollPlanningRun, startPlanningRun } from './holdings-api';
import type { PlanningRunResult } from './holdings-shared';

type PlanningCapability = 'portfolio_analysis' | 'financial_planning';

interface AnalysisPanelProps {
  annualIncome: number | undefined;
  hasHoldings: boolean;
}

interface RunState {
  capability: PlanningCapability;
  phase: 'starting' | 'polling' | 'done' | 'awaiting_approval' | 'failed' | 'timeout';
  result?: PlanningRunResult;
  error?: string;
}

const POLL_INTERVAL_MS = 2_000;
const MAX_POLLS = 15; // ~30s

const CAPABILITY_LABELS: Record<PlanningCapability, string> = {
  portfolio_analysis: 'Portfolio analysis',
  financial_planning: 'Financial plan draft',
};

const DISCLAIMER =
  'Draft analysis — review with a SEBI-registered investment adviser / CA before acting.';

export function AnalysisPanel({ annualIncome, hasHoldings }: AnalysisPanelProps) {
  const [run, setRun] = useState<RunState | null>(null);
  const runTokenRef = useRef(0);

  // Invalidate in-flight polling loops on unmount.
  useEffect(() => {
    return () => {
      runTokenRef.current += 1;
    };
  }, []);

  async function launch(capability: PlanningCapability) {
    const token = ++runTokenRef.current;
    setRun({ capability, phase: 'starting' });

    const started = await startPlanningRun(capability, annualIncome);
    if (token !== runTokenRef.current) return;
    if (!started.ok) {
      setRun({ capability, phase: 'failed', error: started.error });
      return;
    }

    setRun({ capability, phase: 'polling' });
    for (let attempt = 0; attempt < MAX_POLLS; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
      if (token !== runTokenRef.current) return;

      const polled = await pollPlanningRun(started.data.runId);
      if (token !== runTokenRef.current) return;
      if (!polled.ok) {
        setRun({ capability, phase: 'failed', error: polled.error });
        return;
      }

      const { status } = polled.data;
      if (status === 'done') {
        setRun({ capability, phase: 'done', result: polled.data });
        return;
      }
      if (status === 'awaiting_approval') {
        setRun({ capability, phase: 'awaiting_approval', result: polled.data });
        return;
      }
      if (status === 'failed') {
        setRun({
          capability,
          phase: 'failed',
          error: 'The analysis run failed on the backend. Try again in a moment.',
        });
        return;
      }
      // planned / executing → keep polling
    }
    setRun({
      capability,
      phase: 'timeout',
      error: 'The run did not finish within 30 seconds. It may still complete — try again shortly.',
    });
  }

  const busy = run?.phase === 'starting' || run?.phase === 'polling';

  return (
    <section
      aria-label="AI analysis"
      className="rounded-card border border-line bg-white p-5 shadow-card"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-ink">Verra insights</h3>
          <p className="mt-0.5 text-xs text-muted">
            AI-drafted, asset-class level only — a licensed human approves anything you act on.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void launch('portfolio_analysis')}
            disabled={busy || !hasHoldings}
            className="rounded-btn bg-ink px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-85 disabled:opacity-40"
          >
            <span aria-hidden="true">✦ </span>
            Analyze portfolio with Verra
          </button>
          <button
            type="button"
            onClick={() => void launch('financial_planning')}
            disabled={busy || !hasHoldings}
            className="rounded-btn border border-line px-4 py-2 text-sm font-medium text-ink-secondary transition-colors hover:border-accent hover:text-accent disabled:opacity-40"
          >
            Draft financial plan
          </button>
        </div>
      </div>

      {!hasHoldings && (
        <p className="mt-3 text-xs text-muted">Add at least one holding to run an analysis.</p>
      )}

      {busy && run && (
        <div className="mt-4 rounded-2xl bg-cream px-4 py-3" role="status" aria-busy="true">
          <p className="text-sm text-ink-secondary">
            {run.phase === 'starting'
              ? `Starting ${CAPABILITY_LABELS[run.capability].toLowerCase()} run…`
              : `Verra is working through your holdings… (${CAPABILITY_LABELS[run.capability]})`}
          </p>
        </div>
      )}

      {run && (run.phase === 'failed' || run.phase === 'timeout') && (
        <div
          role="alert"
          className="mt-4 rounded-2xl border px-4 py-3"
          style={{
            borderColor: 'var(--color-danger)',
            background: 'color-mix(in srgb, var(--color-danger) 6%, transparent)',
          }}
        >
          <p className="text-sm text-ink">{run.error ?? 'The analysis could not be completed.'}</p>
          <button
            type="button"
            onClick={() => void launch(run.capability)}
            className="mt-2 rounded-btn border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink-secondary hover:border-accent hover:text-accent"
          >
            Retry
          </button>
        </div>
      )}

      {run && (run.phase === 'done' || run.phase === 'awaiting_approval') && run.result && (
        <div className="mt-4 rounded-2xl border border-line bg-cream/60 p-5">
          <p className="text-[11px] font-semibold uppercase tracking-widest text-accent">
            {CAPABILITY_LABELS[run.capability]}
          </p>

          {run.result.content ? (
            <div className="prose-sm mt-2 max-w-none text-sm leading-relaxed text-ink">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{run.result.content}</ReactMarkdown>
            </div>
          ) : (
            <p className="mt-2 text-sm text-muted">
              {run.phase === 'awaiting_approval'
                ? 'The draft is ready on the approvals queue — its contents unlock after human review.'
                : 'The run completed but returned no narrative output.'}
            </p>
          )}

          {run.result.citations.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {run.result.citations.map((citation, i) => (
                <span
                  key={`${citation}-${i}`}
                  className="rounded-full border border-line bg-white px-2.5 py-0.5 text-[11px] font-medium text-accent"
                >
                  § {citation}
                </span>
              ))}
            </div>
          )}

          {run.phase === 'awaiting_approval' && (
            <div
              className="mt-4 rounded-xl border px-4 py-3"
              style={{
                borderColor: 'var(--color-warn)',
                background: 'color-mix(in srgb, var(--color-warn) 8%, transparent)',
              }}
            >
              <p className="text-sm font-medium text-ink">Awaiting human approval</p>
              <p className="mt-1 text-xs text-ink-secondary">
                {run.capability === 'financial_planning'
                  ? 'Financial plans always require sign-off by a licensed professional before they can be shared or acted on.'
                  : 'This run is queued for review by a licensed professional before it can be relied upon.'}{' '}
                <Link href="/approvals" className="font-semibold text-accent underline">
                  Go to approvals
                </Link>
              </p>
            </div>
          )}

          <p className="mt-4 border-t border-line pt-3 text-[11px] font-medium text-muted">
            {DISCLAIMER}
          </p>
        </div>
      )}
    </section>
  );
}
