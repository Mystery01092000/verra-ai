'use client';
import type { DocumentContextState } from './document-context';

interface DocumentContextChipProps {
  state: DocumentContextState;
}

/** Small status chip above the input: attached doc name + docType + review badge. */
export function DocumentContextChip({ state }: DocumentContextChipProps) {
  const isError = state.status === 'error';
  const badge =
    state.status === 'ingesting'
      ? 'Ingesting…'
      : state.status === 'ready'
        ? (state.context?.docType ?? 'unknown')
        : state.status === 'unsupported'
          ? 'Not ingested'
          : 'Ingestion failed';

  return (
    <div
      className="mb-2 inline-flex max-w-full flex-wrap items-center gap-2 rounded-full border bg-white px-3 py-1.5 text-xs shadow-sm"
      style={{ borderColor: isError ? 'var(--color-danger)' : 'var(--color-line)' }}
      role="status"
    >
      <span aria-hidden="true">📄</span>
      <span className="max-w-[180px] truncate font-medium text-ink">{state.fileName}</span>
      <span
        className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
        style={
          isError
            ? {
                background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)',
                color: 'var(--color-danger)',
              }
            : {
                background: 'var(--color-periwinkle-soft)',
                color: 'var(--color-accent-600)',
              }
        }
      >
        {badge}
      </span>
      {state.status === 'ready' && state.context?.needsReview && (
        <span
          className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
          style={{
            background: 'color-mix(in srgb, var(--color-warn) 14%, transparent)',
            color: 'var(--color-warn)',
          }}
        >
          Needs review
        </span>
      )}
      {(isError || state.status === 'unsupported') && state.error && (
        <span className="w-full text-[11px] text-muted sm:w-auto">{state.error}</span>
      )}
    </div>
  );
}
