/**
 * Application constants
 */

// API Configuration
export const API_BASE_URL = __DEV__
  ? 'http://localhost:8000/api/v1'
  : 'https://api.irisart.app/api/v1';

// App Metadata
export const APP_NAME = 'IrisArt';
export const APP_VERSION = '0.1.0';

// Storage Keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  HAS_LAUNCHED: 'has_launched',
  ONBOARDING_COMPLETE: 'onboarding_complete',
  BIOMETRIC_CONSENT_GRANTED: 'biometric_consent_granted',
  USER_DATA: 'user_data',
} as const;

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const GALLERY_PAGE_SIZE = 30;

// Upload Configuration
export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
export const SUPPORTED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png'];

// Timeouts
export const API_TIMEOUT = 30000; // 30 seconds
export const UPLOAD_TIMEOUT = 120000; // 2 minutes
