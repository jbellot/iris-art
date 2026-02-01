/**
 * Upload queue hook with progress tracking and retry logic
 */
import { create } from 'zustand';
import { uploadPhoto, UploadResult } from '../services/upload';
import { useQueryClient } from '@tanstack/react-query';

// Simple unique ID generator
function generateLocalId(): string {
  return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export interface UploadItem {
  id: string; // Local unique ID
  photoPath: string;
  photoId?: string; // Backend photo ID (set after presign)
  progress: number; // 0-100
  status: 'uploading' | 'completed' | 'failed';
  error?: string;
  width?: number;
  height?: number;
}

interface UploadStore {
  uploads: Map<string, UploadItem>;
  startUpload: (
    photoPath: string,
    width: number,
    height: number
  ) => Promise<string>;
  retryUpload: (localId: string) => Promise<void>;
  getUpload: (localId: string) => UploadItem | undefined;
  getUploadByPhotoId: (photoId: string) => UploadItem | undefined;
  getAllUploads: () => UploadItem[];
}

export const useUploadStore = create<UploadStore>((set, get) => ({
  uploads: new Map(),

  startUpload: async (photoPath: string, width: number, height: number) => {
    const localId = generateLocalId();

    // Add to uploads map with initial state
    const uploadItem: UploadItem = {
      id: localId,
      photoPath,
      progress: 0,
      status: 'uploading',
      width,
      height,
    };

    set((state) => ({
      uploads: new Map(state.uploads).set(localId, uploadItem),
    }));

    // Start upload with callbacks
    uploadPhoto(
      photoPath,
      width,
      height,
      {
        onProgress: (percent) => {
          set((state) => {
            const updated = new Map(state.uploads);
            const item = updated.get(localId);
            if (item) {
              updated.set(localId, { ...item, progress: percent });
            }
            return { uploads: updated };
          });
        },
        onComplete: (result: UploadResult) => {
          set((state) => {
            const updated = new Map(state.uploads);
            const item = updated.get(localId);
            if (item) {
              updated.set(localId, {
                ...item,
                photoId: result.photoId,
                progress: 100,
                status: 'completed',
              });
            }
            return { uploads: updated };
          });
        },
        onError: (error: string) => {
          set((state) => {
            const updated = new Map(state.uploads);
            const item = updated.get(localId);
            if (item) {
              updated.set(localId, {
                ...item,
                status: 'failed',
                error,
              });
            }
            return { uploads: updated };
          });
        },
      }
    );

    return localId;
  },

  retryUpload: async (localId: string) => {
    const item = get().uploads.get(localId);
    if (!item || !item.width || !item.height) {
      return;
    }

    // Reset status and progress
    set((state) => {
      const updated = new Map(state.uploads);
      updated.set(localId, {
        ...item,
        progress: 0,
        status: 'uploading',
        error: undefined,
      });
      return { uploads: updated };
    });

    // Retry upload
    uploadPhoto(
      item.photoPath,
      item.width,
      item.height,
      {
        onProgress: (percent) => {
          set((state) => {
            const updated = new Map(state.uploads);
            const currentItem = updated.get(localId);
            if (currentItem) {
              updated.set(localId, { ...currentItem, progress: percent });
            }
            return { uploads: updated };
          });
        },
        onComplete: (result: UploadResult) => {
          set((state) => {
            const updated = new Map(state.uploads);
            const currentItem = updated.get(localId);
            if (currentItem) {
              updated.set(localId, {
                ...currentItem,
                photoId: result.photoId,
                progress: 100,
                status: 'completed',
              });
            }
            return { uploads: updated };
          });
        },
        onError: (error: string) => {
          set((state) => {
            const updated = new Map(state.uploads);
            const currentItem = updated.get(localId);
            if (currentItem) {
              updated.set(localId, {
                ...currentItem,
                status: 'failed',
                error,
              });
            }
            return { uploads: updated };
          });
        },
      }
    );
  },

  getUpload: (localId: string) => {
    return get().uploads.get(localId);
  },

  getUploadByPhotoId: (photoId: string) => {
    const uploads = Array.from(get().uploads.values());
    return uploads.find((u) => u.photoId === photoId);
  },

  getAllUploads: () => {
    return Array.from(get().uploads.values());
  },
}));

/**
 * Hook to access upload store with React Query integration
 */
export function useUpload() {
  const queryClient = useQueryClient();
  const store = useUploadStore();

  const startUploadWithInvalidation = async (
    photoPath: string,
    width: number,
    height: number
  ) => {
    const localId = await store.startUpload(photoPath, width, height);

    // Invalidate photos query when upload completes
    // Poll for completion (in a real app, use a more elegant solution)
    const pollInterval = setInterval(() => {
      const upload = store.getUpload(localId);
      if (upload && upload.status === 'completed') {
        queryClient.invalidateQueries({ queryKey: ['photos'] });
        clearInterval(pollInterval);
      } else if (upload && upload.status === 'failed') {
        clearInterval(pollInterval);
      }
    }, 1000);

    return localId;
  };

  return {
    ...store,
    startUpload: startUploadWithInvalidation,
  };
}
