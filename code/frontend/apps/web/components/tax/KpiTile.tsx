import { CitedAmount, type Citation } from './CitedAmount';

export interface KpiTileProps {
  title: string;
  amount: number;
  currency?: string;
  caption?: string;
  citation?: Citation;
  confidence?: number;
  tone?: 'neutral' | 'positive' | 'negative';
}

const TONE_STYLES: Record<NonNullable<KpiTileProps['tone']>, { bg: string; valueColor: string }> = {
  neutral: { bg: '#F5F5F5', valueColor: '#111114' },
  positive: { bg: 'rgba(31,191,117,0.07)', valueColor: '#0d8f57' },
  negative: { bg: 'rgba(229,72,77,0.07)', valueColor: '#e5484d' },
};

export function KpiTile({
  title,
  amount,
  currency = 'INR',
  caption,
  citation,
  confidence,
  tone = 'neutral',
}: KpiTileProps) {
  const { bg, valueColor } = TONE_STYLES[tone];
  return (
    <div className="rounded-xl p-4" style={{ background: bg }}>
      <div className="text-[11.5px] font-semibold uppercase tracking-wide text-muted">{title}</div>
      <div
        className="mt-1 leading-tight tracking-tight"
        style={{
          fontFamily: 'Archivo, sans-serif',
          fontWeight: 800,
          fontSize: 24,
          color: valueColor,
        }}
      >
        <CitedAmount
          amount={amount}
          currency={currency}
          citation={citation}
          confidence={confidence}
        />
      </div>
      {caption && <div className="mt-1 text-xs text-muted">{caption}</div>}
    </div>
  );
}
