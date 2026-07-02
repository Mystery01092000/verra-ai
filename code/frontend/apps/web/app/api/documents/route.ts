import { NextResponse } from 'next/server';
import { gatewayPostJson } from '../gateway';

export const dynamic = 'force-dynamic';

const MAX_CONTENT_BYTES = 2_000_000; // 2 MB of text is plenty for .txt/.json uploads

interface IngestRequest {
  documentId?: string;
  content: string;
  contentType: 'text' | 'json';
  docType?: string;
}

function parseIngestRequest(raw: unknown): IngestRequest | string {
  if (typeof raw !== 'object' || raw === null) return 'Request body must be a JSON object';
  const body = raw as Record<string, unknown>;

  if (typeof body.content !== 'string' || body.content.length === 0) {
    return 'content must be a non-empty string';
  }
  if (body.content.length > MAX_CONTENT_BYTES) {
    return 'content exceeds the 2 MB limit';
  }
  if (body.contentType !== 'text' && body.contentType !== 'json') {
    return 'contentType must be "text" or "json"';
  }
  const documentId =
    typeof body.documentId === 'string' && body.documentId.length > 0 ? body.documentId : undefined;
  const docType =
    typeof body.docType === 'string' && body.docType.length > 0 ? body.docType : undefined;

  return { documentId, content: body.content, contentType: body.contentType, docType };
}

export async function POST(request: Request): Promise<NextResponse> {
  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return NextResponse.json(
      { success: false, data: null, error: 'Invalid JSON body' },
      { status: 400 },
    );
  }

  const parsed = parseIngestRequest(raw);
  if (typeof parsed === 'string') {
    return NextResponse.json({ success: false, data: null, error: parsed }, { status: 400 });
  }

  const result = await gatewayPostJson<Record<string, unknown>>('/v1/ingest', parsed, 60_000);
  if (!result.ok || result.data === null) {
    return NextResponse.json(
      { success: false, data: null, error: result.error ?? 'Ingestion service unavailable' },
      { status: 502 },
    );
  }

  return NextResponse.json({ success: true, data: result.data, error: null });
}
