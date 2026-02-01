/**
 * Iris guide overlay with circular cutout
 */
import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const GUIDE_SIZE = SCREEN_WIDTH * 0.6; // 60% of screen width
const GUIDE_RADIUS = GUIDE_SIZE / 2;

export default function IrisGuideOverlay() {
  return (
    <View style={styles.container}>
      {/* Top overlay */}
      <View
        style={[
          styles.overlay,
          {
            height: (SCREEN_HEIGHT - GUIDE_SIZE) / 2,
          },
        ]}
      />

      {/* Middle row with side overlays and guide circle */}
      <View style={styles.middleRow}>
        <View
          style={[
            styles.overlay,
            {
              width: (SCREEN_WIDTH - GUIDE_SIZE) / 2,
            },
          ]}
        />
        <View style={styles.guideCircle} />
        <View
          style={[
            styles.overlay,
            {
              width: (SCREEN_WIDTH - GUIDE_SIZE) / 2,
            },
          ]}
        />
      </View>

      {/* Bottom overlay */}
      <View
        style={[
          styles.overlay,
          {
            height: (SCREEN_HEIGHT - GUIDE_SIZE) / 2,
          },
        ]}
      />
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
    height: GUIDE_SIZE,
  },
  guideCircle: {
    width: GUIDE_SIZE,
    height: GUIDE_SIZE,
    borderRadius: GUIDE_RADIUS,
    borderWidth: 3,
    borderColor: '#fff',
  },
});
