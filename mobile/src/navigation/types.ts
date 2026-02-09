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
    photoPath: string;
    photoWidth: number;
    photoHeight: number;
  };
  PhotoDetail: {
    photoId: string;
  };
  ProcessingResult: {
    jobId: string;
    photoId: string;
  };
  StyleGallery: {
    photoId: string;
    processingJobId?: string;
    originalImageUrl: string;
  };
  StylePreview: {
    photoId: string;
    stylePresetId: string;
    processingJobId?: string;
    originalImageUrl: string;
  };
  AIGenerate: {
    photoId: string;
    processingJobId: string;
    originalImageUrl: string;
  };
  HDExport: {
    sourceType: 'styled' | 'ai_generated' | 'processed';
    sourceJobId: string;
    previewImageUrl: string;
  };
};

// Circles Stack
export type CirclesStackParamList = {
  CirclesList: undefined;
  CreateCircle: undefined;
  CircleDetail: {
    circleId: string;
  };
  Invite: {
    circleId: string;
  };
  JoinCircle: {
    token: string;
  };
  // Placeholder screens for future plans (05-04, 05-06)
  SharedGallery: {
    circleId: string;
  };
  FusionBuilder: {
    artworkIds: string[];
    circleId: string;
  };
  CompositionBuilder: {
    artworkIds: string[];
    circleId: string;
  };
  FusionResult: {
    fusionId: string;
  };
};

// Root Stack
export type RootStackParamList = {
  Onboarding: NavigatorScreenParams<OnboardingStackParamList>;
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainStackParamList>;
  Circles: NavigatorScreenParams<CirclesStackParamList>;
};
