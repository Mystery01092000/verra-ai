'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export interface TaxNavHeaderProps {
  assessmentYear: string;
  sourceStatus?: 'live' | 'sample' | 'computing';
}

export function TaxNavHeader({ assessmentYear, sourceStatus = 'live' }: TaxNavHeaderProps) {
  const pathname = usePathname();
  const isScenario = pathname.includes('/scenario');

  return (
    <div className="border-b border-line bg-white/75 px-6 py-3.5 backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Left: Module title and AY pill */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-btn bg-accent/10 font-display font-black text-accent">
              ⊞
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-display text-base font-black tracking-tight text-ink">
                  Tax Module
                </h1>
                <span className="rounded-full border border-periwinkle-soft bg-accent/5 px-2.5 py-0.5 text-[11px] font-semibold text-accent">
                  AY {assessmentYear}
                </span>
                <span className="hidden rounded-full bg-cream px-2 py-0.5 text-[10px] font-medium text-ink-secondary sm:inline-block">
                  Finance Act 2024
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Center: Tabs */}
        <nav
          className="flex items-center rounded-btn border border-line bg-white/80 p-1 shadow-sm"
          aria-label="Tax views"
        >
          <Link
            href={`/tax/${assessmentYear}`}
            className={[
              'flex items-center gap-1.5 rounded-[7px] px-3.5 py-1.5 text-xs font-semibold transition-all',
              !isScenario
                ? 'bg-ink text-white shadow-sm'
                : 'text-ink-secondary hover:bg-cream/80 hover:text-ink',
            ].join(' ')}
          >
            <span>Overview &amp; Filing</span>
          </Link>
          <Link
            href={`/tax/${assessmentYear}/scenario`}
            className={[
              'flex items-center gap-1.5 rounded-[7px] px-3.5 py-1.5 text-xs font-semibold transition-all',
              isScenario
                ? 'bg-ink text-white shadow-sm'
                : 'text-ink-secondary hover:bg-cream/80 hover:text-ink',
            ].join(' ')}
          >
            <span>Scenario Studio</span>
            <span
              className={[
                'rounded-full px-1.5 py-0.2 text-[10px] font-bold uppercase tracking-wider',
                isScenario ? 'bg-periwinkle text-ink' : 'bg-accent/15 text-accent',
              ].join(' ')}
            >
              New
            </span>
          </Link>
        </nav>

        {/* Right: Engine Status Indicator */}
        <div className="flex items-center gap-2">
          {sourceStatus === 'live' && (
            <span className="flex items-center gap-1.5 rounded-full bg-ok/10 px-3 py-1 text-xs font-semibold text-ok">
              <span className="h-1.5 w-1.5 rounded-full bg-ok animate-pulse" />
              Deterministic Engine · Cited
            </span>
          )}
          {sourceStatus === 'sample' && (
            <span className="flex items-center gap-1.5 rounded-full bg-warn/10 px-3 py-1 text-xs font-semibold text-warn">
              <span className="h-1.5 w-1.5 rounded-full bg-warn" />
              Client Fallback Active
            </span>
          )}
          {sourceStatus === 'computing' && (
            <span className="flex items-center gap-1.5 rounded-full bg-cream px-3 py-1 text-xs font-semibold text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-muted animate-ping" />
              Recomputing...
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
