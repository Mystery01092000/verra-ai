'use client';

import { flattenExtracted, isLowConfidence, type IngestResult, type UploadedDoc } from './ingest';

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100);
  return (
    <div className="flex items-center gap-2">
      <div
        role="progressbar"
        aria-label="Classification confidence"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-1.5 w-28 overflow-hidden rounded-full bg-cream"
      >
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, background: 'var(--gradient-brand)' }}
        />
      </div>
      <span className="text-xs text-muted">{pct}%</span>
    </div>
  );
}

function StatusBanner({ result }: { result: IngestResult }) {
  if (result.status === 'needs_review') {
    return (
      <p role="alert" className="mt-3 rounded-btn bg-warn/10 px-3 py-2 text-xs text-warn">
        Low-confidence extraction &mdash; flagged for human review. A person must verify these
        fields before they are used in any filing.
      </p>
    );
  }
  if (result.status === 'unsupported') {
    return (
      <p role="alert" className="mt-3 rounded-btn bg-danger/10 px-3 py-2 text-xs text-danger">
        Verra could not classify this document. It will not be used until reviewed.
      </p>
    );
  }
  return null;
}

function ExtractedTable({ result }: { result: IngestResult }) {
  const fields = flattenExtracted(result.extracted);
  if (fields.length === 0) {
    return <p className="mt-3 text-xs text-muted">No fields were extracted.</p>;
  }
  return (
    <table className="mt-3 w-full text-xs">
      <thead>
        <tr className="border-b border-line text-left text-ink-secondary">
          <th className="py-1.5 font-medium">Field</th>
          <th className="py-1.5 font-medium">Value</th>
          <th className="py-1.5 text-right font-medium">Confidence</th>
        </tr>
      </thead>
      <tbody>
        {fields.map((field) => {
          const low = isLowConfidence(field, result.lowConfidenceFields);
          return (
            <tr
              key={field.path}
              className={['border-b border-line last:border-0', low ? 'bg-warn/10' : ''].join(' ')}
            >
              <td className="py-1.5 pr-2 font-mono text-[11px] text-ink-secondary">
                {field.path}
                {low && (
                  <span className="ml-1.5 rounded-full bg-warn/20 px-1.5 py-0.5 text-[9px] font-semibold text-warn">
                    review
                  </span>
                )}
              </td>
              <td className="max-w-0 truncate py-1.5 pr-2 text-ink" title={field.value}>
                {field.value}
              </td>
              <td className="py-1.5 text-right text-muted">
                {field.confidence !== undefined ? `${Math.round(field.confidence * 100)}%` : '—'}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export interface DocumentResultCardProps {
  doc: UploadedDoc;
  onRetry: (doc: UploadedDoc) => void;
}

export function DocumentResultCard({ doc, onRetry }: DocumentResultCardProps) {
  return (
    <div className="rounded-card border border-periwinkle-soft bg-white p-4 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="truncate text-sm font-medium text-ink">{doc.fileName}</span>
          {doc.result && (
            <span className="shrink-0 rounded-full bg-periwinkle-soft px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-accent-700">
              {doc.result.docType.replace(/_/g, ' ')}
            </span>
          )}
        </div>
        {doc.state === 'uploading' && (
          <span role="status" className="text-xs text-muted">
            Parsing&hellip;
          </span>
        )}
        {doc.result && <ConfidenceBar value={doc.result.classificationConfidence} />}
      </div>

      {doc.state === 'error' && (
        <div className="mt-3 flex items-center justify-between gap-3 rounded-btn bg-cream px-3 py-2">
          <p className="text-xs text-muted">{doc.error ?? 'Upload failed.'}</p>
          <button
            type="button"
            onClick={() => onRetry(doc)}
            className="shrink-0 rounded-btn border border-line px-3 py-1 text-xs font-medium text-ink-secondary transition-colors hover:border-accent hover:text-accent"
          >
            Retry
          </button>
        </div>
      )}

      {doc.result && (
        <>
          <StatusBanner result={doc.result} />
          {doc.result.flags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {doc.result.flags.map((flag) => (
                <span
                  key={flag}
                  className="rounded-full bg-cream px-2 py-0.5 text-[10px] font-medium text-ink-secondary"
                >
                  {flag}
                </span>
              ))}
            </div>
          )}
          <ExtractedTable result={doc.result} />
        </>
      )}
    </div>
  );
}
