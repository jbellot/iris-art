/**
 * Auth store - manages authentication state
 */
import { create } from 'zustand';
import { UserRead } from '../types/api';
import * as authService from '../services/auth';
import { getAccessToken, storeUserData, getUserData } from '../services/storage';

interface AuthState {
  user: UserRead | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: UserRead | null) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const user = await authService.login(email, password);
      await storeUserData(JSON.stringify(user));
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed';
      set({ error: message, isLoading: false, isAuthenticated: false });
      throw error;
    }
  },

  register: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await authService.register(email, password);
      set({ isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Registration failed';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await authService.logout();
      set({ user: null, isAuthenticated: false, isLoading: false });
    } catch (error) {
      // Still clear local state even if API call fails
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const token = await getAccessToken();
      if (!token) {
        set({ isAuthenticated: false, isLoading: false, user: null });
        return;
      }

      // Try to get cached user data first
      const cachedUser = await getUserData();
      if (cachedUser) {
        set({ user: JSON.parse(cachedUser), isAuthenticated: true });
      }

      // Validate token by fetching current user
      const user = await authService.getCurrentUser();
      await storeUserData(JSON.stringify(user));
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      // Token is invalid or expired
      set({ isAuthenticated: false, isLoading: false, user: null });
    }
  },

  setUser: (user: UserRead | null) => {
    set({ user, isAuthenticated: !!user });
  },

  clearError: () => {
    set({ error: null });
  },
}));
