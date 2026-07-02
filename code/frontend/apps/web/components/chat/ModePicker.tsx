'use client';

export interface AssistantMode {
  id: string;
  label: string;
}

export const ASSISTANT_MODES: readonly AssistantMode[] = [
  { id: 'general', label: 'Ask' },
  { id: 'tax-planner', label: 'Tax planner' },
  { id: 'portfolio', label: 'Portfolio' },
  { id: 'nri-tax', label: 'NRI taxes' },
  { id: 'financial-planning', label: 'Financial planning' },
] as const;

interface ModePickerProps {
  mode: string;
  onChange: (mode: string) => void;
  onDark?: boolean;
  disabled?: boolean;
}

/** Compact, calm chip row for switching the assistant's specialisation. */
export function ModePicker({ mode, onChange, onDark = false, disabled = false }: ModePickerProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Assistant mode"
      className="mb-2.5 flex flex-wrap items-center gap-1.5"
    >
      {ASSISTANT_MODES.map((option) => {
        const active = option.id === mode;
        return (
          <button
            key={option.id}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={disabled}
            onClick={() => onChange(option.id)}
            className="rounded-full px-3 py-1 text-[12px] font-medium transition-colors disabled:opacity-50"
            style={
              active
                ? {
                    background: onDark ? 'var(--color-surface)' : 'var(--color-ink)',
                    color: onDark ? 'var(--color-ink)' : 'var(--color-surface)',
                  }
                : {
                    background: onDark ? 'var(--overlay-white)' : 'var(--overlay-ink-soft)',
                    color: onDark ? 'var(--color-on-dark-strong)' : 'var(--color-ink-secondary)',
                    border: onDark
                      ? '1px solid var(--overlay-white-strong)'
                      : '1px solid var(--overlay-ink-strong)',
                  }
            }
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
