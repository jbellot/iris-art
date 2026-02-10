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
 * POST /consent/request
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
    '/consent/request',
    payload
  );
  return response.data;
};

/**
 * Get pending consent requests for the current user
 * GET /consent/pending
 */
export const getPendingConsents = async (): Promise<PendingConsent[]> => {
  const response = await apiClient.get<PendingConsent[]>(
    '/consent/pending'
  );
  return response.data;
};

/**
 * Decide on a consent request (grant or deny)
 * POST /consent/{consentId}/decide
 */
export const decideConsent = async (
  consentId: string,
  decision: 'granted' | 'denied'
): Promise<void> => {
  const payload: DecideConsentPayload = { decision };
  await apiClient.post(`/consent/${consentId}/decide`, payload);
};

/**
 * Revoke a previously granted consent
 * POST /consent/{consentId}/revoke
 */
export const revokeConsent = async (consentId: string): Promise<void> => {
  await apiClient.post(`/consent/${consentId}/revoke`);
};

/**
 * Get consent status for a list of artworks
 * GET /consent/status
 */
export const getConsentStatus = async (
  artworkIds: string[],
  purpose: ConsentPurpose
): Promise<ConsentStatus[]> => {
  const response = await apiClient.get<ConsentStatus[]>(
    '/consent/status',
    {
      params: {
        artwork_ids: artworkIds.join(','),
        purpose,
      },
    }
  );
  return response.data;
};
