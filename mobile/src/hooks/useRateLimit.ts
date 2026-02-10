/**
 * Hook for managing rate limit status
 */
import {useState, useEffect, useCallback} from 'react';
import {getRateLimitStatus} from '../services/purchases';
import type {RateLimitStatus} from '../types/purchases';

interface UseRateLimitReturn extends RateLimitStatus {
  isLoading: boolean;
  remaining: number;
  isLimitReached: boolean;
  refresh: () => Promise<void>;
}

/**
 * Hook for fetching and managing rate limit status
 *
 * Provides:
 * - currentUsage: Current usage count
 * - limit: Monthly limit (3 for free users)
 * - resetDate: ISO date string when limit resets
 * - isPremium: Whether user has premium (unlimited)
 * - isLoading: Loading state
 * - remaining: Computed remaining count (limit - currentUsage)
 * - isLimitReached: Whether user has reached limit (currentUsage >= limit)
 * - refresh: Function to re-fetch status from backend
 */
export const useRateLimit = (): UseRateLimitReturn => {
  const [status, setStatus] = useState<RateLimitStatus>({
    current_usage: 0,
    limit: 3,
    reset_date: new Date().toISOString(),
    is_premium: false,
  });
  const [isLoading, setIsLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      const rateLimitStatus = await getRateLimitStatus();
      setStatus(rateLimitStatus);
    } catch (error) {
      console.error('Error fetching rate limit status:', error);
      // Keep existing status on error
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto-fetch on mount
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Computed values
  const remaining = Math.max(0, status.limit - status.current_usage);
  const isLimitReached = status.current_usage >= status.limit && !status.is_premium;

  return {
    current_usage: status.current_usage,
    limit: status.limit,
    reset_date: status.reset_date,
    is_premium: status.is_premium,
    isLoading,
    remaining,
    isLimitReached,
    refresh: fetchStatus,
  };
};
