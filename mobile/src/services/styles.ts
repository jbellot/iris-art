/**
 * Style transfer API service
 */

import api from './api';
import type {
  StyleJob,
  StyleJobListResponse,
  StyleJobSubmitRequest,
  StyleListResponse,
} from '../types/styles';

/**
 * Get all style presets grouped by tier
 */
export const getStylePresets = async (): Promise<StyleListResponse> => {
  const response = await api.get<StyleListResponse>('/api/v1/styles/presets');
  return response.data;
};

/**
 * Submit a style transfer job
 */
export const applyStyle = async (
  request: StyleJobSubmitRequest,
): Promise<StyleJob> => {
  const response = await api.post<StyleJob>('/api/v1/styles/apply', request);
  return response.data;
};

/**
 * Get style job status
 */
export const getStyleJob = async (jobId: string): Promise<StyleJob> => {
  const response = await api.get<StyleJob>(`/api/v1/styles/jobs/${jobId}`);
  return response.data;
};

/**
 * List user's style jobs with optional photo filter
 */
export const getStyleJobs = async (
  photoId?: string,
  page: number = 1,
  pageSize: number = 20,
): Promise<StyleJobListResponse> => {
  const params: Record<string, string | number> = {
    page,
    page_size: pageSize,
  };

  if (photoId) {
    params.photo_id = photoId;
  }

  const response = await api.get<StyleJobListResponse>(
    '/api/v1/styles/jobs',
    {params},
  );
  return response.data;
};
