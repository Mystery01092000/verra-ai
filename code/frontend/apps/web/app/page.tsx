'use client';
import { useRef, useState } from 'react';
import { AssistantThread } from '@/components/chat/AssistantThread';
import { UserButton } from '@/components/auth/UserButton';
import { extractDocumentText } from '@/lib/extract-document';

export default function Home() {
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleAttach() {
    fileInputRef.current?.click();
  }

  function handleClearDocument() {
    setAttachedFile(null);
    setDocumentText(null);
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setAttachedFile(file.name);
    try {
      setDocumentText(await extractDocumentText(file));
    } catch {
      setDocumentText(null);
    }
    if (e.target) e.target.value = '';
  }

  return (
    <div className="flex h-full flex-col">
      {/* Transparent header over sky */}
      <header className="flex items-center justify-between px-6 py-4">
        <div>
          <h1
            style={{
              fontFamily: 'Archivo, sans-serif',
              fontWeight: 800,
              fontSize: 20,
              color: 'var(--color-on-dark)',
            }}
          >
            Ask Verra
          </h1>
          <p style={{ fontSize: 12, color: 'var(--color-on-dark-muted)', marginTop: 2 }}>
            Cited · Auditable · Human-approved
          </p>
        </div>
        <UserButton onDark={true} />
      </header>

      {/* Chat fills remaining space */}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <AssistantThread
          onAttachDocument={handleAttach}
          onClearDocument={handleClearDocument}
          attachedFile={attachedFile}
          documentText={documentText}
          onDark={true}
        />
      </div>

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.xlsx,.xls,.csv,.txt,.jpg,.jpeg,.png"
        onChange={handleFileChange}
      />
    </div>
  );
}
