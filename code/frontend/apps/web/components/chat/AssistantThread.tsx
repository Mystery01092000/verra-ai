'use client';
import { useState, useRef, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { ChatInput, type AgentOption } from './ChatInput';
import { MessageBubble } from './MessageBubble';
import { ModePicker } from './ModePicker';
import { DocumentContextChip } from './DocumentContextChip';
import { ingestDocumentForChat, type DocumentContextState } from './document-context';
import { AuthModal } from '@/components/auth/AuthModal';

export interface Citation {
  label: string;
  page?: number;
  type: 'document' | 'rule' | 'section';
}

export type ChatProvider = 'bedrock' | 'anthropic' | 'gateway' | 'unconfigured';

export interface Downloadable {
  filename: string;
  content: string;
  mimeType: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
  pending?: boolean;
  pendingLabel?: string;
  downloadable?: Downloadable;
  provider?: ChatProvider;
  model?: string;
}

interface ChatApiResponse {
  content: string;
  provider?: ChatProvider;
  model?: string;
  citations?: Citation[];
  downloadable?: Downloadable;
}

interface AssistantThreadProps {
  agentMode?: string;
  onAttachDocument?: () => void;
  onClearDocument?: () => void;
  attachedFile?: string | null;
  documentText?: string | null;
  onDark?: boolean;
  agentOptions?: readonly AgentOption[];
  onAgentChange?: (mode: string) => void;
}

const DEFAULT_SUGGESTIONS: string[] = [
  'What is my estimated tax liability for AY 2025-26?',
  'Compare old vs new tax regime for my income profile',
  'What advance tax installments are due this quarter?',
  'Explain Section 87A rebate eligibility',
];

const DEFAULT_HEADING: { title: string; subtitle: string } = {
  title: 'Ask Verra anything',
  subtitle: 'Every answer is cited. Nothing is filed without your approval.',
};

const AGENT_SUGGESTIONS: Record<string, string[]> = {
  default: DEFAULT_SUGGESTIONS,
  general: DEFAULT_SUGGESTIONS,
  portfolio: [
    'Review my asset allocation across equity, debt and gold',
    'Am I adequately insured for my income level?',
    'How are gains on equity mutual funds held 2 years taxed?',
    'Is my debt load high relative to my assets?',
  ],
  'nri-tax': [
    'Am I a non-resident for Indian tax purposes this year?',
    'How is interest on NRE vs NRO accounts taxed?',
    'TDS when an NRI sells property in India',
    'Which DTAA benefits apply to a US-based NRI?',
  ],
  'financial-planning': [
    'Draft a financial plan around my goals and holdings',
    'Should I prepay my home loan or invest the surplus?',
    'How much life and health cover do I need?',
    'Plan my emergency fund and monthly investing budget',
  ],
  'tax-planner': [
    'What deductions can I claim under 80C?',
    'How to maximise tax savings for FY 2025-26?',
    'Should I invest in NPS for additional deduction?',
    'Tax saving ELSS vs PPF vs NSC — which is better?',
  ],
  'regime-compare': [
    'Compare old vs new regime at ₹15L salary',
    'Which regime is better with HRA and 80C?',
    'At what income does new regime become disadvantageous?',
    'Show old vs new regime for ₹25L income with deductions',
  ],
  'deduction-finder': [
    'List all deductions available under old regime',
    'Am I eligible for HRA exemption?',
    'Section 80D health insurance deduction limits for FY 2025-26',
    'Can I claim home loan interest under Section 24(b)?',
  ],
  'advance-tax': [
    'When are advance tax instalments due for FY 2025-26?',
    'Calculate advance tax on ₹50L business income',
    'Penalty for missing advance tax deadline — Section 234B/234C',
    'Is advance tax applicable to salaried employees with Form 16?',
  ],
};

const AGENT_HEADINGS: Record<string, { title: string; subtitle: string }> = {
  default: DEFAULT_HEADING,
  general: DEFAULT_HEADING,
  portfolio: {
    title: 'Portfolio',
    subtitle: 'Asset-class insights on your holdings — drafts for adviser review.',
  },
  'nri-tax': {
    title: 'NRI Taxes',
    subtitle: 'Residency, FEMA/RBI and DTAA questions — cited, human-reviewed.',
  },
  'financial-planning': {
    title: 'Financial Planning',
    subtitle: 'Plan drafts that always route to a licensed professional for approval.',
  },
  'tax-planner': {
    title: 'Tax Planner',
    subtitle: 'Get personalised tax-saving strategies for your income.',
  },
  'regime-compare': {
    title: 'Regime Comparator',
    subtitle: 'Old vs new regime — see which saves you more.',
  },
  'deduction-finder': {
    title: 'Deduction Finder',
    subtitle: "Find every deduction you're eligible for.",
  },
  'advance-tax': {
    title: 'Advance Tax Calculator',
    subtitle: 'Know your installments and avoid Section 234B/C penalties.',
  },
};

const THINKING_LABELS: Record<string, string> = {
  default: 'Thinking…',
  general: 'Thinking…',
  portfolio: 'Reviewing your portfolio…',
  'nri-tax': 'Checking residency and FEMA rules…',
  'financial-planning': 'Drafting your plan…',
  'tax-planner': 'Calculating tax implications…',
  'regime-compare': 'Comparing old vs new regime…',
  'deduction-finder': 'Searching for deductions…',
  'advance-tax': 'Computing advance tax schedule…',
};

export function AssistantThread({
  agentMode,
  onAttachDocument,
  onClearDocument,
  attachedFile,
  documentText,
  onDark = false,
  agentOptions,
  onAgentChange,
}: AssistantThreadProps) {
  const { data: session, status } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const [pendingMsg, setPendingMsg] = useState('');
  const [localMode, setLocalMode] = useState('general');
  const [docContext, setDocContext] = useState<DocumentContextState | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const loadedRef = useRef(false);

  // When a parent supplies its own agentOptions (e.g. TaxChatbot) the mode is
  // controlled from outside; otherwise this thread owns a compact mode picker.
  const hasExternalAgentPicker = Boolean(agentOptions && agentOptions.length > 0);
  const mode = hasExternalAgentPicker ? (agentMode ?? 'default') : (agentMode ?? localMode);

  // Attach-document flow: run attached .txt/.json content through ingestion so
  // the next message can carry a compact documentContext. Honest by design —
  // failures surface in the chip and never silently drop the attachment.
  useEffect(() => {
    if (!attachedFile || !documentText) {
      setDocContext(null);
      return;
    }
    let cancelled = false;
    setDocContext({ fileName: attachedFile, status: 'ingesting' });
    void ingestDocumentForChat(attachedFile, documentText).then((state) => {
      if (!cancelled) setDocContext(state);
    });
    return () => {
      cancelled = true;
    };
  }, [attachedFile, documentText]);

  const clearChat = () => {
    setMessages([]);
    try {
      localStorage.removeItem(storageKey);
    } catch {
      // ignore
    }
  };

  const storageKey = session?.user?.email ? `verra-chat-${session.user.email}` : 'verra-chat-guest';

  // Load saved messages when storageKey changes
  useEffect(() => {
    loadedRef.current = false;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw) as Array<Omit<Message, 'timestamp'> & { timestamp: string }>;
        const restored: Message[] = parsed.map((m) => ({
          ...m,
          timestamp: new Date(m.timestamp),
        }));
        setMessages(restored);
      } else {
        setMessages([]);
      }
    } catch {
      setMessages([]);
    }
    loadedRef.current = true;
  }, [storageKey]);

  // Save messages to localStorage after initial load
  useEffect(() => {
    if (!loadedRef.current) return;
    try {
      const toSave = messages.slice(-50);
      localStorage.setItem(storageKey, JSON.stringify(toSave));
    } catch {
      // localStorage may be unavailable in private browsing; silently ignore
    }
  }, [messages, storageKey]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;

    if (!session && status !== 'loading') {
      setPendingMsg(text);
      setShowAuth(true);
      return;
    }

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    const pendingAssistantMsg: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      pending: true,
      pendingLabel: THINKING_LABELS[mode] ?? 'Thinking…',
    };

    setMessages((prev) => [...prev, userMsg, pendingAssistantMsg]);
    setLoading(true);

    try {
      // Send only the last 10 messages to avoid stale history confusing the model
      const recentHistory = messages.filter((m) => !m.pending).slice(-10);
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: recentHistory,
          agentMode: mode,
          documentText,
          ...(attachedFile ? { documentName: attachedFile } : {}),
          ...(docContext?.status === 'ready' && docContext.context
            ? { documentContext: docContext.context }
            : {}),
        }),
      });
      const data = (await res.json()) as ChatApiResponse;

      const aiMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.content || 'I could not process that request.',
        citations: data.citations,
        timestamp: new Date(),
        downloadable: data.downloadable,
        provider: data.provider,
        model: data.model,
      };
      setMessages((prev) => [...prev.filter((m) => !m.pending), aiMsg]);
    } catch {
      const errorMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, there was an error reaching the AI. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev.filter((m) => !m.pending), errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions: string[] = AGENT_SUGGESTIONS[mode] ?? DEFAULT_SUGGESTIONS;
  const heading: { title: string; subtitle: string } = AGENT_HEADINGS[mode] ?? DEFAULT_HEADING;

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center px-6 py-8">
            <div className="mb-10 text-center">
              <div
                className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl text-2xl text-white"
                style={{ background: 'var(--gradient-brand)' }}
                aria-hidden="true"
              >
                ✦
              </div>
              <h2
                className="text-[28px] font-extrabold leading-tight tracking-tight"
                style={{
                  fontFamily: 'Archivo, sans-serif',
                  color: onDark ? 'var(--color-on-dark)' : 'var(--color-ink)',
                }}
              >
                {heading.title}
              </h2>
              <p
                className="mt-2 text-[15px]"
                style={{ color: onDark ? 'var(--color-on-dark-soft)' : 'var(--color-muted)' }}
              >
                {heading.subtitle}
              </p>
            </div>

            <div className="w-full max-w-lg">
              <p
                className="mb-3 text-[11px] font-semibold uppercase tracking-widest"
                style={{ color: 'var(--color-accent)', opacity: 0.7 }}
              >
                Suggestions
              </p>
              <div
                className="overflow-hidden rounded-2xl"
                style={{
                  border: onDark
                    ? '1px solid var(--overlay-white-strong)'
                    : '1px solid var(--overlay-ink-strong)',
                }}
              >
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => void send(s)}
                    className="group flex w-full items-center justify-between px-5 py-4 text-left text-[14px] transition-colors"
                    style={{
                      background:
                        i === 0
                          ? onDark
                            ? 'var(--overlay-white)'
                            : 'var(--overlay-accent-soft)'
                          : 'transparent',
                      color: onDark ? 'var(--color-on-dark-strong)' : 'var(--color-ink-secondary)',
                      borderBottom:
                        i < suggestions.length - 1
                          ? onDark
                            ? '1px solid var(--overlay-white-soft)'
                            : '1px solid var(--overlay-ink)'
                          : 'none',
                    }}
                  >
                    <span>{s}</span>
                    <span
                      className="ml-4 shrink-0 text-[16px] opacity-40 transition-opacity group-hover:opacity-80"
                      aria-hidden="true"
                    >
                      →
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-2xl space-y-5">
            <div className="flex justify-end">
              <button
                onClick={clearChat}
                className="rounded-lg px-3 py-1 text-[12px] transition-colors"
                style={{
                  color: onDark ? 'var(--color-on-dark-faint)' : 'var(--color-muted)',
                  background: onDark ? 'var(--overlay-white-faint)' : 'var(--overlay-ink-soft)',
                }}
              >
                New conversation
              </button>
            </div>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="px-4 pb-4 pt-2 sm:px-6">
        <div className="mx-auto max-w-2xl">
          {!hasExternalAgentPicker && (
            <ModePicker
              mode={mode}
              onChange={(next) => {
                setLocalMode(next);
                onAgentChange?.(next);
              }}
              onDark={onDark}
              disabled={loading}
            />
          )}
          {docContext && <DocumentContextChip state={docContext} />}
          <ChatInput
            onSend={send}
            disabled={loading}
            onAttachDocument={onAttachDocument}
            attachedFile={attachedFile}
            onClearDocument={onClearDocument}
            agentMode={agentMode}
            agentOptions={agentOptions}
            onAgentChange={onAgentChange}
            onDark={onDark}
          />
        </div>
      </div>

      <AuthModal
        isOpen={showAuth}
        onClose={() => setShowAuth(false)}
        onSuccess={() => {
          const msg = pendingMsg;
          setPendingMsg('');
          if (msg) void send(msg);
        }}
      />
    </div>
  );
}
