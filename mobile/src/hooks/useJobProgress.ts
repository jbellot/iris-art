/**
 * WebSocket hook for real-time job progress updates
 */
import { useEffect, useState, useRef } from 'react';
import { WS_BASE_URL } from '../utils/constants';
import { getAccessToken } from '../services/storage';
import { ProcessingProgress } from '../types/processing';

interface JobProgressResult {
  progress: number;
  step: string | null;
  status: string;
  result: {
    result_url?: string;
    processing_time_ms?: number;
    result_width?: number;
    result_height?: number;
  } | null;
  error: {
    error_type?: string;
    message?: string;
    suggestion?: string;
  } | null;
  isConnected: boolean;
}

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 2000;

export function useJobProgress(jobId: string | null): JobProgressResult {
  const [progress, setProgress] = useState<number>(0);
  const [step, setStep] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('pending');
  const [result, setResult] = useState<JobProgressResult['result']>(null);
  const [error, setError] = useState<JobProgressResult['error']>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef<number>(0);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!jobId) {
      return;
    }

    let isMounted = true;

    const connectWebSocket = async () => {
      try {
        const token = await getAccessToken();
        if (!token || !isMounted) {
          return;
        }

        const wsUrl = `${WS_BASE_URL}/ws/jobs/${jobId}?token=${token}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (isMounted) {
            setIsConnected(true);
            retryCountRef.current = 0; // Reset retry count on successful connection
          }
        };

        ws.onmessage = (event) => {
          if (!isMounted) {
            return;
          }

          try {
            const data: ProcessingProgress = JSON.parse(event.data);

            setProgress(data.progress);
            setStep(data.step);
            setStatus(data.status);

            // Handle completion
            if (data.status === 'completed') {
              setResult({
                result_url: data.result_url,
                processing_time_ms: data.processing_time_ms,
                result_width: data.result_width,
                result_height: data.result_height,
              });
              ws.close();
            }

            // Handle failure
            if (data.status === 'failed') {
              setError({
                error_type: data.error_type,
                message: data.message,
                suggestion: data.suggestion,
              });
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
          }
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
        if (isMounted) {
          setIsConnected(false);
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
    };
  }, [jobId]);

  return {
    progress,
    step,
    status,
    result,
    error,
    isConnected,
  };
}
