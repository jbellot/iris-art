/**
 * Circle API service
 */
import apiClient from './api';
import { Circle, CircleMember } from '../types/circles';

export const getCircles = async (): Promise<Circle[]> => {
  const response = await apiClient.get<Circle[]>('/api/v1/circles');
  return response.data;
};

export const createCircle = async (name: string): Promise<Circle> => {
  const response = await apiClient.post<Circle>('/api/v1/circles', { name });
  return response.data;
};

export const getCircleDetail = async (circleId: string): Promise<Circle> => {
  const response = await apiClient.get<Circle>(`/api/v1/circles/${circleId}`);
  return response.data;
};

export const getCircleMembers = async (circleId: string): Promise<CircleMember[]> => {
  const response = await apiClient.get<CircleMember[]>(
    `/api/v1/circles/${circleId}/members`
  );
  return response.data;
};

export const leaveCircle = async (circleId: string): Promise<void> => {
  await apiClient.post(`/api/v1/circles/${circleId}/leave`);
};

export const removeMember = async (
  circleId: string,
  userId: string
): Promise<void> => {
  await apiClient.delete(`/api/v1/circles/${circleId}/members/${userId}`);
};
