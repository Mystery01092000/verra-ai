import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '../components/layout/Sidebar';
import { PageBackground } from '../components/layout/PageBackground';
import { AuthProvider } from '../components/auth/SessionProvider';

export const metadata: Metadata = {
  title: 'Verra — AI Tax & Compliance',
  description: 'AI engine for accounting, tax, audit & compliance',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="flex h-screen overflow-hidden font-sans">
        <PageBackground />
        <AuthProvider>
          <Sidebar />
          <main className="flex-1 overflow-hidden">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
