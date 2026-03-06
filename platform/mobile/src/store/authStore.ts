/**
 * Zustand store — autentificare + sesiune curentă
 */
import { create } from 'zustand';
import { authAPI, tokenStorage } from '../services/api';

interface User {
  id: string;
  email: string;
  role: 'patient' | 'doctor' | 'clinic_admin' | 'platform_admin';
  clinicId: string;
  firstName?: string;
  lastName?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login:       (email: string, password: string) => Promise<void>;
  logout:      () => Promise<void>;
  hydrate:     () => Promise<void>;  // verifică token existent la startup
  setUser:     (user: User) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {
    const { data } = await authAPI.login(email, password);
    await tokenStorage.setAccess(data.access_token);
    await tokenStorage.setRefresh(data.refresh_token);
    set({ user: data.user, isAuthenticated: true });
  },

  logout: async () => {
    try {
      await authAPI.logout();
    } finally {
      await tokenStorage.clearAll();
      set({ user: null, isAuthenticated: false });
    }
  },

  hydrate: async () => {
    set({ isLoading: true });
    try {
      const token = await tokenStorage.getAccess();
      if (!token) {
        set({ isLoading: false, isAuthenticated: false });
        return;
      }
      // TODO: decode JWT local sau call /me
      set({ isAuthenticated: true, isLoading: false });
    } catch {
      await tokenStorage.clearAll();
      set({ isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user) => set({ user }),
}));
