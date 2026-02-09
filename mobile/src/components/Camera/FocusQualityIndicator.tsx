/**
 * Focus quality indicator showing sharpness status
 */
import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  interpolateColor,
} from 'react-native-reanimated';

interface FocusQualityIndicatorProps {
  irisDetected: boolean;
  focusQuality: number;
  isBlurry: boolean;
  isReady: boolean;
}

export default function FocusQualityIndicator({
  irisDetected,
  focusQuality,
  isBlurry,
  isReady,
}: FocusQualityIndicatorProps) {
  // Don't show until iris is detected
  if (!irisDetected || !isReady) {
    return null;
  }

  const colorProgress = useSharedValue(0); // 0 = red, 0.5 = yellow, 1 = green

  useEffect(() => {
    if (focusQuality > 150) {
      colorProgress.value = withSpring(1, { damping: 15 });
    } else if (focusQuality >= 80) {
      colorProgress.value = withSpring(0.5, { damping: 15 });
    } else {
      colorProgress.value = withSpring(0, { damping: 15 });
    }
  }, [focusQuality, colorProgress]);

  const animatedStyle = useAnimatedStyle(() => {
    const color = interpolateColor(
      colorProgress.value,
      [0, 0.5, 1],
      ['#FF3B30', '#FFB800', '#4CAF50']
    );

    return {
      color,
    };
  });

  const getLabel = () => {
    if (focusQuality > 150) {
      return 'Sharp';
    } else if (focusQuality >= 80) {
      return 'Slightly blurry';
    } else {
      return 'Too blurry';
    }
  };

  const getIcon = () => {
    if (focusQuality > 150) {
      return '✓';
    } else if (focusQuality >= 80) {
      return '⚠';
    } else {
      return '✕';
    }
  };

  return (
    <View style={styles.container}>
      <Animated.Text style={[styles.icon, animatedStyle]}>
        {getIcon()}
      </Animated.Text>
      <Animated.Text style={[styles.label, animatedStyle]}>
        {getLabel()}
      </Animated.Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 140,
    left: 16,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  icon: {
    fontSize: 16,
    fontWeight: 'bold',
    marginRight: 6,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
  },
});
