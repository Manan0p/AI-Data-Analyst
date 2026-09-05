'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api, authStorage, User } from '@/services/api';
import { AuthModal } from './AuthModal';

const NAV = [
  { href: '/',         label: 'Dashboard',  icon: '⬡' },
  { href: '/datasets', label: 'Datasets',   icon: '◈' },
];

export function Sidebar() {
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  useEffect(() => {
    setCurrentUser(authStorage.getUser());
  }, []);

  const { data: datasets } = useQuery({
    queryKey: ['datasets', currentUser?.id],
    queryFn: api.datasets,
    enabled: !!currentUser,
  });

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname?.startsWith(href) ?? false;

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
    queryClient.invalidateQueries({ queryKey: ['datasets'] });
  };

  const handleAuthSuccess = (user: User) => {
    setCurrentUser(user);
    queryClient.invalidateQueries({ queryKey: ['datasets'] });
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="mb-6 px-1">
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

      {/* User Auth Section */}
      <div className="mb-6 p-2.5 rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)]">
        {currentUser ? (
          <div className="flex items-center justify-between">
            <div className="truncate pr-2">
              <p className="text-xs font-semibold text-white truncate">{currentUser.email}</p>
              <p className="text-[10px] text-emerald-400">Authenticated</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-2 py-1 text-[10px] rounded bg-red-950/40 text-red-300 hover:bg-red-900/60 transition-colors"
            >
              Sign out
            </button>
          </div>
        ) : (
          <button
            onClick={() => setIsAuthOpen(true)}
            className="w-full py-1.5 px-3 rounded-lg text-xs font-medium text-white shadow-sm flex items-center justify-center gap-1.5 transition-all"
            style={{ background: 'linear-gradient(135deg, #0284c7, #6366f1)' }}
          >
            <span>Sign In / Register</span>
          </button>
        )}
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

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={handleAuthSuccess}
      />
    </aside>
  );
}

