import apiClient from './api';
import { FusionArtwork, FusionSubmitResponse, BlendMode, LayoutType } from '../types/fusion';

export const fusionService = {
  /**
   * Create a fusion artwork by blending multiple iris images
   */
  async createFusion(
    artworkIds: string[],
    circleId: string,
    blendMode: BlendMode = 'poisson'
  ): Promise<FusionSubmitResponse> {
    const response = await apiClient.post<FusionSubmitResponse>('/fusion', {
      artwork_ids: artworkIds,
      circle_id: circleId,
      blend_mode: blendMode,
    });
    return response.data;
  },

  /**
   * Create a composition artwork by arranging multiple iris images
   */
  async createComposition(
    artworkIds: string[],
    circleId: string,
    layout: LayoutType
  ): Promise<FusionSubmitResponse> {
    const response = await apiClient.post<FusionSubmitResponse>('/composition', {
      artwork_ids: artworkIds,
      circle_id: circleId,
      layout,
    });
    return response.data;
  },

  /**
   * Get fusion artwork status
   */
  async getFusionStatus(fusionId: string): Promise<FusionArtwork> {
    const response = await apiClient.get<FusionArtwork>(`/fusion/${fusionId}`);
    return response.data;
  },

  /**
   * Get list of user's fusion artworks
   */
  async getUserFusions(offset: number = 0, limit: number = 20): Promise<FusionArtwork[]> {
    const response = await apiClient.get<FusionArtwork[]>('/fusion', {
      params: { offset, limit },
    });
    return response.data;
  },
};
