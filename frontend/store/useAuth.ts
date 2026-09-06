import { create } from 'zustand';
import { api, authStorage, User } from '@/services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isInitialized: boolean;
  isAuthModalOpen: boolean;
  authModalMode: 'login' | 'register';
  initAuth: () => void;
  setUser: (user: User | null, token?: string | null) => void;
  logout: () => void;
  openAuthModal: (mode?: 'login' | 'register') => void;
  closeAuthModal: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: null,
  isInitialized: false,
  isAuthModalOpen: false,
  authModalMode: 'login',

  initAuth: () => {
    const user = authStorage.getUser();
    const token = authStorage.getToken();
    set({ user, token, isInitialized: true });
  },

  setUser: (user, token) => {
    if (user && token) {
      authStorage.setUser(user);
      authStorage.setToken(token);
      set({ user, token, isAuthModalOpen: false });
    } else if (user) {
      authStorage.setUser(user);
      set({ user, isAuthModalOpen: false });
    } else {
      authStorage.clear();
      set({ user: null, token: null });
    }
  },

  logout: () => {
    api.logout();
    set({ user: null, token: null });
  },

  openAuthModal: (mode = 'login') => {
    set({ isAuthModalOpen: true, authModalMode: mode });
  },

  closeAuthModal: () => {
    set({ isAuthModalOpen: false });
  },
}));
