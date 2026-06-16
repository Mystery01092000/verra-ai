export const metadata = { title: 'Verra', description: 'AI engine for accounting, tax, audit & compliance' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body>{children}</body></html>);
}
