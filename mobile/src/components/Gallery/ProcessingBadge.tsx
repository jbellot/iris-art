/**
 * Processing status badge overlay for gallery thumbnails
 */
import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  Easing,
} from 'react-native-reanimated';

interface ProcessingBadgeProps {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  step: string | null;
}

export default function ProcessingBadge({
  status,
  progress,
  step,
}: ProcessingBadgeProps) {
  const animatedProgress = useSharedValue(0);

  useEffect(() => {
    animatedProgress.value = withTiming(progress, {
      duration: 300,
      easing: Easing.out(Easing.cubic),
    });
  }, [progress]);

  // Note: progressStyle would be used with Animated SVG if we had one
  // For now, we're using a simpler circular container

  // Processing state: show circular progress ring
  if (status === 'processing' || status === 'pending') {
    return (
      <View style={styles.container}>
        <View style={styles.progressContainer}>
          {/* SVG would be ideal here, but for simplicity use a circular progress ring */}
          <View style={styles.circleContainer}>
            <Text style={styles.progressText}>{Math.round(progress)}%</Text>
          </View>
          {step && <Text style={styles.stepText}>{step}</Text>}
        </View>
      </View>
    );
  }

  // Completed state: green checkmark
  if (status === 'completed') {
    return (
      <View style={[styles.container, styles.completedContainer]}>
        <Text style={styles.completedIcon}>✓</Text>
      </View>
    );
  }

  // Failed state: red X with retry hint
  if (status === 'failed') {
    return (
      <View style={[styles.container, styles.failedContainer]}>
        <Text style={styles.failedIcon}>✕</Text>
        <Text style={styles.retryText}>Tap to retry</Text>
      </View>
    );
  }

  return null;
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 8,
  },
  progressContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  circleContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    borderWidth: 3,
    borderColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 122, 255, 0.1)',
  },
  progressText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  stepText: {
    color: '#fff',
    fontSize: 12,
    marginTop: 8,
    textAlign: 'center',
    paddingHorizontal: 8,
  },
  completedContainer: {
    backgroundColor: 'rgba(52, 199, 89, 0.2)',
  },
  completedIcon: {
    color: '#34C759',
    fontSize: 32,
    fontWeight: 'bold',
  },
  failedContainer: {
    backgroundColor: 'rgba(255, 59, 48, 0.2)',
  },
  failedIcon: {
    color: '#FF3B30',
    fontSize: 32,
    fontWeight: 'bold',
  },
  retryText: {
    color: '#FF3B30',
    fontSize: 11,
    marginTop: 4,
  },
});
