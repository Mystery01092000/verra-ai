'use client';

import { useState } from 'react';

export interface Citation {
  type: 'document' | 'rule';
  label: string;
  page?: number;
}

export interface CitedAmountProps {
  amount: number;
  currency?: string;
  citation?: Citation;
  confidence?: number;
  locale?: string;
}

export function CitedAmount({
  amount,
  currency = 'INR',
  citation,
  confidence,
  locale = 'en-IN',
}: CitedAmountProps) {
  const [show, setShow] = useState(false);

  const formatted = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount);

  const hasCitation = Boolean(citation);
  const lowConfidence = confidence !== undefined && confidence < 0.8;
  const missingCitation = !hasCitation;

  return (
    <span className="relative inline-flex items-center gap-1">
      <span
        className={[
          'cursor-help rounded px-1 transition-colors',
          missingCitation ? 'bg-danger/15 text-danger' : '',
          !missingCitation && lowConfidence ? 'bg-warn/15 text-warn' : '',
          !missingCitation && !lowConfidence ? 'hover:bg-periwinkle-soft' : '',
        ].join(' ')}
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        {formatted}
      </span>
      {show && (
        <span className="absolute bottom-full left-0 z-10 mb-1 w-56 rounded-card border border-periwinkle-soft bg-white p-2 text-xs shadow-card">
          {citation ? (
            <>
              <span className="font-semibold text-ink">
                {citation.type === 'document' ? 'Source document' : 'Rule'}
              </span>
              <div className="mt-0.5 text-ink-secondary">{citation.label}</div>
              {citation.page !== undefined && (
                <div className="text-muted">Page {citation.page}</div>
              )}
            </>
          ) : (
            <span className="text-danger">No source citation</span>
          )}
          {confidence !== undefined && (
            <div className="mt-1 text-muted">Confidence: {Math.round(confidence * 100)}%</div>
          )}
        </span>
      )}
    </span>
  );
}
