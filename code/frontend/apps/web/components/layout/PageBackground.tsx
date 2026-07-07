'use client';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';

const ALL_BG = [
  'bg-page-home',
  'bg-page-tax',
  'bg-page-holdings',
  'bg-page-documents',
  'bg-page-audit',
  'bg-page-approvals',
];

function bgForPath(path: string): string {
  if (path === '/' || path.startsWith('/chat')) return 'bg-page-home';
  if (path.startsWith('/tax')) return 'bg-page-tax';
  if (path.startsWith('/holdings')) return 'bg-page-holdings';
  if (path.startsWith('/documents')) return 'bg-page-documents';
  if (path.startsWith('/audit')) return 'bg-page-audit';
  if (path.startsWith('/approvals')) return 'bg-page-approvals';
  return '';
}

export function PageBackground() {
  const path = usePathname();

  useEffect(() => {
    const el = document.documentElement;
    ALL_BG.forEach((c) => el.classList.remove(c));
    const cls = bgForPath(path);
    if (cls) el.classList.add(cls);
  }, [path]);

  return null;
}
