'use client';

import React, { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { Navbar } from '@/components/Navbar';
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

  const isLanding = isInitialized && !user && pathname === '/';

  return (
    <div className="min-h-screen bg-surface flex flex-col font-body-md text-body-md text-on-surface antialiased">
      {!isLanding && <Navbar />}
      <main className={`flex-1 w-full ${!isLanding ? 'pt-16' : ''}`}>
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
