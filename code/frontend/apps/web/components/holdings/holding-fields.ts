/**
 * UI metadata for holding types: grouped select options, category
 * grouping for the list/dashboard, dynamic form fields per type, and
 * money formatting helpers.
 */
import type { HoldingType } from './holdings-shared';

export interface TypeOption {
  value: HoldingType;
  label: string;
}

export interface TypeGroup {
  label: string;
  options: TypeOption[];
}

export const TYPE_GROUPS: TypeGroup[] = [
  {
    label: 'Investments',
    options: [
      { value: 'mutual_fund', label: 'Mutual fund' },
      { value: 'stock', label: 'Stock' },
      { value: 'bond', label: 'Bond' },
      { value: 'real_estate', label: 'Real estate' },
      { value: 'gold', label: 'Gold' },
    ],
  },
  {
    label: 'Deposits & retirement',
    options: [
      { value: 'fixed_deposit', label: 'Fixed deposit' },
      { value: 'recurring_deposit', label: 'Recurring deposit' },
      { value: 'ppf', label: 'PPF' },
      { value: 'epf', label: 'EPF' },
      { value: 'nps', label: 'NPS' },
    ],
  },
  {
    label: 'Insurance',
    options: [
      { value: 'insurance_life', label: 'Life insurance' },
      { value: 'insurance_health', label: 'Health insurance' },
      { value: 'insurance_ulip', label: 'ULIP' },
    ],
  },
  {
    label: 'Loans',
    options: [
      { value: 'loan_home', label: 'Home loan' },
      { value: 'loan_personal', label: 'Personal loan' },
      { value: 'loan_vehicle', label: 'Vehicle loan' },
      { value: 'loan_education', label: 'Education loan' },
    ],
  },
  {
    label: 'Other',
    options: [
      { value: 'cash', label: 'Cash / savings' },
      { value: 'other', label: 'Other' },
    ],
  },
];

const TYPE_LABELS: Record<string, string> = Object.fromEntries(
  TYPE_GROUPS.flatMap((g) => g.options.map((o) => [o.value, o.label])),
);

const TYPE_CATEGORIES: Record<string, string> = Object.fromEntries(
  TYPE_GROUPS.flatMap((g) => g.options.map((o) => [o.value, g.label])),
);

export const CATEGORY_ORDER: string[] = TYPE_GROUPS.map((g) => g.label);

export function typeLabel(type: string): string {
  return TYPE_LABELS[type] ?? type.replace(/_/g, ' ');
}

export function categoryForType(type: string): string {
  return TYPE_CATEGORIES[type] ?? 'Other';
}

export function isLoanType(type: string): boolean {
  return type.startsWith('loan_');
}

export function isInsuranceType(type: string): boolean {
  return type.startsWith('insurance_');
}

// ── Dynamic form fields per type ─────────────────────────────────────

export type FieldKind = 'money' | 'number' | 'percent' | 'date';

export interface HoldingFieldDef {
  key:
    | 'currentValue'
    | 'investedValue'
    | 'units'
    | 'premiumAnnual'
    | 'sumAssured'
    | 'outstandingAmount'
    | 'interestRate'
    | 'emi'
    | 'maturityDate';
  label: string;
  kind: FieldKind;
  required?: boolean;
}

const CURRENT_VALUE: HoldingFieldDef = {
  key: 'currentValue',
  label: 'Current value',
  kind: 'money',
  required: true,
};
const INVESTED_VALUE: HoldingFieldDef = {
  key: 'investedValue',
  label: 'Invested amount',
  kind: 'money',
};
const UNITS: HoldingFieldDef = { key: 'units', label: 'Units', kind: 'number' };
const INTEREST_RATE: HoldingFieldDef = {
  key: 'interestRate',
  label: 'Interest rate (%)',
  kind: 'percent',
};
const MATURITY_DATE: HoldingFieldDef = {
  key: 'maturityDate',
  label: 'Maturity date',
  kind: 'date',
};

const INSURANCE_FIELDS: HoldingFieldDef[] = [
  { key: 'sumAssured', label: 'Sum assured', kind: 'money', required: true },
  { key: 'premiumAnnual', label: 'Annual premium', kind: 'money', required: true },
  { key: 'currentValue', label: 'Current / surrender value', kind: 'money' },
];

const LOAN_FIELDS: HoldingFieldDef[] = [
  { key: 'outstandingAmount', label: 'Outstanding amount', kind: 'money', required: true },
  { key: 'emi', label: 'Monthly EMI', kind: 'money' },
  INTEREST_RATE,
  MATURITY_DATE,
];

const FIELDS_BY_TYPE: Record<HoldingType, HoldingFieldDef[]> = {
  mutual_fund: [CURRENT_VALUE, INVESTED_VALUE, UNITS],
  stock: [CURRENT_VALUE, INVESTED_VALUE, UNITS],
  bond: [CURRENT_VALUE, INVESTED_VALUE, INTEREST_RATE, MATURITY_DATE],
  fixed_deposit: [CURRENT_VALUE, INVESTED_VALUE, INTEREST_RATE, MATURITY_DATE],
  recurring_deposit: [CURRENT_VALUE, INVESTED_VALUE, INTEREST_RATE, MATURITY_DATE],
  ppf: [CURRENT_VALUE, INVESTED_VALUE, MATURITY_DATE],
  epf: [CURRENT_VALUE, INVESTED_VALUE],
  nps: [CURRENT_VALUE, INVESTED_VALUE],
  insurance_life: INSURANCE_FIELDS,
  insurance_health: INSURANCE_FIELDS,
  insurance_ulip: INSURANCE_FIELDS,
  loan_home: LOAN_FIELDS,
  loan_personal: LOAN_FIELDS,
  loan_vehicle: LOAN_FIELDS,
  loan_education: LOAN_FIELDS,
  real_estate: [CURRENT_VALUE, INVESTED_VALUE],
  gold: [CURRENT_VALUE, INVESTED_VALUE, UNITS],
  cash: [CURRENT_VALUE],
  other: [CURRENT_VALUE, INVESTED_VALUE],
};

export function fieldsForType(type: HoldingType): HoldingFieldDef[] {
  return FIELDS_BY_TYPE[type] ?? [CURRENT_VALUE];
}

// ── Money formatting ─────────────────────────────────────────────────

export function formatMoney(amount: number, currency = 'INR'): string {
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${currency} ${Math.round(amount).toLocaleString('en-IN')}`;
  }
}

export function formatPercent(value: number): string {
  return `${value.toFixed(value >= 10 ? 0 : 1)}%`;
}
