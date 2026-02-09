/**
 * Artwork consent types for fusion and composition features
 */

export type ConsentPurpose = 'fusion' | 'composition';

export interface ConsentRequest {
  id: string;
  artwork_id: string;
  grantor_user_id: string;
  grantee_user_id: string;
  purpose: ConsentPurpose;
  status: 'pending' | 'granted' | 'denied' | 'revoked';
  requested_at: string;
}

export interface PendingConsent {
  id: string;
  artwork_id: string;
  artwork_preview_url: string;
  grantee_email: string;
  purpose: ConsentPurpose;
  circle_name: string;
  requested_at: string;
}

export type ConsentStatusType = 'self' | 'granted' | 'pending' | 'denied' | 'none';

export interface ConsentStatus {
  artwork_id: string;
  status: ConsentStatusType;
}

export interface RequestConsentPayload {
  artwork_ids: string[];
  purpose: ConsentPurpose;
  circle_id: string;
}

export interface DecideConsentPayload {
  decision: 'granted' | 'denied';
}

export interface ConsentStatusQuery {
  artwork_ids: string[];
  purpose: ConsentPurpose;
}
