/**
 * Type definitions for artistic style transfer
 */

export type StyleTier = 'free' | 'premium';

export type StyleCategory =
  | 'abstract'
  | 'watercolor'
  | 'oil_painting'
  | 'geometric'
  | 'cosmic'
  | 'nature'
  | 'pop_art'
  | 'minimalist';

export interface StylePreset {
  id: string;
  name: string;
  displayName: string;
  description: string;
  category: StyleCategory;
  tier: StyleTier;
  thumbnailUrl: string | null;
  sortOrder: number;
}

export interface StyleListResponse {
  free: StylePreset[];
  premium: StylePreset[];
}

export type StyleJobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface StyleJob {
  id: string;
  status: StyleJobStatus;
  progress: number;
  currentStep: string | null;
  previewUrl: string | null;
  resultUrl: string | null;
  stylePreset: StylePreset;
  processingTimeMs: number | null;
  errorType: string | null;
  errorMessage: string | null;
  createdAt: string;
  websocketUrl: string | null;
}

export interface StyleJobSubmitRequest {
  photoId: string;
  stylePresetId: string;
  processingJobId?: string;
}

export interface StyleJobListResponse {
  items: StyleJob[];
  total: number;
}
