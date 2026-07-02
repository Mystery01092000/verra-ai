import type { Metadata } from 'next';
import { HoldingsView } from '@/components/holdings/HoldingsView';

export const metadata: Metadata = {
  title: 'Holdings — Verra',
  description: 'Consolidated net worth across investments, deposits, insurance and loans',
};

export default function HoldingsPage() {
  return <HoldingsView />;
}
