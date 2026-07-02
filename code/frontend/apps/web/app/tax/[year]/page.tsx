import { TaxChatbot } from '../../../components/tax/TaxChatbot';
import { TaxDashboard } from '../../../components/tax/TaxDashboard';

export default function TaxYearPage({ params }: { params: { year: string } }) {
  return (
    <div className="flex h-full min-h-0 flex-col lg:flex-row">
      {/* Left pane — cited, deterministic dashboard */}
      <section
        aria-label="Tax dashboard"
        className="min-w-0 flex-1 overflow-y-auto px-6 py-6 lg:basis-[55%]"
      >
        <TaxDashboard assessmentYear={params.year} />
      </section>

      {/* Right pane — assistant (kept as-is) */}
      <section
        aria-label="Tax assistant"
        className="flex min-h-0 min-w-0 flex-1 flex-col border-t border-line bg-white/70 backdrop-blur-sm lg:basis-[45%] lg:border-l lg:border-t-0"
      >
        <TaxChatbot assessmentYear={params.year} />
      </section>
    </div>
  );
}
