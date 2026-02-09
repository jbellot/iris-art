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
  };
}
