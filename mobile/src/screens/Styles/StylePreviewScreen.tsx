/**
 * StylePreviewScreen - preview styled result with progressive loading
 */

import React, {useEffect, useState} from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Share,
  Image,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {useNavigation, useRoute, RouteProp} from '@react-navigation/native';
import {NativeStackNavigationProp} from '@react-navigation/native-stack';
// Note: CameraRoll requires @react-native-camera-roll/camera-roll package
// For now, we'll use a placeholder that shows an alert
const CameraRoll = {
  save: async (uri: string, options?: any) => {
    // TODO: Install @react-native-camera-roll/camera-roll and implement
    throw new Error('CameraRoll not yet configured');
  },
};
import {ProgressiveImage} from '../../components/Styles/ProgressiveImage';
import {useStyleTransfer} from '../../hooks/useStyleTransfer';
import type {MainStackParamList} from '../../navigation/types';

type StylePreviewScreenRouteProp = RouteProp<
  MainStackParamList,
  'StylePreview'
>;
type StylePreviewScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  'StylePreview'
>;

export function StylePreviewScreen() {
  const route = useRoute<StylePreviewScreenRouteProp>();
  const navigation = useNavigation<StylePreviewScreenNavigationProp>();

  const {photoId, stylePresetId, processingJobId, originalImageUrl} =
    route.params;

  const {applyStyle, activeJob, presets} = useStyleTransfer({
    photoId,
    processingJobId,
  });

  const [jobSubmitted, setJobSubmitted] = useState(false);

  // Get the selected style preset info
  const allPresets = [...(presets?.free || []), ...(presets?.premium || [])];
  const selectedPreset = allPresets.find(p => p.id === stylePresetId);

  // Submit style job on mount
  useEffect(() => {
    if (!jobSubmitted) {
      applyStyle(stylePresetId).catch(err => {
        console.error('Failed to submit style job:', err);
        Alert.alert('Error', 'Failed to apply style. Please try again.');
      });
      setJobSubmitted(true);
    }
  }, [applyStyle, stylePresetId, jobSubmitted]);

  const handleTryAnother = () => {
    navigation.goBack();
  };

  const handleSave = async () => {
    if (!activeJob?.resultUrl) {
      Alert.alert('Not Ready', 'Please wait for styling to complete.');
      return;
    }

    try {
      await CameraRoll.save(activeJob.resultUrl, {type: 'photo'});
      Alert.alert('Saved', 'Styled iris saved to your camera roll!');
    } catch (err) {
      console.error('Failed to save image:', err);
      Alert.alert('Error', 'Failed to save image. Please try again.');
    }
  };

  const handleShare = async () => {
    if (!activeJob?.resultUrl) {
      Alert.alert('Not Ready', 'Please wait for styling to complete.');
      return;
    }

    try {
      await Share.share({
        url: activeJob.resultUrl,
        message: `Check out my iris art with ${selectedPreset?.displayName || 'this style'}!`,
      });
    } catch (err) {
      console.error('Failed to share:', err);
    }
  };

  const handleRetry = () => {
    setJobSubmitted(false);
  };

  // Error state
  if (activeJob?.status === 'failed') {
    return (
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
        <View style={styles.header}>
          <Text style={styles.styleName}>
            {selectedPreset?.displayName || 'Style Preview'}
          </Text>
        </View>

        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Something went wrong</Text>
          <Text style={styles.errorMessage}>
            {activeJob.errorMessage || 'Failed to apply style'}
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={handleRetry}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Processing state
  const isProcessing =
    activeJob?.status === 'pending' || activeJob?.status === 'processing';

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.styleName}>
          {selectedPreset?.displayName || 'Style Preview'}
        </Text>
        {isProcessing && (
          <View style={styles.progressContainer}>
            <ActivityIndicator size="small" color="#FFFFFF" />
            <Text style={styles.progressText}>
              {activeJob?.currentStep || 'Processing...'}
            </Text>
          </View>
        )}
      </View>

      {/* Main content */}
      <View style={styles.content}>
        {/* Source image thumbnail for comparison */}
        <View style={styles.comparisonContainer}>
          <View style={styles.comparisonItem}>
            <Image
              source={{uri: originalImageUrl}}
              style={styles.comparisonImage}
              resizeMode="cover"
            />
            <Text style={styles.comparisonLabel}>Original</Text>
          </View>

          {/* Styled result */}
          <View style={styles.comparisonItem}>
            {isProcessing && !activeJob?.previewUrl ? (
              <View style={styles.loadingPlaceholder}>
                <ActivityIndicator size="large" color="#FFFFFF" />
              </View>
            ) : (
              <ProgressiveImage
                previewUrl={activeJob?.previewUrl || null}
                fullUrl={activeJob?.resultUrl || null}
                style={styles.comparisonImage}
              />
            )}
            <Text style={styles.comparisonLabel}>Styled</Text>
          </View>
        </View>
      </View>

      {/* Actions bar */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={handleTryAnother}>
          <Text style={styles.actionButtonText}>Try Another Style</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.actionButton,
            styles.primaryButton,
            !activeJob?.resultUrl && styles.disabledButton,
          ]}
          onPress={handleSave}
          disabled={!activeJob?.resultUrl}>
          <Text
            style={[
              styles.actionButtonText,
              styles.primaryButtonText,
              !activeJob?.resultUrl && styles.disabledButtonText,
            ]}>
            Save
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.actionButton,
            !activeJob?.resultUrl && styles.disabledButton,
          ]}
          onPress={handleShare}
          disabled={!activeJob?.resultUrl}>
          <Text
            style={[
              styles.actionButtonText,
              !activeJob?.resultUrl && styles.disabledButtonText,
            ]}>
            Share
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  styleName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  progressText: {
    fontSize: 14,
    color: '#AAAAAA',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  comparisonContainer: {
    flexDirection: 'row',
    gap: 16,
    justifyContent: 'center',
  },
  comparisonItem: {
    flex: 1,
    alignItems: 'center',
  },
  comparisonImage: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 12,
    backgroundColor: '#1E1E1E',
    marginBottom: 8,
  },
  comparisonLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#AAAAAA',
  },
  loadingPlaceholder: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 12,
    backgroundColor: '#1E1E1E',
    justifyContent: 'center',
    alignItems: 'center',
  },
  actions: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: '#2A2A2A',
  },
  actionButton: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#2A2A2A',
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#6200EA',
  },
  disabledButton: {
    backgroundColor: '#1E1E1E',
    opacity: 0.5,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  primaryButtonText: {
    color: '#FFFFFF',
  },
  disabledButtonText: {
    color: '#666666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FF6B6B',
    marginBottom: 8,
  },
  errorMessage: {
    fontSize: 16,
    color: '#AAAAAA',
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
    backgroundColor: '#6200EA',
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
