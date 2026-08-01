'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';

const NAV = [
  { href: '/',         label: 'Dashboard',  icon: '⬡' },
  { href: '/datasets', label: 'Datasets',   icon: '◈' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: rawDatasets } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets });

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname?.startsWith(href) ?? false;

  // Deduplicate datasets by ID
  const datasets = rawDatasets ? Array.from(new Map(rawDatasets.map(d => [d.id, d])).values()) : [];

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="mb-8 px-1">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg shadow-sm" style={{ background: 'linear-gradient(135deg,#0284c7,#6366f1)' }}>
            <span className="text-xs font-bold text-white">IF</span>
          </div>
          <div>
            <p className="text-sm font-bold leading-none text-white">InsightForge</p>
            <p className="mt-0.5 text-xs" style={{ color: 'var(--text-faint)' }}>AI Data Analyst</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="space-y-1">
        <p className="label mb-2 px-3">Navigation</p>
        {NAV.map(({ href, label, icon }) => (
          <Link
            key={href}
            href={href}
            className={`nav-link ${isActive(href) ? 'active' : ''}`}
          >
            <span className="text-base leading-none">{icon}</span>
            {label}
          </Link>
        ))}
      </nav>

      {/* Datasets list */}
      {datasets && datasets.length > 0 && (
        <div className="mt-6">
          <p className="label mb-2 px-3">Datasets</p>
          <div className="space-y-1">
            {datasets.map(d => (
              <div key={d.id} className="space-y-0.5">
                <Link
                  href={`/analyse/${d.id}`}
                  className={`nav-link text-xs ${pathname === `/analyse/${d.id}` ? 'active' : ''}`}
                >
                  <span className="text-sm">▸</span>
                  <span className="truncate">{d.name.replace(/\.csv$/i, '')}</span>
                </Link>
                <Link
                  href={`/explore/${d.id}`}
                  className={`nav-link ml-4 text-xs ${pathname === `/explore/${d.id}` ? 'active' : ''}`}
                >
                  <span className="text-xs opacity-50">⊞</span>
                  <span className="text-xs opacity-70">Explorer</span>
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-auto pt-6">
        <div className="rounded-xl p-3" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
          <p className="text-xs font-semibold" style={{ color: 'var(--accent-cyan)' }}>Powered by Gemini</p>
          <p className="mt-0.5 text-xs" style={{ color: 'var(--text-faint)' }}>gemini-2.5-flash</p>
        </div>
      </div>
    </aside>
  );
}
