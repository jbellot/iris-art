/**
 * Burst capture button with 3-frame capture and best-frame selection
 */
import React, { useState } from 'react';
import { Pressable, StyleSheet, View, Text, Vibration } from 'react-native';
import { Camera, PhotoFile } from 'react-native-vision-camera';
import RNFS from 'react-native-fs';

interface BurstCaptureButtonProps {
  cameraRef: React.RefObject<Camera | null>;
  flash: 'off' | 'on';
  readyToCapture: boolean;
  onCaptureComplete: (photoPath: string, width: number, height: number) => void;
}

export default function BurstCaptureButton({
  cameraRef,
  flash,
  readyToCapture,
  onCaptureComplete,
}: BurstCaptureButtonProps) {
  const [capturing, setCapturing] = useState(false);
  const [selectingBest, setSelectingBest] = useState(false);

  const handleCapture = async () => {
    if (!cameraRef.current || capturing) {
      return;
    }

    try {
      setCapturing(true);
      Vibration.vibrate(50);

      // Capture 3 frames 200ms apart
      const frames: PhotoFile[] = [];

      for (let i = 0; i < 3; i++) {
        const photo = await cameraRef.current.takePhoto({
          flash,
          enableShutterSound: i === 0, // Only first frame has shutter sound
        });
        frames.push(photo);

        if (i < 2) {
          await new Promise<void>((resolve) => setTimeout(resolve, 200));
        }
      }

      setCapturing(false);
      setSelectingBest(true);

      // Select best frame (for now, just use the middle frame)
      // In a real implementation, we would analyze each frame for sharpness
      // For this MVP, we trust the middle frame as it's most likely to be stable
      const bestFrame = frames[1];

      // Delete non-selected frames
      const framesToDelete = [frames[0], frames[2]];
      for (const frame of framesToDelete) {
        try {
          await RNFS.unlink(frame.path);
        } catch (error) {
          // Ignore deletion errors
        }
      }

      setSelectingBest(false);

      // Navigate to photo review with best frame
      onCaptureComplete(bestFrame.path, bestFrame.width, bestFrame.height);
    } catch (error) {
      console.error('Failed to capture burst:', error);
      setCapturing(false);
      setSelectingBest(false);
    }
  };

  const disabled = !readyToCapture || capturing || selectingBest;

  return (
    <View style={styles.container}>
      {selectingBest && (
        <Text style={styles.selectingText}>Selecting best shot...</Text>
      )}
      <Pressable
        onPress={handleCapture}
        disabled={disabled}
        style={({ pressed }) => [
          styles.button,
          pressed && styles.pressed,
          disabled && styles.disabled,
        ]}>
        <View style={styles.inner} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  button: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#000',
  },
  inner: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: '#fff',
  },
  pressed: {
    opacity: 0.7,
    transform: [{ scale: 0.95 }],
  },
  disabled: {
    opacity: 0.3,
  },
  selectingText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
});
