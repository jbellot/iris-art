/**
 * API request/response types matching Phase 1 backend schemas
 */

// Auth Types
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserRead {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  apple_id?: string;
  google_id?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

// Privacy/Consent Types
export interface JurisdictionResponse {
  jurisdiction: 'GDPR' | 'BIPA' | 'CCPA' | 'GENERIC';
  detected_country?: string;
  detected_region?: string;
}

export interface ConsentRequirements {
  jurisdiction: string;
  requires_explicit_consent: boolean;
  consent_text: string;
  data_retention_days?: number;
  withdrawal_notice_days?: number;
  additional_info?: string;
}

export interface ConsentGrantRequest {
  consent_type: 'biometric_capture' | 'data_processing' | 'marketing';
  jurisdiction: string;
  consent_text_version: string;
  metadata?: Record<string, any>;
}

export interface ConsentGrantResponse {
  id: string;
  user_id: string;
  consent_type: string;
  jurisdiction: string;
  granted_at: string;
  withdrawn_at?: string;
}

export interface BiometricStatusResponse {
  has_granted_consent: boolean;
  consent_record?: ConsentGrantResponse;
}

// Generic API Error
export interface ApiError {
  detail: string;
  status_code?: number;
}
