'use client';
import { useState, useRef } from 'react';
import { AssistantThread } from '@/components/chat/AssistantThread';
import { extractDocumentText } from '@/lib/extract-document';

const AGENT_OPTIONS = [
  { id: 'tax-planner', label: 'Tax Planner', icon: '✦' },
  { id: 'regime-compare', label: 'Regime Compare', icon: '⊞' },
  { id: 'deduction-finder', label: 'Deduction Finder', icon: '◈' },
  { id: 'advance-tax', label: 'Advance Tax', icon: '⊟' },
] as const;

type AgentId = (typeof AGENT_OPTIONS)[number]['id'];

interface TaxChatbotProps {
  assessmentYear: string;
}

export function TaxChatbot({ assessmentYear }: TaxChatbotProps) {
  const [activeAgent, setActiveAgent] = useState<AgentId>('tax-planner');
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const [documentText, setDocumentText] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleAttach() {
    fileInputRef.current?.click();
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setAttachedFile(file.name);
    try {
      const text = await extractDocumentText(file);
      setDocumentText(text);
    } catch {
      setDocumentText(`[Could not extract text from ${file.name}]`);
    }
    if (e.target) e.target.value = '';
  }

  function handleAgentChange(id: string) {
    setActiveAgent(id as AgentId);
    setAttachedFile(null);
    setDocumentText(null);
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-zinc-100 bg-white/80 px-6 py-4 backdrop-blur-sm">
        <div>
          <h1
            className="text-[17px] font-semibold text-zinc-900"
            style={{ fontFamily: 'Archivo, sans-serif' }}
          >
            Tax Planning
          </h1>
          <p className="mt-0.5 text-[12px] text-zinc-400">
            Assessment Year {assessmentYear} · India · AI-powered with human oversight
          </p>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <AssistantThread
          agentMode={activeAgent}
          agentOptions={AGENT_OPTIONS}
          onAgentChange={handleAgentChange}
          onAttachDocument={handleAttach}
          onClearDocument={() => {
            setAttachedFile(null);
            setDocumentText(null);
          }}
          attachedFile={attachedFile}
          documentText={documentText}
          onDark={false}
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
