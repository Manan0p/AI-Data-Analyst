'use client';

import { useEffect, useState } from 'react';
import { api, User } from '@/services/api';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
  initialMode?: 'login' | 'register';
}

export function AuthModal({ isOpen, onClose, onSuccess, initialMode = 'login' }: AuthModalProps) {
  const [isLogin, setIsLogin] = useState(initialMode === 'login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Sync mode when modal opens
  useEffect(() => {
    if (isOpen) {
      setIsLogin(initialMode === 'login');
      setError(null);
    }
  }, [isOpen, initialMode]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = isLogin
        ? await api.login(email, password)
        : await api.register(email, password, name || undefined);
      onSuccess(res.user);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-on-surface/40 backdrop-blur-sm p-space-md">
      <div className="w-full max-w-md rounded-2xl p-space-xl bg-surface-container-lowest border border-outline-variant/40 shadow-2xl transition-all">
        <div className="flex items-center justify-between pb-space-sm border-b border-outline-variant/30">
          <div className="flex items-center gap-space-xs">
            <span className="material-symbols-outlined text-primary text-[24px]">lock</span>
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
              {isLogin ? 'Sign In to InsightForge' : 'Create an Account'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-on-surface-variant hover:text-on-surface p-1 rounded-lg hover:bg-surface-container-low transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {error && (
          <div className="mt-space-md p-space-sm rounded-lg bg-error-container text-error text-body-sm font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-space-md space-y-space-md">
          {!isLogin && (
            <div>
              <label className="block font-label-md text-label-md font-semibold text-on-surface mb-1">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Dr. Elena Rostova"
                className="w-full px-space-sm py-2 rounded-lg text-body-sm bg-surface-container-low border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary focus:bg-white transition-all"
              />
            </div>
          )}

          <div>
            <label className="block font-label-md text-label-md font-semibold text-on-surface mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="lead.analyst@example.com"
              className="w-full px-space-sm py-2 rounded-lg text-body-sm bg-surface-container-low border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary focus:bg-white transition-all"
            />
          </div>

          <div>
            <label className="block font-label-md text-label-md font-semibold text-on-surface mb-1">Password</label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-space-sm py-2 rounded-lg text-body-sm bg-surface-container-low border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary focus:bg-white transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg font-semibold text-label-md text-on-primary bg-primary hover:bg-primary-container disabled:opacity-50 transition-all flex items-center justify-center gap-space-xs shadow-xs"
          >
            {loading ? (
              <>
                <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
                <span>Authenticating...</span>
              </>
            ) : isLogin ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="mt-space-md text-center pt-space-xs border-t border-outline-variant/20">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError(null);
            }}
            className="text-body-sm font-medium text-primary hover:underline"
          >
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
          </button>
        </div>
      </div>
    </div>
  );
}
