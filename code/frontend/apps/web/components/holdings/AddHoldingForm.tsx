'use client';
import { useState } from 'react';
import type { HoldingType } from './holdings-shared';
import { TYPE_GROUPS, fieldsForType, isLoanType, type HoldingFieldDef } from './holding-fields';

interface AddHoldingFormProps {
  onAdd: (payload: Record<string, unknown>) => Promise<string | null>;
}

const INPUT_CLASS =
  'w-full rounded-btn border border-line bg-white px-3 py-2 text-sm text-ink placeholder:text-muted focus:border-accent focus:outline-none';

function buildFieldValue(def: HoldingFieldDef, raw: string): number | string | undefined {
  const trimmed = raw.trim();
  if (trimmed === '') return undefined;
  if (def.kind === 'date') return trimmed;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
}

export function AddHoldingForm({ onAdd }: AddHoldingFormProps) {
  const [type, setType] = useState<HoldingType>('mutual_fund');
  const [name, setName] = useState('');
  const [institution, setInstitution] = useState('');
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const fields = fieldsForType(type);

  function handleTypeChange(next: HoldingType) {
    setType(next);
    setFieldValues({});
    setError(null);
    setSaved(false);
  }

  function setField(key: string, value: string) {
    setFieldValues((prev) => ({ ...prev, [key]: value }));
  }

  function validate(): string | null {
    if (!name.trim()) return 'Give this holding a name.';
    for (const def of fields) {
      if (!def.required) continue;
      const raw = fieldValues[def.key] ?? '';
      if (buildFieldValue(def, raw) === undefined) {
        return `${def.label} is required and must be a non-negative number.`;
      }
    }
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaved(false);
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    const payload: Record<string, unknown> = {
      type,
      name: name.trim(),
      currency: 'INR',
      ...(institution.trim() ? { institution: institution.trim() } : {}),
    };
    for (const def of fields) {
      const value = buildFieldValue(def, fieldValues[def.key] ?? '');
      if (value !== undefined) payload[def.key] = value;
    }
    // Loans and pure-cover insurance may have no market value of their own.
    if (payload.currentValue === undefined && isLoanType(type)) payload.currentValue = 0;

    setSubmitting(true);
    setError(null);
    const submitError = await onAdd(payload);
    setSubmitting(false);
    if (submitError) {
      setError(submitError);
      return;
    }
    setName('');
    setInstitution('');
    setFieldValues({});
    setSaved(true);
  }

  return (
    <form
      onSubmit={(e) => void handleSubmit(e)}
      className="rounded-card border border-line bg-white p-5 shadow-card"
      aria-label="Add a holding"
    >
      <h3 className="text-sm font-semibold text-ink">Add a holding</h3>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label
            htmlFor="holding-type"
            className="mb-1 block text-xs font-medium text-ink-secondary"
          >
            Type
          </label>
          <select
            id="holding-type"
            value={type}
            onChange={(e) => handleTypeChange(e.target.value as HoldingType)}
            className={INPUT_CLASS}
          >
            {TYPE_GROUPS.map((group) => (
              <optgroup key={group.label} label={group.label}>
                {group.options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        <div>
          <label
            htmlFor="holding-name"
            className="mb-1 block text-xs font-medium text-ink-secondary"
          >
            Name
          </label>
          <input
            id="holding-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Nifty 50 Index Fund"
            className={INPUT_CLASS}
            required
          />
        </div>

        <div>
          <label
            htmlFor="holding-institution"
            className="mb-1 block text-xs font-medium text-ink-secondary"
          >
            Institution (optional)
          </label>
          <input
            id="holding-institution"
            value={institution}
            onChange={(e) => setInstitution(e.target.value)}
            placeholder="e.g. HDFC, SBI, Zerodha"
            className={INPUT_CLASS}
          />
        </div>

        {fields.map((def) => (
          <div key={def.key}>
            <label
              htmlFor={`holding-${def.key}`}
              className="mb-1 block text-xs font-medium text-ink-secondary"
            >
              {def.label}
              {def.required ? ' *' : ''}
            </label>
            <input
              id={`holding-${def.key}`}
              type={def.kind === 'date' ? 'date' : 'number'}
              min={0}
              step={def.kind === 'percent' ? '0.01' : '1'}
              inputMode={def.kind === 'date' ? undefined : 'decimal'}
              value={fieldValues[def.key] ?? ''}
              onChange={(e) => setField(def.key, e.target.value)}
              placeholder={def.kind === 'money' ? '₹ amount' : undefined}
              className={INPUT_CLASS}
            />
          </div>
        ))}
      </div>

      {error && (
        <p role="alert" className="mt-3 text-sm" style={{ color: 'var(--color-danger)' }}>
          {error}
        </p>
      )}
      {saved && !error && (
        <p role="status" className="mt-3 text-sm" style={{ color: 'var(--color-ok)' }}>
          Holding saved.
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="mt-4 rounded-btn px-5 py-2 text-sm font-medium text-white transition-opacity hover:opacity-85 disabled:opacity-40"
        style={{ background: 'var(--gradient-brand)' }}
      >
        {submitting ? 'Saving…' : 'Add holding'}
      </button>
    </form>
  );
}
