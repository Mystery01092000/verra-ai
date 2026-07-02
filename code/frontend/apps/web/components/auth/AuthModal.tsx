'use client';
import { useState } from 'react';
import { signIn } from 'next-auth/react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

type Tab = 'login' | 'register';

export function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
  const [tab, setTab] = useState<Tab>('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  // Login fields
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  // Register fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [age, setAge] = useState('');
  const [password, setPassword] = useState('');

  if (!isOpen) return null;

  const inputCls =
    'w-full rounded-[10px] border border-line bg-cream px-4 py-3 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-[rgba(85,102,255,0.15)] transition-all';
  const labelCls = 'block mb-1 text-xs font-medium text-ink-secondary';

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    const res = await signIn('credentials', {
      email: loginEmail,
      password: loginPassword,
      redirect: false,
    });
    setLoading(false);
    if (res?.ok) {
      onSuccess?.();
      onClose();
    } else {
      setError('Invalid email or password.');
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, phone, age: Number(age), password }),
      });
      const data = (await res.json()) as { error?: string };
      if (!res.ok) {
        setError(data.error ?? 'Registration failed');
        setLoading(false);
        return;
      }
      // Auto sign-in after registration
      const signInRes = await signIn('credentials', { email, password, redirect: false });
      setLoading(false);
      if (signInRes?.ok) {
        onSuccess?.();
        onClose();
      } else {
        setError('Registered! Please sign in.');
      }
    } catch {
      setLoading(false);
      setError('Network error. Try again.');
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[12vh]">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-[420px] overflow-hidden rounded-[22px] bg-white shadow-[0_32px_80px_rgba(17,17,20,0.22)]">
        {/* Header */}
        <div className="px-8 pb-6 pt-8 text-center">
          <div
            className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full text-xl text-white"
            style={{ background: 'var(--gradient-brand)' }}
          >
            ✦
          </div>
          <h2
            style={{
              fontFamily: 'Archivo, sans-serif',
              fontWeight: 800,
              fontSize: 22,
              color: 'var(--color-ink)',
            }}
          >
            {tab === 'login' ? 'Welcome back' : 'Create your account'}
          </h2>
          <p className="mt-1 text-sm text-muted">
            {tab === 'login' ? 'Sign in to your Verra account.' : 'Join Verra — no OTP required.'}
          </p>
        </div>

        {/* Tabs */}
        <div className="mx-8 mb-6 flex rounded-[12px] bg-cream p-1">
          {(['login', 'register'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => {
                setTab(t);
                setError('');
              }}
              className={`flex-1 rounded-[9px] py-2 text-sm font-medium transition-all ${
                tab === t ? 'bg-white text-ink shadow-sm' : 'text-muted hover:text-ink'
              }`}
            >
              {t === 'login' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>

        <div className="px-8 pb-8">
          {tab === 'login' ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className={labelCls}>Email</label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="you@example.com"
                  className={inputCls}
                  required
                />
              </div>
              <div>
                <label className={labelCls}>Password</label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••"
                  className={inputCls}
                  required
                />
              </div>
              {error && (
                <p className="rounded-[8px] bg-danger/10 px-3 py-2 text-xs text-danger">{error}</p>
              )}
              <button
                type="submit"
                disabled={loading}
                className="mt-2 w-full rounded-[10px] py-3 text-sm font-semibold text-white transition-opacity disabled:opacity-60"
                style={{ background: 'var(--gradient-brand)' }}
              >
                {loading ? 'Signing in…' : 'Sign in'}
              </button>
              <p className="text-center text-xs text-muted">Demo: demo@verra.ai / demo123</p>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-3">
              <div>
                <label className={labelCls}>Full name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Arjun Sharma"
                  className={inputCls}
                  required
                />
              </div>
              <div>
                <label className={labelCls}>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className={inputCls}
                  required
                />
              </div>
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className={labelCls}>Phone number</label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="9876543210"
                    className={inputCls}
                    required
                  />
                </div>
                <div className="w-24">
                  <label className={labelCls}>Age</label>
                  <input
                    type="number"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    placeholder="28"
                    min="18"
                    max="120"
                    className={inputCls}
                    required
                  />
                </div>
              </div>
              <div>
                <label className={labelCls}>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a password"
                  className={inputCls}
                  required
                  minLength={6}
                />
              </div>
              {error && (
                <p className="rounded-[8px] bg-danger/10 px-3 py-2 text-xs text-danger">{error}</p>
              )}
              <button
                type="submit"
                disabled={loading}
                className="mt-2 w-full rounded-[10px] py-3 text-sm font-semibold text-white transition-opacity disabled:opacity-60"
                style={{ background: 'var(--gradient-brand)' }}
              >
                {loading ? 'Creating account…' : 'Create account'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
