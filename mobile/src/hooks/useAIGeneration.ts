/**
 * Hook for AI art generation from processed iris
 */

import {useCallback} from 'react';
import {generateAIArt} from '../services/exports';
import {useStyleStore} from '../store/styleStore';
import {useJobProgress} from './useJobProgress';

interface UseAIGenerationOptions {
  photoId: string;
  processingJobId: string;
}

export function useAIGeneration({
  photoId,
  processingJobId,
}: UseAIGenerationOptions) {
  const {activeJobs, addJob, updateJob, getJobForPhoto} = useStyleStore();

  // Get active AI job for this photo (AI jobs have no stylePreset)
  const activeJob = getJobForPhoto(photoId);
  const isAIJob = activeJob && !activeJob.stylePreset;

  // WebSocket progress tracking for active job
  const {
    progress,
    step,
    status,
    result,
    error,
    isConnected: wsConnected,
  } = useJobProgress(isAIJob && activeJob ? activeJob.id : null);

  // Update store when WebSocket sends updates
  if (isAIJob && activeJob && (progress || step || status)) {
    const updates: any = {status};
    if (progress !== undefined) {
      updates.progress = progress;
    }
    if (step) {
      updates.currentStep = step;
    }
    if (result?.result_url) {
      updates.resultUrl = result.result_url;
      updates.previewUrl = result.preview_url || null;
      updates.processingTimeMs = result.processing_time_ms || null;
    }
    if (error?.message) {
      updates.errorType = error.error_type || null;
      updates.errorMessage = error.message;
    }
    updateJob(activeJob.id, updates);
  }

  // Generate AI art
  const generate = useCallback(
    async (prompt?: string, styleHint?: string) => {
      try {
        const job = await generateAIArt(
          photoId,
          processingJobId,
          prompt,
          styleHint,
        );
        addJob(job);

        return job;
      } catch (err) {
        console.error('Failed to generate AI art:', err);
        throw err;
      }
    },
    [photoId, processingJobId, addJob],
  );

  return {
    // Active job state
    activeJob: isAIJob && activeJob ? activeJobs[activeJob.id] : null,
    isGenerating:
      isAIJob &&
      activeJob &&
      (activeJob.status === 'pending' || activeJob.status === 'processing'),
    wsConnected,

    // Actions
    generate,
  };
}
