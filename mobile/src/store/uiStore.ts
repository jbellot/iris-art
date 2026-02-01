/**
 * UI store - manages app UI state
 */
import { create } from 'zustand';
import {
  getHasLaunched,
  setHasLaunched as saveHasLaunched,
  getOnboardingComplete,
  setOnboardingComplete as saveOnboardingComplete,
  getBiometricConsentGranted,
  setBiometricConsentGranted as saveBiometricConsentGranted,
} from '../services/storage';

interface UiState {
  isFirstLaunch: boolean;
  onboardingComplete: boolean;
  biometricConsentGranted: boolean;
  isLoading: boolean;

  // Actions
  initializeUiState: () => Promise<void>;
  setFirstLaunch: (value: boolean) => Promise<void>;
  setOnboardingComplete: (value: boolean) => Promise<void>;
  setBiometricConsentGranted: (value: boolean) => Promise<void>;
}

export const useUiStore = create<UiState>((set) => ({
  isFirstLaunch: true,
  onboardingComplete: false,
  biometricConsentGranted: false,
  isLoading: true,

  initializeUiState: async () => {
    try {
      const hasLaunched = await getHasLaunched();
      const onboardingComplete = await getOnboardingComplete();
      const biometricConsentGranted = await getBiometricConsentGranted();

      set({
        isFirstLaunch: !hasLaunched,
        onboardingComplete,
        biometricConsentGranted,
        isLoading: false,
      });

      // Mark as launched if first time
      if (!hasLaunched) {
        await saveHasLaunched(true);
      }
    } catch (error) {
      console.error('Failed to initialize UI state:', error);
      set({ isLoading: false });
    }
  },

  setFirstLaunch: async (value: boolean) => {
    await saveHasLaunched(!value);
    set({ isFirstLaunch: value });
  },

  setOnboardingComplete: async (value: boolean) => {
    await saveOnboardingComplete(value);
    set({ onboardingComplete: value });
  },

  setBiometricConsentGranted: async (value: boolean) => {
    await saveBiometricConsentGranted(value);
    set({ biometricConsentGranted: value });
  },
}));
