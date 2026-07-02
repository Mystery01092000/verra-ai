'use client';

import { useRef, useState } from 'react';
import { DocumentResultCard } from './DocumentResultCard';
import { normalizeIngestResult, type UploadedDoc } from './ingest';

const MAX_FILE_BYTES = 1_000_000; // 1 MB

interface IngestEnvelope {
  success: boolean;
  data: Record<string, unknown> | null;
  error: string | null;
}

function contentTypeFor(fileName: string): 'text' | 'json' | null {
  const lower = fileName.toLowerCase();
  if (lower.endsWith('.json')) return 'json';
  if (lower.endsWith('.txt')) return 'text';
  return null;
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<UploadedDoc[]>([]);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function patchDoc(id: string, patch: Partial<UploadedDoc>) {
    setDocs((prev) => prev.map((d) => (d.id === id ? { ...d, ...patch } : d)));
  }

  async function ingest(doc: UploadedDoc) {
    patchDoc(doc.id, { state: 'uploading', error: undefined, result: undefined });
    try {
      const res = await fetch('/api/documents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: doc.content, contentType: doc.contentType }),
      });
      const envelope = (await res.json()) as IngestEnvelope;
      if (!res.ok || !envelope.success || envelope.data === null) {
        patchDoc(doc.id, {
          state: 'error',
          error:
            res.status === 502
              ? 'Backend unreachable — the ingestion service could not be contacted.'
              : (envelope.error ?? 'Ingestion failed.'),
        });
        return;
      }
      patchDoc(doc.id, { state: 'done', result: normalizeIngestResult(envelope.data) });
    } catch {
      patchDoc(doc.id, {
        state: 'error',
        error: 'Backend unreachable — the ingestion service could not be contacted.',
      });
    }
  }

  async function addFiles(files: FileList | File[]) {
    for (const file of Array.from(files)) {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const contentType = contentTypeFor(file.name);
      if (contentType === null) {
        setDocs((prev) => [
          {
            id,
            fileName: file.name,
            contentType: 'text',
            content: '',
            state: 'error',
            error: 'Unsupported file type — only .txt and .json are accepted here.',
          },
          ...prev,
        ]);
        continue;
      }
      if (file.size > MAX_FILE_BYTES) {
        setDocs((prev) => [
          {
            id,
            fileName: file.name,
            contentType,
            content: '',
            state: 'error',
            error: 'File exceeds the 1 MB limit.',
          },
          ...prev,
        ]);
        continue;
      }
      let content: string;
      try {
        content = await file.text();
      } catch {
        setDocs((prev) => [
          {
            id,
            fileName: file.name,
            contentType,
            content: '',
            state: 'error',
            error: 'Could not read the file in the browser.',
          },
          ...prev,
        ]);
        continue;
      }
      if (contentType === 'json') {
        try {
          JSON.parse(content);
        } catch {
          setDocs((prev) => [
            {
              id,
              fileName: file.name,
              contentType,
              content: '',
              state: 'error',
              error: 'This .json file is not valid JSON.',
            },
            ...prev,
          ]);
          continue;
        }
      }
      const doc: UploadedDoc = {
        id,
        fileName: file.name,
        contentType,
        content,
        state: 'uploading',
      };
      setDocs((prev) => [doc, ...prev]);
      void ingest(doc);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-line bg-white/60 px-6 py-4 backdrop-blur-sm">
        <h1 className="font-display text-lg font-black tracking-tight text-ink">Documents</h1>
        <p className="text-xs text-muted">
          Upload Form 16, 26AS, AIS, bank statements &mdash; parsed once, reused everywhere
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              if (e.dataTransfer.files.length > 0) void addFiles(e.dataTransfer.files);
            }}
            className={[
              'rounded-card border-2 border-dashed bg-white px-12 py-10 text-center transition-colors',
              dragging ? 'border-accent bg-periwinkle-soft/30' : 'border-line',
            ].join(' ')}
          >
            <p className="mb-2 text-3xl" aria-hidden="true">
              {'📎'}
            </p>
            <p className="font-medium text-ink">Drop documents here</p>
            <p className="mt-1 text-sm text-muted">
              .txt and .json for now &mdash; Form 16 &middot; 26AS &middot; AIS exports
            </p>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="mt-4 rounded-btn px-5 py-2 text-sm font-medium text-white transition-opacity hover:opacity-85"
              style={{ background: 'var(--gradient-brand)' }}
            >
              Browse files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".txt,.json"
              className="hidden"
              aria-label="Choose documents to upload"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) void addFiles(e.target.files);
                e.target.value = '';
              }}
            />
          </div>

          {docs.length > 0 && (
            <section aria-label="Uploaded documents" className="space-y-3">
              <h2 className="text-sm font-semibold text-ink-secondary">This session</h2>
              {docs.map((doc) => (
                <DocumentResultCard key={doc.id} doc={doc} onRetry={(d) => void ingest(d)} />
              ))}
            </section>
          )}

          <p className="text-center text-xs text-muted">
            Documents are parsed once and reused across all modules. Low-confidence fields are
            flagged for human review. Zero retention with AI providers.
          </p>
        </div>
      </div>
    </div>
  );
}
