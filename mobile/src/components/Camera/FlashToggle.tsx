/**
 * Flash toggle button
 */
import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { FlashMode } from '../../hooks/useCamera';

interface FlashToggleProps {
  flash: FlashMode;
  onToggle: () => void;
}

export default function FlashToggle({ flash, onToggle }: FlashToggleProps) {
  return (
    <TouchableOpacity
      onPress={onToggle}
      style={[styles.button, flash === 'on' && styles.active]}>
      <Text style={[styles.text, flash === 'on' && styles.activeText]}>
        ⚡ {flash === 'on' ? 'ON' : 'OFF'}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  active: {
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  text: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  activeText: {
    color: '#FFD700',
  },
});
