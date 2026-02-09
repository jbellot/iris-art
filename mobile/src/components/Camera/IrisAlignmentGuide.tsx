/**
 * Iris alignment guide with reactive feedback
 */
import React, { useEffect } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withRepeat,
  withSequence,
  interpolateColor,
} from 'react-native-reanimated';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface IrisAlignmentGuideProps {
  irisDetected: boolean;
  irisCenter: { x: number; y: number };
  irisRadius: number;
  distance: number;
  isReady: boolean;
  readyToCapture: boolean;
}

export default function IrisAlignmentGuide({
  irisDetected,
  irisCenter,
  irisRadius,
  distance,
  isReady,
  readyToCapture,
}: IrisAlignmentGuideProps) {
  const guideSize = SCREEN_WIDTH * 0.6;
  const guideRadius = guideSize / 2;

  // Animation values
  const colorProgress = useSharedValue(0); // 0 = white/gray, 0.5 = yellow, 1 = green
  const pulseScale = useSharedValue(1);

  // Update color based on state
  useEffect(() => {
    if (readyToCapture) {
      colorProgress.value = withSpring(1, { damping: 15 });
      // Gentle pulse animation
      pulseScale.value = withRepeat(
        withSequence(
          withSpring(1.05, { damping: 10 }),
          withSpring(1, { damping: 10 })
        ),
        -1,
        false
      );
    } else if (irisDetected) {
      colorProgress.value = withSpring(0.5, { damping: 15 });
      pulseScale.value = withSpring(1);
    } else {
      colorProgress.value = withSpring(0, { damping: 15 });
      pulseScale.value = withSpring(1);
    }
  }, [irisDetected, readyToCapture, colorProgress, pulseScale]);

  const animatedCircleStyle = useAnimatedStyle(() => {
    const borderColor = interpolateColor(
      colorProgress.value,
      [0, 0.5, 1],
      ['#FFFFFF', '#FFB800', '#4CAF50']
    );

    return {
      borderColor,
      transform: [{ scale: pulseScale.value }],
    };
  });

  // Determine distance hint
  const getDistanceHint = () => {
    if (!irisDetected || !isReady) {
      return 'Position your eye in the circle';
    }

    if (distance < 0.3) {
      return 'Move closer';
    } else if (distance > 0.7) {
      return 'Move away';
    } else if (readyToCapture) {
      return 'Perfect! Hold steady';
    } else {
      return 'Good distance';
    }
  };

  // Determine position hint (if iris detected but off-center)
  const getPositionHint = () => {
    if (!irisDetected || !isReady) {
      return null;
    }

    const centerX = 0.5;
    const centerY = 0.5;
    const threshold = 0.15;

    const dx = irisCenter.x - centerX;
    const dy = irisCenter.y - centerY;

    if (Math.abs(dx) > threshold) {
      return dx > 0 ? 'Move left' : 'Move right';
    }
    if (Math.abs(dy) > threshold) {
      return dy > 0 ? 'Move down' : 'Move up';
    }

    return null;
  };

  const distanceHint = getDistanceHint();
  const positionHint = getPositionHint();

  return (
    <View style={styles.container}>
      {/* Top overlay */}
      <View
        style={[
          styles.overlay,
          {
            height: (SCREEN_HEIGHT - guideSize) / 2,
          },
        ]}
      />

      {/* Middle row with side overlays and guide circle */}
      <View style={styles.middleRow}>
        <View
          style={[
            styles.overlay,
            {
              width: (SCREEN_WIDTH - guideSize) / 2,
            },
          ]}
        />

        {/* Animated guide circle */}
        <Animated.View
          style={[
            styles.guideCircle,
            {
              width: guideSize,
              height: guideSize,
              borderRadius: guideRadius,
            },
            animatedCircleStyle,
          ]}
        />

        <View
          style={[
            styles.overlay,
            {
              width: (SCREEN_WIDTH - guideSize) / 2,
            },
          ]}
        />
      </View>

      {/* Bottom overlay */}
      <View
        style={[
          styles.overlay,
          {
            height: (SCREEN_HEIGHT - guideSize) / 2,
          },
        ]}
      />

      {/* Distance hint text */}
      <View style={styles.hintContainer}>
        <Text style={styles.hintText}>{distanceHint}</Text>
        {positionHint && (
          <Text style={styles.positionHintText}>{positionHint}</Text>
        )}
      </View>

      {/* Getting ready message */}
      {!isReady && (
        <View style={styles.gettingReadyContainer}>
          <Text style={styles.gettingReadyText}>Getting ready...</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
  },
  overlay: {
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
  },
  middleRow: {
    flexDirection: 'row',
    height: SCREEN_WIDTH * 0.6,
  },
  guideCircle: {
    borderWidth: 4,
  },
  hintContainer: {
    position: 'absolute',
    top: '25%',
    alignItems: 'center',
  },
  hintText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  positionHintText: {
    color: '#FFB800',
    fontSize: 14,
    fontWeight: '500',
    marginTop: 8,
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  gettingReadyContainer: {
    position: 'absolute',
    top: '20%',
    alignItems: 'center',
  },
  gettingReadyText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '500',
    textShadowColor: 'rgba(0, 0, 0, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
});
