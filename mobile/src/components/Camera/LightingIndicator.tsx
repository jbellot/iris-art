/**
 * Lighting indicator showing brightness status
 */
import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  interpolateColor,
} from 'react-native-reanimated';

interface LightingIndicatorProps {
  irisDetected: boolean;
  lightingStatus: 'too_dark' | 'too_bright' | 'good';
  isReady: boolean;
}

export default function LightingIndicator({
  irisDetected,
  lightingStatus,
  isReady,
}: LightingIndicatorProps) {
  // Don't show until iris is detected
  if (!irisDetected || !isReady) {
    return null;
  }

  const colorProgress = useSharedValue(0.5); // 0.5 = amber, 1 = green

  useEffect(() => {
    if (lightingStatus === 'good') {
      colorProgress.value = withSpring(1, { damping: 15 });
    } else {
      colorProgress.value = withSpring(0.5, { damping: 15 });
    }
  }, [lightingStatus, colorProgress]);

  const animatedStyle = useAnimatedStyle(() => {
    const color = interpolateColor(
      colorProgress.value,
      [0.5, 1],
      ['#FFB800', '#4CAF50']
    );

    return {
      color,
    };
  });

  const getLabel = () => {
    if (lightingStatus === 'too_dark') {
      return 'Find more light';
    } else if (lightingStatus === 'too_bright') {
      return 'Reduce glare';
    } else {
      return 'Good lighting';
    }
  };

  const getIcon = () => {
    if (lightingStatus === 'good') {
      return '☀';
    } else {
      return '⚠';
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
    right: 16,
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
