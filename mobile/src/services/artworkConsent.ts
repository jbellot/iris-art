/**
 * Artwork consent service for fusion and composition features
 */
import apiClient from './api';
import {
  ConsentRequest,
  PendingConsent,
  ConsentStatus,
  RequestConsentPayload,
  DecideConsentPayload,
  ConsentPurpose,
} from '../types/consent';

/**
 * Request consent for artworks
 * POST /api/v1/consent/request
 */
export const requestConsent = async (
  artworkIds: string[],
  purpose: ConsentPurpose,
  circleId: string
): Promise<ConsentRequest[]> => {
  const payload: RequestConsentPayload = {
    artwork_ids: artworkIds,
    purpose,
    circle_id: circleId,
  };

  const response = await apiClient.post<ConsentRequest[]>(
    '/api/v1/consent/request',
    payload
  );
  return response.data;
};

/**
 * Get pending consent requests for the current user
 * GET /api/v1/consent/pending
 */
export const getPendingConsents = async (): Promise<PendingConsent[]> => {
  const response = await apiClient.get<PendingConsent[]>(
    '/api/v1/consent/pending'
  );
  return response.data;
};

/**
 * Decide on a consent request (grant or deny)
 * POST /api/v1/consent/{consentId}/decide
 */
export const decideConsent = async (
  consentId: string,
  decision: 'granted' | 'denied'
): Promise<void> => {
  const payload: DecideConsentPayload = { decision };
  await apiClient.post(`/api/v1/consent/${consentId}/decide`, payload);
};

/**
 * Revoke a previously granted consent
 * POST /api/v1/consent/{consentId}/revoke
 */
export const revokeConsent = async (consentId: string): Promise<void> => {
  await apiClient.post(`/api/v1/consent/${consentId}/revoke`);
};

/**
 * Get consent status for a list of artworks
 * GET /api/v1/consent/status
 */
export const getConsentStatus = async (
  artworkIds: string[],
  purpose: ConsentPurpose
): Promise<ConsentStatus[]> => {
  const response = await apiClient.get<ConsentStatus[]>(
    '/api/v1/consent/status',
    {
      params: {
        artwork_ids: artworkIds.join(','),
        purpose,
      },
    }
  );
  return response.data;
};
