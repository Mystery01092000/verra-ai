'use client';
import { useRef, useState, useEffect } from 'react';

export interface AgentOption {
  id: string;
  label: string;
  icon: string;
}

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
  onAttachDocument?: () => void;
  attachedFile?: string | null;
  onClearDocument?: () => void;
  agentMode?: string;
  agentOptions?: readonly AgentOption[];
  onAgentChange?: (mode: string) => void;
  onDark?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled,
  onAttachDocument,
  attachedFile,
  onClearDocument,
  agentMode,
  agentOptions,
  onAgentChange,
  placeholder = 'Ask about your taxes, deductions, compliance…',
}: Props) {
  const [value, setValue] = useState('');
  const [showAgentMenu, setShowAgentMenu] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowAgentMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }

  const activeAgent = agentOptions?.find((a) => a.id === agentMode);

  return (
    <div className="relative">
      {attachedFile && (
        <div className="mb-2.5 inline-flex items-center gap-2 rounded-full border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink shadow-sm">
          <span className="text-muted">📄</span>
          <span className="max-w-[200px] truncate">{attachedFile}</span>
          {onClearDocument && (
            <button
              onClick={onClearDocument}
              className="flex h-4 w-4 items-center justify-center rounded-full text-muted transition-colors hover:bg-line hover:text-ink"
              aria-label="Remove file"
            >
              ×
            </button>
          )}
        </div>
      )}

      {/* Main card — no overflow-hidden so the agent dropdown can escape the card */}
      <div className="rounded-2xl bg-white shadow-[var(--shadow-input)]">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          rows={2}
          className="w-full resize-none bg-transparent px-5 pt-4 pb-2 text-[15px] leading-relaxed text-ink placeholder:text-muted focus:outline-none disabled:opacity-50"
          style={{ minHeight: 64, maxHeight: 200 }}
        />

        {/* Toolbar row */}
        <div className="flex items-center gap-2 px-4 pb-3.5 pt-1">
          {onAttachDocument && (
            <button
              type="button"
              onClick={onAttachDocument}
              title="Attach document"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-cream hover:text-ink-secondary"
            >
              <svg
                width="16"
                height="16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                />
              </svg>
            </button>
          )}

          {/* Agent mode chip — only shown when options provided */}
          {agentOptions && agentOptions.length > 0 && (
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setShowAgentMenu((v) => !v)}
                className="flex items-center gap-1.5 rounded-full border border-line bg-cream px-3 py-1.5 text-[13px] font-medium text-ink-secondary transition-colors hover:border-accent/40 hover:bg-accent/5 hover:text-accent"
              >
                <span aria-hidden="true">{activeAgent?.icon ?? '✦'}</span>
                <span>{activeAgent?.label ?? 'Ask Verra'}</span>
                <svg width="10" height="6" viewBox="0 0 10 6" fill="none" aria-hidden="true">
                  <path
                    d="M1 1L5 5L9 1"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>

              {showAgentMenu && (
                <div className="absolute bottom-full left-0 z-50 mb-2 w-52 overflow-hidden rounded-xl border border-line bg-white shadow-[var(--shadow-menu)]">
                  {agentOptions.map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => {
                        onAgentChange?.(opt.id);
                        setShowAgentMenu(false);
                      }}
                      className={[
                        'flex w-full items-center gap-3 px-4 py-3 text-left text-sm transition-colors hover:bg-cream',
                        opt.id === agentMode ? 'text-accent font-medium' : 'text-ink-secondary',
                      ].join(' ')}
                    >
                      <span className="text-base">{opt.icon}</span>
                      <span className="flex-1">{opt.label}</span>
                      {opt.id === agentMode && (
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 14 14"
                          fill="none"
                          aria-hidden="true"
                        >
                          <path
                            d="M2.5 7L5.5 10L11.5 4"
                            stroke="currentColor"
                            strokeWidth="1.75"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="flex-1" />

          {/* Send */}
          <button
            type="button"
            onClick={submit}
            disabled={!value.trim() || disabled}
            aria-label="Send message"
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink text-white transition-all hover:bg-ink-secondary disabled:opacity-25"
          >
            <svg
              width="15"
              height="15"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5M5 12l7-7 7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
