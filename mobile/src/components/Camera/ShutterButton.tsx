/**
 * Shutter button for photo capture
 */
import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

interface ShutterButtonProps {
  onCapture: () => void;
  disabled?: boolean;
}

export default function ShutterButton({
  onCapture,
  disabled = false,
}: ShutterButtonProps) {
  return (
    <Pressable
      onPress={onCapture}
      disabled={disabled}
      style={({ pressed }) => [
        styles.container,
        pressed && styles.pressed,
        disabled && styles.disabled,
      ]}>
      <View style={styles.inner} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
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
    opacity: 0.5,
  },
});
