/**
 * Client-side helper: pushes an attached .txt/.json document through the
 * existing /api/documents ingestion route and distils the result into a
 * compact `documentContext` payload for subsequent chat messages.
 */

export interface DocumentKeyField {
  path: string;
  value: string;
}

export interface ChatDocumentContext {
  docType: string;
  keyFields: DocumentKeyField[];
  needsReview: boolean;
}

export interface DocumentContextState {
  fileName: string;
  status: 'ingesting' | 'ready' | 'error' | 'unsupported';
  context?: ChatDocumentContext;
  error?: string;
}

interface IngestEnvelope {
  success: boolean;
  data: Record<string, unknown> | null;
  error: string | null;
}

const MAX_KEY_FIELDS = 6;
const MAX_VALUE_CHARS = 80;

export function ingestContentTypeFor(fileName: string): 'text' | 'json' | null {
  const lower = fileName.toLowerCase();
  if (lower.endsWith('.json')) return 'json';
  if (lower.endsWith('.txt')) return 'text';
  return null;
}

function previewValue(value: unknown): string | null {
  if (typeof value === 'string') return value.trim() || null;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  return null;
}

/** Pulls up to MAX_KEY_FIELDS primitive (or {value, confidence}) fields. */
function extractKeyFields(
  node: unknown,
  prefix = '',
  out: DocumentKeyField[] = [],
): DocumentKeyField[] {
  if (typeof node !== 'object' || node === null || Array.isArray(node)) return out;
  for (const [key, value] of Object.entries(node as Record<string, unknown>)) {
    if (out.length >= MAX_KEY_FIELDS) return out;
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      const wrapped = value as Record<string, unknown>;
      if ('value' in wrapped) {
        const preview = previewValue(wrapped.value);
        if (preview) out.push({ path, value: preview.slice(0, MAX_VALUE_CHARS) });
        continue;
      }
      extractKeyFields(wrapped, path, out);
      continue;
    }
    const preview = previewValue(value);
    if (preview) out.push({ path, value: preview.slice(0, MAX_VALUE_CHARS) });
  }
  return out;
}

function pickString(raw: Record<string, unknown>, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === 'string' && value.length > 0) return value;
  }
  return undefined;
}

function pickArrayLength(raw: Record<string, unknown>, ...keys: string[]): number {
  for (const key of keys) {
    const value = raw[key];
    if (Array.isArray(value)) return value.length;
  }
  return 0;
}

export async function ingestDocumentForChat(
  fileName: string,
  content: string,
): Promise<DocumentContextState> {
  const contentType = ingestContentTypeFor(fileName);
  if (!contentType) {
    return {
      fileName,
      status: 'unsupported',
      error: 'Only .txt and .json attachments are ingested; raw text is still sent to the chat.',
    };
  }

  try {
    const res = await fetch('/api/documents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, contentType }),
    });
    const envelope = (await res.json()) as IngestEnvelope;
    if (!res.ok || !envelope.success || envelope.data === null) {
      return {
        fileName,
        status: 'error',
        error:
          res.status === 502
            ? 'Ingestion service unreachable — the document was not parsed.'
            : (envelope.error ?? 'Ingestion failed — the document was not parsed.'),
      };
    }

    const raw = envelope.data;
    const docType = pickString(raw, 'docType', 'doc_type') ?? 'unknown';
    const lowConfidence = pickArrayLength(raw, 'lowConfidenceFields', 'low_confidence_fields');
    const flags = pickArrayLength(raw, 'flags');
    return {
      fileName,
      status: 'ready',
      context: {
        docType,
        keyFields: extractKeyFields(raw.extracted),
        needsReview: lowConfidence > 0 || flags > 0,
      },
    };
  } catch {
    return {
      fileName,
      status: 'error',
      error: 'Ingestion service unreachable — the document was not parsed.',
    };
  }
}
