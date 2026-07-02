'use client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from './AssistantThread';

interface Props {
  message: Message;
}

function downloadFile(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function CitationChip({ citation }: { citation: NonNullable<Message['citations']>[number] }) {
  const icons = { document: '📄', rule: '§', section: '⊞' } as const;
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-accent/20 bg-accent/6 px-2.5 py-0.5 text-[11px] font-medium text-accent/80">
      <span aria-hidden="true">{icons[citation.type]}</span>
      {citation.label}
      {citation.page != null ? ` · p.${citation.page}` : ''}
    </span>
  );
}

function TypingIndicator({ label }: { label?: string }) {
  return (
    <div className="flex flex-col gap-2 py-1">
      <div
        className="flex items-center gap-3 rounded-2xl bg-white px-5 py-4 shadow-[var(--shadow-bubble)]"
        role="status"
        aria-label={label ?? 'Verra is thinking'}
      >
        <span className="flex gap-1" aria-hidden="true">
          <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-accent [animation-delay:0ms]" />
          <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-accent [animation-delay:150ms]" />
          <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-accent [animation-delay:300ms]" />
        </span>
        {label && <span className="text-[13px] text-muted">{label}</span>}
      </div>
    </div>
  );
}

const MD: React.ComponentProps<typeof ReactMarkdown>['components'] = {
  table: ({ ...props }) => (
    <div className="my-3 overflow-x-auto rounded-xl border border-line">
      <table className="min-w-full border-collapse text-[14px]" {...props} />
    </div>
  ),
  thead: ({ ...props }) => <thead className="bg-cream" {...props} />,
  th: ({ ...props }) => (
    <th
      className="border-b border-line px-4 py-2.5 text-left text-xs font-semibold text-ink-secondary"
      {...props}
    />
  ),
  td: ({ ...props }) => (
    <td
      className="border-b border-line/60 px-4 py-2.5 text-[13px] text-ink-secondary last:border-b-0"
      {...props}
    />
  ),
  tr: ({ ...props }) => <tr className="even:bg-cream/50" {...props} />,
  p: ({ ...props }) => (
    <p className="mb-2.5 last:mb-0 text-[15px] leading-relaxed text-ink" {...props} />
  ),
  strong: ({ ...props }) => <strong className="font-semibold text-ink" {...props} />,
  ul: ({ ...props }) => (
    <ul className="mb-2.5 ml-4 list-disc space-y-1 text-[15px] text-ink-secondary" {...props} />
  ),
  ol: ({ ...props }) => (
    <ol className="mb-2.5 ml-4 list-decimal space-y-1 text-[15px] text-ink-secondary" {...props} />
  ),
  li: ({ ...props }) => <li className="text-[14px] text-ink-secondary" {...props} />,
  h1: ({ ...props }) => (
    <h1
      className="mb-3 text-[17px] font-bold text-ink"
      style={{ fontFamily: 'Archivo, sans-serif' }}
      {...props}
    />
  ),
  h2: ({ ...props }) => <h2 className="mb-2 mt-4 text-[15px] font-semibold text-ink" {...props} />,
  h3: ({ ...props }) => (
    <h3
      className="mb-1.5 mt-3 text-[12px] font-semibold uppercase tracking-widest text-muted"
      {...props}
    />
  ),
  blockquote: ({ ...props }) => (
    <blockquote
      className="my-2 border-l-4 border-accent/30 pl-4 text-[14px] italic text-muted"
      {...props}
    />
  ),
  code: ({ className, children, ...props }) => {
    const isBlock = !!className?.includes('language-');
    return isBlock ? (
      <code
        className="block w-full overflow-x-auto rounded-lg bg-ink p-4 font-mono text-[13px] text-cream"
        {...props}
      >
        {children}
      </code>
    ) : (
      <code className="rounded bg-cream px-1.5 py-0.5 font-mono text-[13px] text-accent" {...props}>
        {children}
      </code>
    );
  },
  pre: ({ ...props }) => <pre className="my-3 overflow-x-auto rounded-xl bg-ink" {...props} />,
};

function Timestamp({ message }: { message: Message }) {
  const showProvider = message.provider && message.provider !== 'unconfigured';
  return (
    <p className="pl-1 text-[11px] text-muted">
      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      {showProvider && (
        <span>
          {' · '}
          {message.provider}
          {message.model ? ` · ${message.model}` : ''}
        </span>
      )}
    </p>
  );
}

/** System notice for provider-configuration errors — visually distinct from a normal reply. */
function SystemNotice({ message }: { message: Message }) {
  return (
    <div className="flex flex-col gap-1">
      <div
        className="rounded-2xl rounded-tl-md border border-warn/40 bg-warn/10 px-5 py-4"
        role="status"
      >
        <div className="mb-2 flex items-center gap-2">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="shrink-0 text-warn"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
            />
          </svg>
          <span className="text-[12px] font-semibold uppercase tracking-widest text-warn">
            Configuration required
          </span>
        </div>
        <div className="text-ink-secondary">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
      <Timestamp message={message} />
    </div>
  );
}

export function MessageBubble({ message }: Props) {
  if (message.pending) return <TypingIndicator label={message.pendingLabel} />;

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-[85%] rounded-2xl rounded-tr-md px-5 py-3.5 text-[15px] leading-relaxed text-white"
          style={{ background: 'var(--gradient-brand)' }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  if (message.provider === 'unconfigured') return <SystemNotice message={message} />;

  return (
    <div className="flex flex-col gap-1">
      <div className="rounded-2xl rounded-tl-md bg-white px-5 py-4 shadow-[var(--shadow-bubble)]">
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>
          {message.content}
        </ReactMarkdown>

        {message.downloadable && (
          <div className="mt-3 border-t border-line pt-3">
            <button
              onClick={() =>
                downloadFile(
                  message.downloadable!.filename,
                  message.downloadable!.content,
                  message.downloadable!.mimeType,
                )
              }
              className="inline-flex items-center gap-2 rounded-lg border border-accent/25 bg-accent/6 px-3.5 py-2 text-[13px] font-medium text-accent transition-colors hover:bg-accent/12"
            >
              📥 Download {message.downloadable.filename}
            </button>
          </div>
        )}

        {message.citations && message.citations.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5 border-t border-line pt-3">
            {message.citations.map((c, i) => (
              <CitationChip key={i} citation={c} />
            ))}
          </div>
        )}
      </div>

      <Timestamp message={message} />
    </div>
  );
}
