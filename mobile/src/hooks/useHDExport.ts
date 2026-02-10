/**
 * Hook for HD export workflow
 */

import {useState, useCallback} from 'react';
import {requestHDExport} from '../services/exports';
import {useJobProgress} from './useJobProgress';
import type {ExportJob, ExportSourceType} from '../types/exports';

export function useHDExport() {
  const [activeExport, setActiveExport] = useState<ExportJob | null>(null);

  // WebSocket progress tracking for active export
  const {
    progress,
    step,
    status,
    result,
    error,
    isConnected: wsConnected,
  } = useJobProgress(activeExport?.id || null);

  // Update active export when WebSocket sends updates
  if (activeExport && (progress || step || status)) {
    const updates: Partial<ExportJob> = {status: status as any};
    if (progress !== undefined) {
      updates.progress = progress;
    }
    if (step) {
      updates.currentStep = step;
    }
    if (result?.result_url) {
      updates.resultUrl = result.result_url;
      updates.resultWidth = result.result_width || null;
      updates.resultHeight = result.result_height || null;
      updates.fileSizeBytes = result.file_size_bytes || null;
      updates.processingTimeMs = result.processing_time_ms || null;
    }
    if (error?.message) {
      updates.errorType = error.error_type || null;
      updates.errorMessage = error.message;
    }

    setActiveExport(prev => (prev ? {...prev, ...updates} : null));
  }

  // Request HD export
  const requestExport = useCallback(
    async (sourceType: ExportSourceType, sourceJobId: string) => {
      try {
        const job = await requestHDExport({sourceType, sourceJobId});
        setActiveExport(job);

        return job;
      } catch (err) {
        console.error('Failed to request HD export:', err);
        throw err;
      }
    },
    [],
  );

  // Download result (placeholder - actual download would use react-native-fs)
  const downloadResult = useCallback(async (resultUrl: string) => {
    // TODO: Implement actual download with react-native-fs or CameraRoll
    console.log('Download result:', resultUrl);
    throw new Error('Download not yet implemented');
  }, []);

  // Poll payment status after purchase completion
  // Returns true when is_paid=true, false on timeout (30s max)
  const pollPaymentStatus = useCallback(
    async (exportJobId: string): Promise<boolean> => {
      const maxAttempts = 15; // 15 attempts * 2 seconds = 30 seconds
      const pollInterval = 2000; // 2 seconds

      for (let i = 0; i < maxAttempts; i++) {
        try {
          // Import api client dynamically to avoid circular dependency
          const {default: apiClient} = await import('../services/api');
          const response = await apiClient.get<{
            is_paid: boolean;
            job_id: string;
          }>(`/exports/jobs/${exportJobId}/payment-status`);

          if (response.data.is_paid) {
            return true;
          }

          // Wait before next attempt
          await new Promise<void>(resolve => setTimeout(resolve, pollInterval));
        } catch (error) {
          console.error('Error polling payment status:', error);
          // Continue polling on error
        }
      }

      // Timeout after 30 seconds
      console.warn('Payment status polling timed out after 30 seconds');
      return false;
    },
    [],
  );

  return {
    // Active export state
    activeExport,
    isExporting:
      activeExport &&
      (activeExport.status === 'pending' ||
        activeExport.status === 'processing'),
    wsConnected,

    // Actions
    requestExport,
    downloadResult,
    pollPaymentStatus,
  };
}
