/**
 * API service for HD exports
 */

import apiClient from './api';
import type {
  ExportJob,
  HDExportRequest,
  ExportJobListResponse,
} from '../types/exports';
import type {StyleJob} from '../types/styles';

/**
 * Request HD export of styled, AI-generated, or processed image
 */
export async function requestHDExport(
  request: HDExportRequest,
): Promise<ExportJob> {
  const {data} = await apiClient.post<ExportJob>('/exports/hd', request);
  return data;
}

/**
 * Get export job status
 */
export async function getExportJob(jobId: string): Promise<ExportJob> {
  const {data} = await apiClient.get<ExportJob>(
    `/exports/jobs/${jobId}`,
  );
  return data;
}

/**
 * List user's export jobs
 */
export async function getExportJobs(): Promise<ExportJobListResponse> {
  const {data} = await apiClient.get<ExportJobListResponse>(
    '/exports/jobs',
  );
  return data;
}

/**
 * Generate AI art from processed iris
 */
export async function generateAIArt(
  photoId: string,
  processingJobId: string,
  prompt?: string,
  styleHint?: string,
): Promise<StyleJob> {
  const params: Record<string, string> = {
    photo_id: photoId,
    processing_job_id: processingJobId,
  };

  if (prompt) {
    params.prompt = prompt;
  }

  if (styleHint) {
    params.style_hint = styleHint;
  }

  const {data} = await apiClient.post<StyleJob>(
    '/styles/generate',
    null,
    {params},
  );

  return data;
}
