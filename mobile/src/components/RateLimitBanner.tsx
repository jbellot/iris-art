/**
 * Rate limit banner component - shows AI generation quota status
 */
import React from 'react';
import {View, Text, TouchableOpacity, StyleSheet} from 'react-native';

interface RateLimitBannerProps {
  currentUsage: number;
  limit: number;
  resetDate: string;
  onUpgrade: () => void;
}

/**
 * RateLimitBanner shows remaining AI generation quota for free users
 *
 * Displays info banner when usage < limit
 * Displays warning banner when usage >= limit (with upgrade CTA)
 *
 * @param currentUsage - Current AI generation count this month
 * @param limit - Monthly limit for free users
 * @param resetDate - ISO date string when quota resets
 * @param onUpgrade - Callback when user taps upgrade button
 */
export default function RateLimitBanner({
  currentUsage,
  limit,
  resetDate,
  onUpgrade,
}: RateLimitBannerProps) {
  const remaining = Math.max(0, limit - currentUsage);
  const isLimitReached = currentUsage >= limit;

  // Format reset date
  const formatResetDate = (isoDate: string): string => {
    const date = new Date(isoDate);
    const now = new Date();
    const diffDays = Math.ceil(
      (date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24),
    );

    if (diffDays === 0) {
      return 'today';
    } else if (diffDays === 1) {
      return 'tomorrow';
    } else {
      return `in ${diffDays} days`;
    }
  };

  if (isLimitReached) {
    // Warning banner - limit reached
    return (
      <View style={[styles.banner, styles.warningBanner]}>
        <View style={styles.content}>
          <Text style={styles.warningText}>
            Monthly limit reached. Resets {formatResetDate(resetDate)}.
          </Text>
          <TouchableOpacity
            style={styles.upgradeButton}
            onPress={onUpgrade}
            activeOpacity={0.8}>
            <Text style={styles.upgradeButtonText}>Upgrade</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Info banner - quota remaining
  return (
    <View style={[styles.banner, styles.infoBanner]}>
      <Text style={styles.infoText}>
        You have {remaining} free AI generation{remaining !== 1 ? 's' : ''}{' '}
        this month
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginHorizontal: 16,
    marginVertical: 8,
  },
  infoBanner: {
    backgroundColor: '#1E3A8A',
  },
  warningBanner: {
    backgroundColor: '#92400E',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  infoText: {
    fontSize: 14,
    color: '#93C5FD',
    fontWeight: '500',
  },
  warningText: {
    fontSize: 14,
    color: '#FCD34D',
    fontWeight: '500',
    flex: 1,
    marginRight: 12,
  },
  upgradeButton: {
    backgroundColor: '#7C3AED',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  upgradeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
});
