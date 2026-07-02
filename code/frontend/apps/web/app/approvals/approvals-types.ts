/** Tolerant normalizers for runs awaiting human approval (PRD FR-TR-2). */

export interface ApprovalRun {
  runId: string;
  status: string;
  capability: string;
  createdAt: string;
  summary: string | null;
  citations: string[];
}

function pickString(raw: Record<string, unknown>, fallback: string, ...keys: string[]): string {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === 'string' && value.length > 0) return value;
  }
  return fallback;
}

function citationLabel(citation: unknown): string | null {
  if (typeof citation === 'string') return citation;
  if (typeof citation !== 'object' || citation === null) return null;
  const obj = citation as Record<string, unknown>;
  for (const key of ['label', 'sourceCitation', 'source_citation', 'source', 'section']) {
    const value = obj[key];
    if (typeof value === 'string' && value.length > 0) return value;
  }
  return null;
}

export function normalizeRun(raw: unknown, index: number): ApprovalRun {
  const obj = typeof raw === 'object' && raw !== null ? (raw as Record<string, unknown>) : {};
  const citationsRaw = Array.isArray(obj.citations) ? obj.citations : [];
  return {
    runId: pickString(obj, `run-${index}`, 'runId', 'run_id', 'id'),
    status: pickString(obj, 'needs_approval', 'status'),
    capability: pickString(obj, 'unknown', 'capability'),
    createdAt: pickString(obj, '', 'createdAt', 'created_at', 'ts'),
    summary: pickString(obj, '', 'summary', 'description') || null,
    citations: citationsRaw
      .map(citationLabel)
      .filter((label): label is string => label !== null)
      .slice(0, 8),
  };
}

export function formatCreatedAt(value: string): string {
  if (!value) return 'unknown time';
  const asNumber = Number(value);
  const date = Number.isFinite(asNumber)
    ? new Date(asNumber > 1e12 ? asNumber : asNumber * 1000)
    : new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}
