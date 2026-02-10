/**
 * ProgressiveImage component - cross-fades from low-res preview to full-res
 */

import React, {useState} from 'react';
import {StyleSheet, View, ActivityIndicator, Text, Image} from 'react-native';
import FastImage from '@d11/react-native-fast-image';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  Easing,
} from 'react-native-reanimated';

interface ProgressiveImageProps {
  previewUrl: string | null;
  fullUrl: string | null;
  onFullLoaded?: () => void;
  style?: any;
}

const AnimatedFastImage = Animated.createAnimatedComponent(FastImage);
const AnimatedImage = Animated.createAnimatedComponent(Image);

export function ProgressiveImage({
  previewUrl,
  fullUrl,
  onFullLoaded,
  style,
}: ProgressiveImageProps) {
  const [fullImageLoaded, setFullImageLoaded] = useState(false);

  // Opacity values for cross-fade
  const previewOpacity = useSharedValue(1);
  const fullOpacity = useSharedValue(0);

  const handleFullImageLoad = () => {
    setFullImageLoaded(true);

    // Animate cross-fade: fade out preview, fade in full
    previewOpacity.value = withTiming(0, {
      duration: 300,
      easing: Easing.inOut(Easing.ease),
    });
    fullOpacity.value = withTiming(1, {
      duration: 300,
      easing: Easing.inOut(Easing.ease),
    });

    onFullLoaded?.();
  };

  const previewStyle = useAnimatedStyle(() => ({
    opacity: previewOpacity.value,
  }));

  const fullStyle = useAnimatedStyle(() => ({
    opacity: fullOpacity.value,
  }));

  // If no preview or full URL, show placeholder
  if (!previewUrl && !fullUrl) {
    return (
      <View style={[styles.container, style, styles.placeholderContainer]}>
        <Text style={styles.placeholderText}>No image available</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, style]}>
      {/* Preview image (low-res, slightly blurred) */}
      {previewUrl && (
        <AnimatedImage
          source={{uri: previewUrl}}
          style={[styles.image, previewStyle]}
          resizeMode="cover"
          blurRadius={3}
        />
      )}

      {/* Full resolution image */}
      {fullUrl && (
        <AnimatedFastImage
          source={{uri: fullUrl}}
          style={[styles.image, fullStyle]}
          resizeMode={FastImage.resizeMode.cover}
          onLoad={handleFullImageLoad}
        />
      )}

      {/* Loading indicator while full image loads */}
      {fullUrl && !fullImageLoaded && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#FFFFFF" />
          <Text style={styles.loadingText}>Enhancing...</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    width: '100%',
    aspectRatio: 1,
    backgroundColor: '#1E1E1E',
    borderRadius: 12,
    overflow: 'hidden',
  },
  image: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    width: '100%',
    height: '100%',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },
  loadingText: {
    marginTop: 8,
    fontSize: 14,
    color: '#FFFFFF',
    fontWeight: '500',
  },
  placeholderContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 14,
    color: '#AAAAAA',
  },
});
