/**
 * Gallery hook with React Query for fetching paginated photos
 */
import { useInfiniteQuery } from '@tanstack/react-query';
import api from '../services/api';
import { PhotoListResponse } from '../types/photo';

export function useGallery() {
  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useInfiniteQuery({
    queryKey: ['photos'],
    queryFn: async ({ pageParam = 1 }) => {
      const response = await api.get<PhotoListResponse>('/photos', {
        params: { page: pageParam, page_size: 20 },
      });
      return response.data;
    },
    getNextPageParam: (lastPage) => {
      const { page, page_size, total } = lastPage;
      if (page * page_size < total) return page + 1;
      return undefined;
    },
    initialPageParam: 1,
    staleTime: 60_000, // 1 minute
  });

  // Flatten pages into single photo array
  const photos = data?.pages.flatMap((page) => page.items) ?? [];

  return {
    photos,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  };
}
