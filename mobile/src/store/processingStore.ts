/**
 * Zustand store for tracking active processing jobs
 */
import { create } from 'zustand';

export interface ProcessingJobState {
  jobId: string;
  photoId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  step: string | null;
  error: {
    error_type?: string;
    message?: string;
    suggestion?: string;
  } | null;
  result: {
    result_url?: string;
    processing_time_ms?: number;
    result_width?: number;
    result_height?: number;
  } | null;
}

interface ProcessingStore {
  jobs: Map<string, ProcessingJobState>;
  addJob: (jobId: string, photoId: string) => void;
  updateJob: (
    jobId: string,
    updates: Partial<Omit<ProcessingJobState, 'jobId' | 'photoId'>>,
  ) => void;
  removeJob: (jobId: string) => void;
  getJobForPhoto: (photoId: string) => ProcessingJobState | undefined;
  getAllJobs: () => ProcessingJobState[];
  getActiveJobs: () => ProcessingJobState[];
}

export const useProcessingStore = create<ProcessingStore>((set, get) => ({
  jobs: new Map(),

  addJob: (jobId: string, photoId: string) => {
    set((state) => {
      const updated = new Map(state.jobs);
      updated.set(jobId, {
        jobId,
        photoId,
        status: 'pending',
        progress: 0,
        step: null,
        error: null,
        result: null,
      });
      return { jobs: updated };
    });
  },

  updateJob: (jobId: string, updates: Partial<Omit<ProcessingJobState, 'jobId' | 'photoId'>>) => {
    set((state) => {
      const updated = new Map(state.jobs);
      const existing = updated.get(jobId);
      if (existing) {
        updated.set(jobId, { ...existing, ...updates });
      }
      return { jobs: updated };
    });
  },

  removeJob: (jobId: string) => {
    set((state) => {
      const updated = new Map(state.jobs);
      updated.delete(jobId);
      return { jobs: updated };
    });
  },

  getJobForPhoto: (photoId: string) => {
    const jobs = Array.from(get().jobs.values());
    return jobs.find((job) => job.photoId === photoId);
  },

  getAllJobs: () => {
    return Array.from(get().jobs.values());
  },

  getActiveJobs: () => {
    const jobs = Array.from(get().jobs.values());
    return jobs.filter(
      (job) => job.status === 'pending' || job.status === 'processing',
    );
  },
}));
