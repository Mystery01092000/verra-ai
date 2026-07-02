'use client';
import { useState, useRef, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { AuthModal } from './AuthModal';

interface UserButtonProps {
  onDark?: boolean;
}

export function UserButton({ onDark = false }: UserButtonProps) {
  const { data: session, status } = useSession();
  const [showAuth, setShowAuth] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  if (status === 'loading') return null;

  if (!session) {
    const btnCls = onDark
      ? 'rounded-full border border-white/40 px-4 py-1.5 text-sm font-medium text-white hover:bg-white/15 transition-all'
      : 'rounded-full border border-line px-4 py-1.5 text-sm font-medium text-ink-secondary hover:border-accent hover:text-accent transition-all';
    return (
      <>
        <button onClick={() => setShowAuth(true)} className={btnCls}>
          Sign in
        </button>
        <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
      </>
    );
  }

  const initials = (session.user?.name ?? 'U')
    .split(' ')
    .map((n) => n[0] ?? '')
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setShowMenu((v) => !v)}
        className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-white focus:outline-none focus:ring-2 focus:ring-accent/40"
        style={{ background: 'var(--gradient-brand)' }}
        title={session.user?.name ?? ''}
      >
        {initials}
      </button>
      {showMenu && (
        <div className="absolute right-0 top-10 z-[60] w-52 rounded-[14px] bg-white p-2 shadow-[0_8px_30px_rgba(17,17,20,0.14)]">
          <div className="px-3 pb-2 pt-1">
            <p className="truncate text-sm font-semibold text-ink">{session.user?.name}</p>
            <p className="truncate text-xs text-muted">{session.user?.email}</p>
          </div>
          <hr className="border-line" />
          <button
            onClick={() => signOut({ callbackUrl: '/' })}
            className="mt-1 w-full rounded-[8px] px-3 py-2 text-left text-xs text-danger hover:bg-danger/8 transition-colors"
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
