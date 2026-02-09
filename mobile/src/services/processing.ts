/**
 * Processing API service
 */
import api from './api';
import { ProcessingJob } from '../types/processing';

export interface BatchProcessingResponse {
  jobs: ProcessingJob[];
}

export interface JobListResponse {
  items: ProcessingJob[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Submit a single photo for processing
 */
export async function submitProcessing(
  photoId: string,
): Promise<ProcessingJob> {
  const response = await api.post<ProcessingJob>('/processing/submit', {
    photo_id: photoId,
  });
  return response.data;
}

/**
 * Submit multiple photos for batch processing
 */
export async function submitBatchProcessing(
  photoIds: string[],
): Promise<ProcessingJob[]> {
  const response = await api.post<BatchProcessingResponse>(
    '/processing/batch',
    {
      photo_ids: photoIds,
    },
  );
  return response.data.jobs;
}

/**
 * Get status of a specific processing job
 */
export async function getJobStatus(jobId: string): Promise<ProcessingJob> {
  const response = await api.get<ProcessingJob>(`/processing/jobs/${jobId}`);
  return response.data;
}

/**
 * Get all processing jobs for the current user
 */
export async function getUserJobs(page: number = 1): Promise<JobListResponse> {
  const response = await api.get<JobListResponse>('/processing/jobs', {
    params: { page },
  });
  return response.data;
}

/**
 * Reprocess a failed or completed job
 */
export async function reprocessJob(jobId: string): Promise<ProcessingJob> {
  const response = await api.post<ProcessingJob>(
    `/processing/jobs/${jobId}/reprocess`,
  );
  return response.data;
}
