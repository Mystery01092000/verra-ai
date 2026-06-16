import { tokens } from '@verra/design-system';
export default function Home() {
  return (
    <main style={{ fontFamily: 'Inter, sans-serif', padding: 40 }}>
      <h1 style={{ color: tokens.color.ink }}>Verra</h1>
      <p style={{ color: tokens.color.inkSecondary }}>Workspace shell — implement per design/verra-prototype.html.</p>
    </main>
  );
}
