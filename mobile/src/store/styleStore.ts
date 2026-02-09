/**
 * Zustand store for style transfer jobs
 */

import {create} from 'zustand';
import type {StyleJob, StylePreset} from '../types/styles';

interface StyleStore {
  // Active style jobs indexed by job ID
  activeJobs: Record<string, StyleJob>;

  // Currently selected preset in style gallery
  selectedPreset: StylePreset | null;

  // Actions
  addJob: (job: StyleJob) => void;
  updateJob: (jobId: string, updates: Partial<StyleJob>) => void;
  removeJob: (jobId: string) => void;
  setSelectedPreset: (preset: StylePreset | null) => void;
  getJobForPhoto: (photoId: string) => StyleJob | null;
  clearCompletedJobs: () => void;
}

export const useStyleStore = create<StyleStore>((set, get) => ({
  activeJobs: {},
  selectedPreset: null,

  addJob: (job: StyleJob) => {
    set(state => ({
      activeJobs: {
        ...state.activeJobs,
        [job.id]: job,
      },
    }));
  },

  updateJob: (jobId: string, updates: Partial<StyleJob>) => {
    set(state => {
      const existingJob = state.activeJobs[jobId];
      if (!existingJob) {
        return state;
      }

      return {
        activeJobs: {
          ...state.activeJobs,
          [jobId]: {
            ...existingJob,
            ...updates,
          },
        },
      };
    });
  },

  removeJob: (jobId: string) => {
    set(state => {
      const {[jobId]: removed, ...remaining} = state.activeJobs;
      return {activeJobs: remaining};
    });
  },

  setSelectedPreset: (preset: StylePreset | null) => {
    set({selectedPreset: preset});
  },

  getJobForPhoto: (photoId: string) => {
    const {activeJobs} = get();

    // Find most recent active job for this photo
    const jobs = Object.values(activeJobs).filter(
      job =>
        job.status === 'pending' || job.status === 'processing',
    );

    // Return the most recently created one
    if (jobs.length === 0) {
      return null;
    }

    return jobs.reduce((latest, current) =>
      new Date(current.createdAt) > new Date(latest.createdAt)
        ? current
        : latest,
    );
  },

  clearCompletedJobs: () => {
    set(state => {
      const activeJobs = Object.fromEntries(
        Object.entries(state.activeJobs).filter(
          ([_, job]) => job.status !== 'completed' && job.status !== 'failed',
        ),
      );
      return {activeJobs};
    });
  },
}));
