import { TaxNavHeader } from '../../../../components/tax/TaxNavHeader';
import { ScenarioBuilder } from '../../../../components/tax/ScenarioBuilder';
import { TaxChatbot } from '../../../../components/tax/TaxChatbot';

export default function TaxScenarioPage({ params }: { params: { year: string } }) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      {/* Subnavigation Bar */}
      <TaxNavHeader assessmentYear={params.year} sourceStatus="live" />

      {/* Main Split Body */}
      <div className="flex flex-1 min-h-0 flex-col lg:flex-row overflow-hidden">
        {/* Left pane — Scenario Modeling Studio */}
        <section
          aria-label="Tax scenario builder"
          className="min-w-0 flex-1 overflow-y-auto px-6 py-6 lg:basis-[58%]"
        >
          <ScenarioBuilder assessmentYear={params.year} />
        </section>

        {/* Right pane — Tax Assistant */}
        <section
          aria-label="Tax assistant"
          className="flex min-h-0 min-w-0 flex-1 flex-col border-t border-line bg-white/70 backdrop-blur-sm lg:basis-[42%] lg:border-l lg:border-t-0"
        >
          <TaxChatbot assessmentYear={params.year} />
        </section>
      </div>
    </div>
  );
}
