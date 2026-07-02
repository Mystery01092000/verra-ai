'use client';

import { CitedAmount, type Citation } from './CitedAmount';
import { ruleCitation, type TaxComputation } from './tax-data';

interface RowProps {
  label: string;
  amount: number;
  citation?: Citation;
}

function Row({ label, amount, citation }: RowProps) {
  return (
    <li className="flex items-center justify-between gap-4">
      <span>{label}</span>
      <CitedAmount amount={amount} citation={citation} />
    </li>
  );
}

export interface ComputationCardProps {
  computation: TaxComputation;
}

export function ComputationCard({ computation }: ComputationCardProps) {
  const c = computation;
  const refundDue = c.netTaxRefundDue < 0;

  return (
    <div className="rounded-card border border-periwinkle-soft bg-white p-4 shadow-card">
      <h3 className="text-lg font-semibold text-ink">Tax Computation</h3>
      <ul className="mt-3 space-y-2 text-sm text-ink-secondary">
        <Row
          label="Total deductions"
          amount={c.totalDeductions}
          citation={ruleCitation(c.citations, '16(ia)')}
        />
        <Row
          label="Tax before rebate"
          amount={c.taxBeforeRebate}
          citation={ruleCitation(c.citations, 'slabs')}
        />
        <Row
          label="Rebate u/s 87A"
          amount={c.rebate87a}
          citation={ruleCitation(c.citations, 'rebate_87a')}
        />
        <Row label="Surcharge" amount={c.surcharge} citation={ruleCitation(c.citations, 'slabs')} />
        <Row
          label="Health &amp; Education Cess (4%)"
          amount={c.cess}
          citation={ruleCitation(c.citations, 'cess')}
        />
        <li className="flex items-center justify-between gap-4 border-t border-line pt-2 font-semibold text-ink">
          <span>Total tax</span>
          <CitedAmount amount={c.totalTax} citation={ruleCitation(c.citations, 'slabs')} />
        </li>
        <li className="flex items-center justify-between gap-4">
          <span>{refundDue ? 'Refund due' : 'Net payable'}</span>
          <span className={refundDue ? 'text-ok' : undefined}>
            <CitedAmount
              amount={Math.abs(c.netTaxRefundDue)}
              citation={ruleCitation(c.citations, 'slabs')}
            />
          </span>
        </li>
        <li className="flex items-center justify-between gap-4 text-xs text-muted">
          <span>Effective tax rate (derived from figures above)</span>
          <span>{(c.effectiveTaxRate * 100).toFixed(1)}%</span>
        </li>
      </ul>
    </div>
  );
}
