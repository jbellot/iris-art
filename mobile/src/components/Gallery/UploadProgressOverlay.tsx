/**
 * Upload progress overlay for photo thumbnails
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface UploadProgressOverlayProps {
  progress: number; // 0-100
  status: 'uploading' | 'failed';
  error?: string;
}

export default function UploadProgressOverlay({
  progress,
  status,
  error,
}: UploadProgressOverlayProps) {
  if (status === 'failed') {
    return (
      <View style={styles.overlay}>
        <View style={styles.errorContent}>
          <Text style={styles.errorIcon}>✕</Text>
          <Text style={styles.errorText}>Tap to retry</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.overlay}>
      <Text style={styles.progressText}>{Math.round(progress)}%</Text>
      <View style={styles.progressBarContainer}>
        <View style={[styles.progressBar, { width: `${progress}%` }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 8,
  },
  progressText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  progressBarContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#007AFF',
  },
  errorContent: {
    alignItems: 'center',
  },
  errorIcon: {
    color: '#FF3B30',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  errorText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
});
