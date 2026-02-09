/**
 * Invite API service
 */
import apiClient from './api';
import { InviteInfo, InviteResponse } from '../types/circles';

export const createInvite = async (circleId: string): Promise<InviteResponse> => {
  const response = await apiClient.post<InviteResponse>(
    `/api/v1/circles/${circleId}/invite`
  );
  return response.data;
};

export const getInviteInfo = async (token: string): Promise<InviteInfo> => {
  const response = await apiClient.get<InviteInfo>(
    `/api/v1/invites/${token}/info`
  );
  return response.data;
};

export const acceptInvite = async (token: string): Promise<{ circle_id: string }> => {
  const response = await apiClient.post<{ circle_id: string }>(
    `/api/v1/invites/${token}/accept`
  );
  return response.data;
};
