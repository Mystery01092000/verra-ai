'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserButton } from '@/components/auth/UserButton';

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

const NAV: NavItem[] = [
  { href: '/', label: 'Home', icon: '⌂' },
  { href: '/tax/2025-26', label: 'Tax', icon: '⊞' },
  { href: '/holdings', label: 'Holdings', icon: '◈' },
  { href: '/documents', label: 'Documents', icon: '⎘' },
  { href: '/audit', label: 'Audit log', icon: '⛓' },
  { href: '/approvals', label: 'Approvals', icon: '✓' },
];

export function Sidebar() {
  const path = usePathname();
  const onDark = path === '/';

  const baseTextColor = onDark ? 'rgba(255,255,255,0.85)' : 'var(--color-ink-secondary)';
  const activeStyle = onDark
    ? { background: 'rgba(255,255,255,0.18)', color: 'var(--color-surface)', fontWeight: 600 }
    : {
        background: 'rgba(255,255,255,0.7)',
        color: 'var(--color-ink)',
        fontWeight: 600,
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      };
  const hoverBg = onDark ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.5)';

  return (
    <aside
      className="relative z-10 flex h-full w-[200px] shrink-0 flex-col"
      style={{ background: 'transparent' }}
    >
      {/* Wordmark */}
      <div className="flex items-center gap-1.5 px-5 py-6">
        <span
          className="text-xl font-black leading-none tracking-[-0.04em]"
          style={
            onDark
              ? { fontFamily: 'Archivo, sans-serif', color: 'var(--color-surface)' }
              : {
                  fontFamily: 'Archivo, sans-serif',
                  background: 'var(--gradient-brand)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }
          }
        >
          Verra
        </span>
        <span
          style={{
            fontFamily: 'Archivo, sans-serif',
            fontSize: 12,
            color: onDark ? 'rgba(255,255,255,0.5)' : 'var(--color-muted)',
          }}
        >
          ›
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 px-2.5" aria-label="Main navigation">
        {NAV.map(({ href, label, icon }) => {
          const active = path === href || (href !== '/' && path.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className="flex items-center gap-2.5 rounded-[9px] px-3 py-[9px] text-[15px] font-medium transition-all"
              style={active ? activeStyle : { color: baseTextColor }}
              onMouseEnter={(e) => {
                if (!active) (e.currentTarget as HTMLAnchorElement).style.background = hoverBg;
              }}
              onMouseLeave={(e) => {
                if (!active)
                  (e.currentTarget as HTMLAnchorElement).style.background = 'transparent';
              }}
            >
              <span className="text-base" aria-hidden="true">
                {icon}
              </span>
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom CTA */}
      <div className="px-2.5 pb-5">
        <Link
          href="/chat"
          className="flex w-full items-center justify-center gap-2 rounded-[10px] bg-ink px-4 py-2.5 text-sm font-bold text-white transition-all hover:-translate-y-px hover:shadow-[0_8px_20px_rgba(17,17,20,.22)]"
        >
          <span aria-hidden="true">✦</span> Ask Verra
        </Link>
        <div className="mt-3">
          <UserButton onDark={onDark} />
        </div>
        <p
          className="mt-3 text-center text-[10px] font-semibold"
          style={{ color: onDark ? 'rgba(255,255,255,0.45)' : 'var(--color-muted)' }}
        >
          Powered by{' '}
          <b className="font-black" style={{ fontFamily: 'Archivo, sans-serif' }}>
            Verra
          </b>
        </p>
      </div>
    </aside>
  );
}
