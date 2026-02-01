/**
 * Biometric consent service - Phase 1 privacy API integration
 */
import apiClient from './api';

export interface ConsentRequirements {
  consent_text: string;
  consent_text_version: string;
  requires_explicit_consent: boolean;
  jurisdiction_name: string;
}

export interface JurisdictionResponse {
  jurisdiction: string;
  consent_requirements: ConsentRequirements;
}

export interface BiometricConsentStatus {
  has_consent: boolean;
}

export interface ConsentGrantRequest {
  consent_type: 'biometric_capture' | 'data_processing';
  jurisdiction: string;
  consent_text_version: string;
}

/**
 * Check if user has active biometric consent
 * GET /api/v1/privacy/consent/biometric-status
 */
export async function checkBiometricConsent(): Promise<boolean> {
  try {
    const response = await apiClient.get<BiometricConsentStatus>(
      '/privacy/consent/biometric-status'
    );
    return response.data.has_consent;
  } catch (error) {
    console.error('Failed to check biometric consent:', error);
    return false;
  }
}

/**
 * Get jurisdiction-specific consent requirements
 * GET /api/v1/privacy/jurisdiction
 */
export async function getJurisdictionInfo(
  countryCode?: string,
  stateCode?: string
): Promise<JurisdictionResponse | null> {
  try {
    const params: Record<string, string> = {};
    if (countryCode) {
      params.country_code = countryCode;
    }
    if (stateCode) {
      params.state_code = stateCode;
    }

    const response = await apiClient.get<JurisdictionResponse>(
      '/privacy/jurisdiction',
      { params }
    );
    return response.data;
  } catch (error) {
    console.error('Failed to get jurisdiction info:', error);
    return null;
  }
}

/**
 * Grant biometric consent
 * POST /api/v1/privacy/consent
 */
export async function grantBiometricConsent(
  jurisdiction: string,
  consentTextVersion: string
): Promise<boolean> {
  try {
    const payload: ConsentGrantRequest = {
      consent_type: 'biometric_capture',
      jurisdiction,
      consent_text_version: consentTextVersion,
    };

    await apiClient.post('/privacy/consent', payload);
    return true;
  } catch (error) {
    console.error('Failed to grant biometric consent:', error);
    return false;
  }
}
