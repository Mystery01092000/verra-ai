import type { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { findUserByEmail, validatePassword } from './users-store';

const DEV_FALLBACK_SECRET = 'verra-dev-secret-change-in-production';

/**
 * Resolve the NextAuth secret. Throws at startup in production when
 * NEXTAUTH_SECRET is missing; warns loudly and falls back in development.
 * (The `next build` phase is exempt so CI builds do not require secrets.)
 */
function resolveAuthSecret(): string {
  const secret = process.env.NEXTAUTH_SECRET;
  if (secret) return secret;

  const isBuildPhase = process.env.NEXT_PHASE === 'phase-production-build';
  if (process.env.NODE_ENV === 'production' && !isBuildPhase) {
    throw new Error(
      'NEXTAUTH_SECRET is required in production. Generate one with `openssl rand -base64 32` ' +
        'and set it in the environment (see apps/web/.env.example).',
    );
  }

  console.warn(
    '[Verra auth] WARNING: NEXTAUTH_SECRET is not set — using an INSECURE development fallback. ' +
      'Set NEXTAUTH_SECRET in apps/web/.env.local (see .env.example).',
  );
  return DEV_FALLBACK_SECRET;
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        const user = findUserByEmail(credentials.email);
        if (!user || !validatePassword(user, credentials.password)) return null;
        return { id: user.id, name: user.name, email: user.email };
      },
    }),
  ],
  session: { strategy: 'jwt' },
  secret: resolveAuthSecret(),
  pages: { signIn: '/' },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.name = user.name;
        token.email = user.email;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.name = token.name;
        session.user.email = token.email as string;
      }
      return session;
    },
  },
};
