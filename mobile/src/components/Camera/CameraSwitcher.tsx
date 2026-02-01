/**
 * Camera front/back switcher button
 */
import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';

interface CameraSwitcherProps {
  onToggle: () => void;
}

export default function CameraSwitcher({ onToggle }: CameraSwitcherProps) {
  return (
    <TouchableOpacity onPress={onToggle} style={styles.button}>
      <Text style={styles.text}>🔄</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    fontSize: 24,
  },
});
