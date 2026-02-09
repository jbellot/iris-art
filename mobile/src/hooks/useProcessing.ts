/**
 * Hook for processing operations with store integration
 */
import { useQueryClient } from '@tanstack/react-query';
import {
  submitProcessing,
  submitBatchProcessing,
  reprocessJob,
} from '../services/processing';
import { useProcessingStore } from '../store/processingStore';

export function useProcessing() {
  const queryClient = useQueryClient();
  const { addJob, updateJob } = useProcessingStore();

  /**
   * Start processing a single photo
   */
  const startProcessing = async (photoId: string): Promise<string> => {
    try {
      const job = await submitProcessing(photoId);
      addJob(job.job_id, photoId);
      return job.job_id;
    } catch (error) {
      console.error('Failed to start processing:', error);
      throw error;
    }
  };

  /**
   * Start batch processing multiple photos
   */
  const startBatchProcessing = async (
    photoIds: string[],
  ): Promise<string[]> => {
    try {
      const jobs = await submitBatchProcessing(photoIds);
      jobs.forEach((job) => {
        addJob(job.job_id, job.photo_id);
      });
      return jobs.map((job) => job.job_id);
    } catch (error) {
      console.error('Failed to start batch processing:', error);
      throw error;
    }
  };

  /**
   * Reprocess a failed or completed job
   */
  const reprocess = async (jobId: string): Promise<string> => {
    try {
      const newJob = await reprocessJob(jobId);
      addJob(newJob.job_id, newJob.photo_id);
      return newJob.job_id;
    } catch (error) {
      console.error('Failed to reprocess job:', error);
      throw error;
    }
  };

  /**
   * Invalidate photos cache when job completes
   */
  const invalidatePhotosOnComplete = () => {
    queryClient.invalidateQueries({ queryKey: ['photos'] });
  };

  return {
    startProcessing,
    startBatchProcessing,
    reprocess,
    invalidatePhotosOnComplete,
  };
}
