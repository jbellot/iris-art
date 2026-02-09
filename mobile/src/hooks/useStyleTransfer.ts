/**
 * Hook for applying style presets to photos
 */

import {useCallback} from 'react';
import {useQuery} from '@tanstack/react-query';
import {applyStyle, getStylePresets} from '../services/styles';
import {useStyleStore} from '../store/styleStore';
import {useJobProgress} from './useJobProgress';
import type {StyleJobSubmitRequest} from '../types/styles';

interface UseStyleTransferOptions {
  photoId: string;
  processingJobId?: string;
}

export function useStyleTransfer({
  photoId,
  processingJobId,
}: UseStyleTransferOptions) {
  const {activeJobs, addJob, updateJob, getJobForPhoto} = useStyleStore();

  // Get active job for this photo
  const activeJob = getJobForPhoto(photoId);

  // WebSocket progress tracking for active job
  const {
    progress,
    step,
    status,
    result,
    error,
    isConnected: wsConnected,
  } = useJobProgress(activeJob?.id || null);

  // Update store when WebSocket sends updates
  if (activeJob && (progress || step || status)) {
    const updates: any = {status};
    if (progress !== undefined) {
      updates.progress = progress;
    }
    if (step) {
      updates.currentStep = step;
    }
    if (result?.result_url) {
      updates.resultUrl = result.result_url;
      updates.processingTimeMs = result.processing_time_ms || null;
    }
    if (error?.message) {
      updates.errorType = error.error_type || null;
      updates.errorMessage = error.message;
    }
    updateJob(activeJob.id, updates);
  }

  // Fetch style presets with React Query (cached for 5 minutes)
  const {
    data: presetsData,
    isLoading: presetsLoading,
    error: presetsError,
  } = useQuery({
    queryKey: ['stylePresets'],
    queryFn: getStylePresets,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Apply style preset
  const applyStylePreset = useCallback(
    async (stylePresetId: string) => {
      try {
        const request: StyleJobSubmitRequest = {
          photoId,
          stylePresetId,
          processingJobId,
        };

        const job = await applyStyle(request);
        addJob(job);

        return job;
      } catch (err) {
        console.error('Failed to apply style:', err);
        throw err;
      }
    },
    [photoId, processingJobId, addJob],
  );

  return {
    // Active job state
    activeJob: activeJob ? activeJobs[activeJob.id] : null,
    wsConnected,

    // Style presets
    presets: presetsData,
    presetsLoading,
    presetsError,

    // Actions
    applyStyle: applyStylePreset,
  };
}
