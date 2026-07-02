'use client';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';

const ALL_BG = ['bg-page-home', 'bg-page-tax', 'bg-page-documents', 'bg-page-audit'];

function bgForPath(path: string): string {
  if (path === '/' || path.startsWith('/chat')) return 'bg-page-home';
  if (path.startsWith('/tax')) return 'bg-page-tax';
  if (path.startsWith('/documents')) return 'bg-page-documents';
  if (path.startsWith('/audit')) return 'bg-page-audit';
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
