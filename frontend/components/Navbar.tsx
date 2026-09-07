'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { useAuth } from '@/store/useAuth';

export function Navbar() {
  const pathname = usePathname();
  const { user, openAuthModal, logout } = useAuth();
  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets });

  const currentPath = pathname || '/';
  const pathParts = currentPath.split('/');
  const routeDatasetId = pathParts.length > 2 ? pathParts[2] : null;
  const activeDatasetId = routeDatasetId || datasets?.[0]?.id;

  const navItems = [
    { label: 'Datasets', href: '/', isActive: currentPath === '/' },
    {
      label: 'Executive Insights',
      href: activeDatasetId ? `/insights/${activeDatasetId}` : '#',
      isActive: currentPath.startsWith('/insights'),
      disabled: !activeDatasetId,
    },
    {
      label: 'Agent Analyst Chat',
      href: activeDatasetId ? `/analyse/${activeDatasetId}` : '#',
      isActive: currentPath.startsWith('/analyse'),
      disabled: !activeDatasetId,
    },
    {
      label: 'Explorer & Profiler',
      href: activeDatasetId ? `/explore/${activeDatasetId}` : '#',
      isActive: currentPath.startsWith('/explore'),
      disabled: !activeDatasetId,
    },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-surface-container-lowest/95 backdrop-blur-md border-b border-outline-variant/30 shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      <div className="h-16 w-full px-gutter-canvas flex items-center justify-between gap-space-lg">
        {/* Left: Brand & Navigation */}
        <div className="flex items-center gap-space-xl">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-space-sm group">
            <div className="w-8 h-8 rounded-lg bg-primary-container text-white flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform">
              <span className="material-symbols-outlined text-[20px]">insights</span>
            </div>
            <div className="flex items-center gap-space-xs">
              <span className="font-headline-sm text-headline-sm text-on-surface tracking-tight font-bold">
                InsightForge
              </span>
              <span className="hidden sm:inline-flex px-space-xs py-space-3xs rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm uppercase">
                Autonomous AI Studio
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-space-lg">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className={`py-space-xs transition-colors font-label-md text-label-md ${
                  item.isActive
                    ? 'text-primary font-bold border-b-2 border-primary'
                    : 'text-on-surface-variant hover:text-on-surface'
                } ${item.disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>

        {/* Right: Telemetry & User Controls */}
        <div className="flex items-center gap-space-md">
          {/* Dual-Core Telemetry Pill */}
          <div className="hidden xl:flex items-center gap-space-xs px-space-sm py-space-2xs rounded-full bg-primary-fixed text-on-primary-fixed font-code-sm text-code-sm shadow-xs">
            <span className="material-symbols-outlined text-[14px] text-primary animate-pulse">
              bolt
            </span>
            <span className="font-semibold">Gemini + Groq</span>
          </div>

          {/* Connection Pulse */}
          <div className="hidden md:flex items-center gap-space-2xs px-space-xs py-space-3xs font-code-sm text-code-sm text-on-surface-variant">
            <span className="w-2 h-2 rounded-full bg-tertiary-fixed-dim ring-4 ring-tertiary-fixed/30"></span>
            <span>Connected (14ms)</span>
          </div>

          {/* User Profile / Auth Action */}
          {user ? (
            <div className="flex items-center gap-space-sm pl-space-xs border-l border-outline-variant/30">
              <div className="relative flex items-center gap-space-xs">
                <div className="w-8 h-8 rounded-full bg-primary-fixed text-primary font-semibold flex items-center justify-center text-xs ring-1 ring-outline-variant">
                  {user.name ? user.name[0].toUpperCase() : 'U'}
                </div>
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-tertiary-fixed-dim ring-2 ring-surface-container-lowest"></span>
              </div>
              <div className="hidden lg:flex flex-col items-start leading-none">
                <span className="font-label-md text-label-md text-on-surface font-semibold">{user.name || user.email}</span>
                <span className="font-body-sm text-body-sm text-on-surface-variant">Data Lead</span>
              </div>
              <button
                onClick={logout}
                title="Logout"
                className="p-1 rounded text-on-surface-variant hover:text-error hover:bg-surface-container-low transition-colors"
              >
                <span className="material-symbols-outlined text-[18px]">logout</span>
              </button>
            </div>
          ) : (
            <button
              onClick={() => openAuthModal('login')}
              className="inline-flex items-center gap-space-xs px-space-md py-space-xs rounded-lg bg-primary text-on-primary hover:bg-primary-container text-label-md font-medium transition-all shadow-xs"
            >
              <span className="material-symbols-outlined text-[16px]">login</span>
              <span>Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
