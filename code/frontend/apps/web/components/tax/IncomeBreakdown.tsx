import { CitedAmount, type Citation } from './CitedAmount';

export interface IncomeRow {
  head: string;
  amount: number;
  citation?: Citation;
  confidence?: number;
}

export interface IncomeBreakdownProps {
  rows: IncomeRow[];
  total: number;
  currency?: string;
}

export function IncomeBreakdown({ rows, total, currency = 'INR' }: IncomeBreakdownProps) {
  return (
    <div className="rounded-card border border-periwinkle-soft bg-white p-4 shadow-card">
      <h3 className="text-lg font-semibold text-ink">Income Breakdown</h3>
      <table className="mt-3 w-full text-sm">
        <thead>
          <tr className="border-b border-line text-left text-ink-secondary">
            <th className="py-2 font-medium">Head</th>
            <th className="py-2 text-right font-medium">Amount</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.head} className="border-b border-line last:border-0">
              <td className="py-2 capitalize text-ink">{row.head.replace(/_/g, ' ')}</td>
              <td className="py-2 text-right">
                <CitedAmount
                  amount={row.amount}
                  currency={currency}
                  citation={row.citation}
                  confidence={row.confidence}
                />
              </td>
            </tr>
          ))}
          <tr className="font-semibold text-ink">
            <td className="py-2">Gross Total Income</td>
            <td className="py-2 text-right">
              <CitedAmount amount={total} currency={currency} />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
