/**
 * Hook for fetching shared circle gallery with pagination
 */
import { useState, useCallback } from 'react';
import apiClient from '../services/api';

export interface CircleArtwork {
  artwork_id: string;
  photo_id: string;
  thumbnail_url: string;
  full_url: string;
  owner_user_id: string;
  owner_email: string;
  owner_name?: string;
  created_at: string;
}

interface CircleGalleryResponse {
  artworks: CircleArtwork[];
  total: number;
  limit: number;
  offset: number;
}

export function useCircleGallery(circleId: string) {
  const [artworks, setArtworks] = useState<CircleArtwork[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const LIMIT = 20;

  const fetchGallery = useCallback(
    async (resetOffset = false) => {
      if (loading) return;

      const currentOffset = resetOffset ? 0 : offset;
      setLoading(true);
      setError(null);

      try {
        const response = await apiClient.get<CircleGalleryResponse>(
          `/api/v1/circles/${circleId}/gallery`,
          {
            params: {
              limit: LIMIT,
              offset: currentOffset,
            },
          }
        );

        const { artworks: newArtworks, total } = response.data;

        if (resetOffset) {
          setArtworks(newArtworks);
          setOffset(LIMIT);
        } else {
          setArtworks((prev) => [...prev, ...newArtworks]);
          setOffset((prev) => prev + LIMIT);
        }

        // Check if there are more items
        setHasMore(currentOffset + newArtworks.length < total);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch gallery');
      } finally {
        setLoading(false);
      }
    },
    [circleId, loading, offset]
  );

  const loadMore = useCallback(() => {
    if (hasMore && !loading) {
      fetchGallery(false);
    }
  }, [hasMore, loading, fetchGallery]);

  const refresh = useCallback(() => {
    setOffset(0);
    setHasMore(true);
    fetchGallery(true);
  }, [fetchGallery]);

  // Initial load
  useState(() => {
    fetchGallery(true);
  });

  return {
    artworks,
    loading,
    error,
    hasMore,
    loadMore,
    refresh,
  };
}
