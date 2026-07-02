/** Tolerant normalizers for audit-chain events (camelCase or snake_case wire). */

export interface AuditEvent {
  eventId: string;
  type: string;
  tenantId: string;
  agent: string;
  ts: string;
  hash: string;
  prevHash: string;
}

export interface VerifyResult {
  ok: boolean;
  firstBadIndex: number | null;
  length: number | null;
}

function pickString(raw: Record<string, unknown>, fallback: string, ...keys: string[]): string {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === 'string' && value.length > 0) return value;
    if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  }
  return fallback;
}

export function normalizeAuditEvent(raw: unknown, index: number): AuditEvent {
  const obj = typeof raw === 'object' && raw !== null ? (raw as Record<string, unknown>) : {};
  return {
    eventId: pickString(obj, `event-${index}`, 'eventId', 'event_id', 'id'),
    type: pickString(obj, 'unknown', 'type', 'eventType', 'event_type'),
    tenantId: pickString(obj, '', 'tenantId', 'tenant_id'),
    agent: pickString(obj, 'system', 'agent'),
    ts: pickString(obj, '', 'ts', 'timestamp', 'createdAt', 'created_at'),
    hash: pickString(obj, '', 'hash'),
    prevHash: pickString(obj, '', 'prevHash', 'prev_hash'),
  };
}

export function shortHash(hash: string): string {
  return hash ? `${hash.slice(0, 10)}…` : '—';
}

export function formatTimestamp(ts: string): string {
  if (!ts) return 'unknown time';
  const asNumber = Number(ts);
  const date = Number.isFinite(asNumber)
    ? new Date(asNumber > 1e12 ? asNumber : asNumber * 1000)
    : new Date(ts);
  if (Number.isNaN(date.getTime())) return ts;
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}
