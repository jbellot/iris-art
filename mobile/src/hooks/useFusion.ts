/**
 * Hook for fusion progress tracking via REST polling + WebSocket
 * Reuses WebSocket pattern from Phase 3, adds fusion-specific magical step names
 */
import { useEffect, useState, useRef } from 'react';
import { WS_BASE_URL } from '../utils/constants';
import { getAccessToken } from '../services/storage';
import { FusionProgress } from '../types/fusion';
import { fusionService } from '../services/fusion';

interface UseFusionResult {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  resultUrl?: string;
  thumbnailUrl?: string;
  error?: string;
  isConnected: boolean;
}

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 2000;

// Magical step names mapping
const FUSION_STEPS: Record<string, string> = {
  'preparing': 'Gathering iris artworks...',
  'loading_models': 'Preparing for blending...',
  'blending': 'Creating seamless fusion...',
  'postprocessing': 'Adding finishing touches...',
  'saving': 'Almost done...',
};

const COMPOSITION_STEPS: Record<string, string> = {
  'preparing': 'Arranging your irises...',
  'layout': 'Creating layout...',
  'saving': 'Saving composition...',
};

export function useFusion(fusionId: string | null, fusionType: 'fusion' | 'composition' = 'fusion'): UseFusionResult {
  const [status, setStatus] = useState<UseFusionResult['status']>('pending');
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [resultUrl, setResultUrl] = useState<string | undefined>(undefined);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | undefined>(undefined);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef<number>(0);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stepMapping = fusionType === 'fusion' ? FUSION_STEPS : COMPOSITION_STEPS;

  // Magical step name mapper
  const getMagicalStep = (step: string): string => {
    return stepMapping[step] || step;
  };

  // REST polling fallback
  const startPolling = () => {
    if (!fusionId || pollingIntervalRef.current) {
      return;
    }

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const fusionData = await fusionService.getFusionStatus(fusionId);
        setStatus(fusionData.status);

        if (fusionData.status === 'completed') {
          setProgress(100);
          setResultUrl(fusionData.result_url);
          setThumbnailUrl(fusionData.thumbnail_url);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        } else if (fusionData.status === 'failed') {
          setError(fusionData.error || 'Fusion processing failed');
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000); // Poll every 3 seconds
  };

  useEffect(() => {
    if (!fusionId) {
      return;
    }

    let isMounted = true;

    const connectWebSocket = async () => {
      try {
        const token = await getAccessToken();
        if (!token || !isMounted) {
          // Fallback to polling if no token
          startPolling();
          return;
        }

        const wsUrl = `${WS_BASE_URL}/ws/jobs/${fusionId}?token=${token}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (isMounted) {
            setIsConnected(true);
            retryCountRef.current = 0;
          }
        };

        ws.onmessage = (event) => {
          if (!isMounted) {
            return;
          }

          try {
            const data: FusionProgress = JSON.parse(event.data);

            setProgress(data.progress);
            setCurrentStep(getMagicalStep(data.current_step));
            setStatus(data.status);

            // Handle completion
            if (data.status === 'completed') {
              setResultUrl(data.result_url);
              setThumbnailUrl(data.thumbnail_url);
              ws.close();
            }

            // Handle failure
            if (data.status === 'failed') {
              setError(data.error || 'Fusion processing failed');
              ws.close();
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        ws.onerror = (event) => {
          console.error('WebSocket error:', event);
          if (isMounted) {
            setIsConnected(false);
            // Fallback to polling on WebSocket error
            startPolling();
          }
        };

        ws.onclose = () => {
          if (!isMounted) {
            return;
          }

          setIsConnected(false);

          // Only attempt reconnect if job is not completed/failed and we haven't exceeded retries
          if (
            status !== 'completed' &&
            status !== 'failed' &&
            retryCountRef.current < MAX_RETRIES
          ) {
            retryCountRef.current += 1;
            retryTimeoutRef.current = setTimeout(() => {
              connectWebSocket();
            }, RETRY_DELAY_MS);
          } else if (status !== 'completed' && status !== 'failed') {
            // Fallback to polling after max retries
            startPolling();
          }
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
        if (isMounted) {
          setIsConnected(false);
          startPolling();
        }
      }
    };

    connectWebSocket();

    // Cleanup
    return () => {
      isMounted = false;
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [fusionId]);

  return {
    status,
    progress,
    currentStep,
    resultUrl,
    thumbnailUrl,
    error,
    isConnected,
  };
}
