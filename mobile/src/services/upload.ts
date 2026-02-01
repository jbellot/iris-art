/**
 * Photo upload service with presigned URL and retry logic
 */
import axios from 'axios';
import apiClient from './api';
import { PresignedUploadResponse } from '../types/photo';

export interface UploadResult {
  photoId: string;
  success: boolean;
  error?: string;
}

export interface UploadCallbacks {
  onProgress: (percent: number) => void;
  onComplete: (result: UploadResult) => void;
  onError: (error: string) => void;
}

/**
 * Upload photo to S3 using presigned URL with retry logic
 */
export async function uploadPhoto(
  photoPath: string,
  photoWidth: number,
  photoHeight: number,
  callbacks: UploadCallbacks,
  maxRetries: number = 3
): Promise<UploadResult> {
  try {
    // Step 1: Request presigned URL from backend
    const { data: presignData } = await apiClient.post<PresignedUploadResponse>(
      '/photos/upload',
      {
        content_type: 'image/jpeg',
      }
    );

    const { upload_url, photo_id, s3_key } = presignData;

    // Step 2: Upload to S3 with progress tracking and retry
    let attempt = 0;
    let lastError: any = null;

    while (attempt < maxRetries) {
      try {
        // Read file as blob from local path
        const fileUri = photoPath.startsWith('file://')
          ? photoPath
          : `file://${photoPath}`;
        const fileResponse = await fetch(fileUri);
        const blob = await fileResponse.blob();

        // Create a separate axios instance without JWT interceptor
        // Presigned URL has auth in query string
        const s3Client = axios.create();

        await s3Client.put(upload_url, blob, {
          headers: { 'Content-Type': 'image/jpeg' },
          onUploadProgress: (progressEvent) => {
            const total = progressEvent.total || blob.size;
            const percent = Math.round((progressEvent.loaded / total) * 100);
            callbacks.onProgress(percent);
          },
        });

        // Step 3: Confirm upload with backend
        await apiClient.post(`/photos/${photo_id}/confirm`, {
          file_size: blob.size,
          width: photoWidth,
          height: photoHeight,
        });

        const result: UploadResult = { photoId: photo_id, success: true };
        callbacks.onComplete(result);
        return result;
      } catch (error: any) {
        lastError = error;
        attempt++;

        // Check if error is retryable (network error or 5xx, not 4xx)
        const isRetryable =
          !error.response ||
          (error.response?.status >= 500 && error.response?.status < 600);

        if (!isRetryable || attempt >= maxRetries) {
          break;
        }

        // Exponential backoff: 1s, 2s, 4s
        const backoffMs = 1000 * Math.pow(2, attempt - 1);
        await new Promise<void>((resolve) => setTimeout(() => resolve(), backoffMs));
      }
    }

    // All retries exhausted
    const errorMsg = lastError?.message || 'Upload failed after retries';
    callbacks.onError(errorMsg);
    return {
      photoId: presignData.photo_id,
      success: false,
      error: errorMsg,
    };
  } catch (error: any) {
    // Failed to get presigned URL
    const errorMsg = error?.message || 'Failed to start upload';
    callbacks.onError(errorMsg);
    return {
      photoId: '',
      success: false,
      error: errorMsg,
    };
  }
}
