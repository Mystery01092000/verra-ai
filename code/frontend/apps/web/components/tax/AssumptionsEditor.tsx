'use client';

import type { TaxAssumptions } from './tax-data';

export interface AssumptionsEditorProps {
  value: TaxAssumptions;
  onChange: (next: TaxAssumptions) => void;
  disabled?: boolean;
}

interface AmountFieldProps {
  id: string;
  label: string;
  hint: string;
  value: number;
  disabled: boolean;
  onChange: (value: number) => void;
}

function AmountField({ id, label, hint, value, disabled, onChange }: AmountFieldProps) {
  return (
    <div className="min-w-0 flex-1">
      <label htmlFor={id} className="block text-xs font-semibold text-ink-secondary">
        {label}
      </label>
      <div className="mt-1 flex items-center rounded-btn border border-line bg-white focus-within:shadow-glow">
        <span className="pl-3 text-sm text-muted" aria-hidden="true">
          &#8377;
        </span>
        <input
          id={id}
          type="number"
          inputMode="numeric"
          min={0}
          step={5000}
          value={value}
          disabled={disabled}
          onChange={(e) => {
            const next = Number(e.target.value);
            onChange(Number.isFinite(next) && next >= 0 ? next : 0);
          }}
          className="w-full bg-transparent px-2 py-2 text-sm text-ink outline-none disabled:cursor-not-allowed disabled:text-muted"
        />
      </div>
      <p className="mt-1 text-[11px] text-muted">{hint}</p>
    </div>
  );
}

export function AssumptionsEditor({ value, onChange, disabled = false }: AssumptionsEditorProps) {
  const regimes: Array<{ id: TaxAssumptions['regime']; label: string }> = [
    { id: 'new', label: 'New regime' },
    { id: 'old', label: 'Old regime' },
  ];

  return (
    <section
      aria-label="Tax assumptions"
      className="rounded-card border border-periwinkle-soft bg-white p-4 shadow-card"
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-ink">Assumptions</h3>
        <div
          role="radiogroup"
          aria-label="Tax regime"
          className="flex rounded-btn border border-line p-0.5"
        >
          {regimes.map(({ id, label }) => {
            const active = value.regime === id;
            return (
              <button
                key={id}
                type="button"
                role="radio"
                aria-checked={active}
                disabled={disabled}
                onClick={() => onChange({ ...value, regime: id })}
                className={[
                  'rounded-[7px] px-3 py-1 text-xs font-semibold transition-colors disabled:cursor-not-allowed',
                  active
                    ? 'bg-ink text-white'
                    : 'text-ink-secondary hover:bg-cream disabled:hover:bg-transparent',
                ].join(' ')}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-3 flex flex-col gap-3 sm:flex-row">
        <AmountField
          id="assumption-gross-salary"
          label="Gross salary"
          hint="Annual, before exemptions"
          value={value.grossSalary}
          disabled={disabled}
          onChange={(grossSalary) => onChange({ ...value, grossSalary })}
        />
        <AmountField
          id="assumption-80c"
          label="Section 80C"
          hint="PF, ELSS, LIC — old regime only"
          value={value.section80c}
          disabled={disabled}
          onChange={(section80c) => onChange({ ...value, section80c })}
        />
        <AmountField
          id="assumption-80d"
          label="Section 80D"
          hint="Health insurance premium"
          value={value.section80d}
          disabled={disabled}
          onChange={(section80d) => onChange({ ...value, section80d })}
        />
      </div>

      <p className="mt-2 text-[11px] text-muted">
        Standard deduction is applied automatically per regime. Figures recompute live via
        Verra&rsquo;s deterministic calculators &mdash; never estimated by the LLM.
      </p>
    </section>
  );
}
