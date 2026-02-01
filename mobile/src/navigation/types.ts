/**
 * Navigation types for type-safe navigation
 */
import { NavigatorScreenParams } from '@react-navigation/native';

// Onboarding Stack
export type OnboardingStackParamList = {
  Welcome: undefined;
  PrePermission: undefined;
  BiometricConsent: undefined;
};

// Auth Stack
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

// Main App Stack
export type MainStackParamList = {
  Gallery: undefined;
  Camera: undefined;
  PhotoReview: {
    photoUri: string;
  };
  PhotoDetail: {
    photoId: string;
  };
};

// Root Stack
export type RootStackParamList = {
  Onboarding: NavigatorScreenParams<OnboardingStackParamList>;
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainStackParamList>;
};
