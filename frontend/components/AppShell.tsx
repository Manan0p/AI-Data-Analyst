'use client';

import React, { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/Sidebar';
import { AuthModal } from '@/components/AuthModal';
import { useAuth } from '@/store/useAuth';

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const {
    user,
    isInitialized,
    initAuth,
    isAuthModalOpen,
    authModalMode,
    closeAuthModal,
    setUser,
  } = useAuth();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  // If user is unauthenticated on the root route, give the landing page full-screen width
  const isLanding = isInitialized && !user && pathname === '/';

  return (
    <div className="flex min-h-screen bg-[#09090b]">
      {!isLanding && <Sidebar />}
      <main className={`flex-1 overflow-auto ${isLanding ? 'w-full' : ''}`}>
        {children}
      </main>
      <AuthModal
        isOpen={isAuthModalOpen}
        initialMode={authModalMode}
        onClose={closeAuthModal}
        onSuccess={(newUser) => setUser(newUser)}
      />
    </div>
  );
}
