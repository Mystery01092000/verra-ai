/** Client-side types and tolerant normalizers for the ingestion flow. */

export interface IngestResult {
  documentId: string;
  docType: string;
  classificationConfidence: number;
  extracted: Record<string, unknown>;
  lowConfidenceFields: string[];
  flags: string[];
  status: string;
}

export interface ExtractedField {
  path: string;
  value: string;
  confidence?: number;
}

export interface UploadedDoc {
  id: string;
  fileName: string;
  contentType: 'text' | 'json';
  content: string;
  state: 'uploading' | 'done' | 'error';
  error?: string;
  result?: IngestResult;
}

function pickString(raw: Record<string, unknown>, fallback: string, ...keys: string[]): string {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === 'string' && value.length > 0) return value;
  }
  return fallback;
}

function pickNumber(raw: Record<string, unknown>, ...keys: string[]): number {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === 'number' && Number.isFinite(value)) return value;
  }
  return 0;
}

function pickStringArray(raw: Record<string, unknown>, ...keys: string[]): string[] {
  for (const key of keys) {
    const value = raw[key];
    if (Array.isArray(value)) return value.filter((v): v is string => typeof v === 'string');
  }
  return [];
}

export function normalizeIngestResult(raw: Record<string, unknown>): IngestResult {
  const extractedRaw = raw.extracted;
  const extracted =
    typeof extractedRaw === 'object' && extractedRaw !== null && !Array.isArray(extractedRaw)
      ? (extractedRaw as Record<string, unknown>)
      : {};
  return {
    documentId: pickString(raw, '', 'documentId', 'document_id'),
    docType: pickString(raw, 'unknown', 'docType', 'doc_type'),
    classificationConfidence: pickNumber(
      raw,
      'classificationConfidence',
      'classification_confidence',
    ),
    extracted,
    lowConfidenceFields: pickStringArray(raw, 'lowConfidenceFields', 'low_confidence_fields'),
    flags: pickStringArray(raw, 'flags'),
    status: pickString(raw, 'parsed', 'status'),
  };
}

const MAX_FIELDS = 120;
const MAX_DEPTH = 3;
const MAX_VALUE_CHARS = 120;

function previewValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'string') return value.length > 0 ? value : '—';
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  const json = JSON.stringify(value);
  return json.length > MAX_VALUE_CHARS ? `${json.slice(0, MAX_VALUE_CHARS)}…` : json;
}

/** Flatten extracted payloads into rows; supports {value, confidence} field wrappers. */
export function flattenExtracted(
  node: Record<string, unknown>,
  prefix = '',
  depth = 0,
  out: ExtractedField[] = [],
): ExtractedField[] {
  for (const [key, value] of Object.entries(node)) {
    if (out.length >= MAX_FIELDS) return out;
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      const wrapped = value as Record<string, unknown>;
      if ('value' in wrapped && typeof wrapped.confidence === 'number') {
        out.push({
          path,
          value: previewValue(wrapped.value),
          confidence: wrapped.confidence,
        });
        continue;
      }
      if (depth < MAX_DEPTH) {
        flattenExtracted(wrapped, path, depth + 1, out);
        continue;
      }
    }
    out.push({ path, value: previewValue(value) });
  }
  return out;
}

export function isLowConfidence(field: ExtractedField, lowConfidenceFields: string[]): boolean {
  const leaf = field.path.split('.').pop() ?? field.path;
  return lowConfidenceFields.includes(field.path) || lowConfidenceFields.includes(leaf);
}
