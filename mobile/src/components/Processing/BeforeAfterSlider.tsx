/**
 * Before/After image comparison slider with draggable divider
 */
import React from 'react';
import { View, StyleSheet, Text } from 'react-native';
import { GestureDetector, Gesture } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  runOnJS,
} from 'react-native-reanimated';
import FastImage from '@d11/react-native-fast-image';

interface BeforeAfterSliderProps {
  originalUrl: string;
  processedUrl: string;
  width: number;
  height: number;
}

export default function BeforeAfterSlider({
  originalUrl,
  processedUrl,
  width,
  height,
}: BeforeAfterSliderProps) {
  // Slider position (0 to width)
  const sliderPosition = useSharedValue(width / 2);

  const panGesture = Gesture.Pan()
    .onUpdate((event) => {
      // Constrain slider to image bounds
      const newPosition = Math.max(0, Math.min(width, event.x));
      sliderPosition.value = newPosition;
    })
    .onEnd(() => {
      // Optional: snap to center if close
      if (
        Math.abs(sliderPosition.value - width / 2) < 20
      ) {
        sliderPosition.value = width / 2;
      }
    });

  const afterImageStyle = useAnimatedStyle(() => {
    return {
      width: sliderPosition.value,
    };
  });

  const dividerStyle = useAnimatedStyle(() => {
    return {
      left: sliderPosition.value - 1,
    };
  });

  const handleStyle = useAnimatedStyle(() => {
    return {
      left: sliderPosition.value - 20,
    };
  });

  return (
    <View style={[styles.container, { width, height }]}>
      {/* Before image (full background) */}
      <FastImage
        source={{
          uri: originalUrl,
          priority: FastImage.priority.high,
          cache: FastImage.cacheControl.immutable,
        }}
        style={[styles.image, { width, height }]}
        resizeMode={FastImage.resizeMode.contain}
      />

      {/* Label: Before */}
      <View style={styles.labelBefore}>
        <Text style={styles.labelText}>Before</Text>
      </View>

      {/* After image (clipped by slider position) */}
      <Animated.View
        style={[
          styles.afterContainer,
          { height },
          afterImageStyle,
        ]}>
        <FastImage
          source={{
            uri: processedUrl,
            priority: FastImage.priority.high,
            cache: FastImage.cacheControl.immutable,
          }}
          style={[styles.image, { width, height }]}
          resizeMode={FastImage.resizeMode.contain}
        />
      </Animated.View>

      {/* Label: After */}
      <View style={styles.labelAfter}>
        <Text style={styles.labelText}>After</Text>
      </View>

      {/* Divider line */}
      <Animated.View style={[styles.divider, { height }, dividerStyle]} />

      {/* Draggable handle */}
      <GestureDetector gesture={panGesture}>
        <Animated.View style={[styles.handle, handleStyle]}>
          <View style={styles.handleCircle}>
            <Text style={styles.handleArrows}>⟷</Text>
          </View>
        </Animated.View>
      </GestureDetector>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    backgroundColor: '#000',
  },
  image: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
  afterContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    overflow: 'hidden',
  },
  labelBefore: {
    position: 'absolute',
    top: 16,
    left: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  labelAfter: {
    position: 'absolute',
    top: 16,
    right: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  labelText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  divider: {
    position: 'absolute',
    width: 2,
    backgroundColor: '#fff',
    top: 0,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 4,
  },
  handle: {
    position: 'absolute',
    top: '50%',
    width: 40,
    height: 40,
    marginTop: -20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  handleCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  handleArrows: {
    color: '#000',
    fontSize: 20,
    fontWeight: 'bold',
  },
});
