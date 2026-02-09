/**
 * Processing result screen with before/after slider, metadata, and actions
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Dimensions,
  Share,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { MainStackParamList } from '../../navigation/types';
import { getJobStatus } from '../../services/processing';
import { useProcessing } from '../../hooks/useProcessing';
import { ProcessingJob } from '../../types/processing';
import BeforeAfterSlider from '../../components/Processing/BeforeAfterSlider';

type ProcessingResultScreenProps = {
  navigation: NativeStackNavigationProp<
    MainStackParamList,
    'ProcessingResult'
  >;
  route: RouteProp<MainStackParamList, 'ProcessingResult'>;
};

const SCREEN_WIDTH = Dimensions.get('window').width;
const SCREEN_HEIGHT = Dimensions.get('window').height;

export default function ProcessingResultScreen({
  navigation,
  route,
}: ProcessingResultScreenProps) {
  const { jobId, photoId } = route.params;
  const { reprocess } = useProcessing();
  const [job, setJob] = useState<ProcessingJob | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadJobStatus();
  }, [jobId]);

  const loadJobStatus = async () => {
    try {
      const jobData = await getJobStatus(jobId);
      setJob(jobData);
    } catch (error) {
      console.error('Failed to load job status:', error);
      Alert.alert('Error', 'Failed to load processing result.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveToDevice = async () => {
    if (!job || !job.result_url) {
      return;
    }

    try {
      // TODO: Implement save to device using CameraRoll or MediaLibrary
      // For now, show a placeholder alert
      Alert.alert(
        'Save to Device',
        'Image download and save functionality will be implemented with platform-specific permissions.',
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to save image to device.');
    }
  };

  const handleShare = async () => {
    if (!job || !job.result_url) {
      return;
    }

    try {
      await Share.share({
        message: 'Check out my iris art!',
        url: job.result_url,
      });
    } catch (error) {
      console.error('Failed to share:', error);
    }
  };

  const handleReprocess = async () => {
    try {
      const newJobId = await reprocess(jobId);
      Alert.alert('Processing Started', 'Your photo is being reprocessed.', [
        {
          text: 'OK',
          onPress: () => navigation.goBack(),
        },
      ]);
    } catch (error) {
      Alert.alert('Error', 'Failed to start reprocessing. Please try again.');
    }
  };

  const handleRecapture = () => {
    navigation.navigate('Camera');
  };

  // Loading state
  if (loading || !job) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading result...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Still processing (user navigated directly before completion)
  if (job.status === 'processing' || job.status === 'pending') {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>
            Processing: {job.current_step || 'Starting...'}
          </Text>
          <Text style={styles.progressText}>{job.progress}%</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Error state
  if (job.status === 'failed') {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}>
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorTitle}>Processing Failed</Text>
          <Text style={styles.errorMessage}>
            {job.error_message || 'An error occurred during processing.'}
          </Text>
          {job.suggestion && (
            <Text style={styles.errorSuggestion}>{job.suggestion}</Text>
          )}

          <View style={styles.errorActions}>
            {job.error_type === 'quality_issue' ? (
              <TouchableOpacity
                style={styles.primaryButton}
                onPress={handleRecapture}>
                <Text style={styles.primaryButtonText}>
                  📷 Recapture Photo
                </Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={styles.primaryButton}
                onPress={handleReprocess}>
                <Text style={styles.primaryButtonText}>🔄 Try Again</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </SafeAreaView>
    );
  }

  // Success state with before/after slider
  const sliderHeight = SCREEN_HEIGHT * 0.6;

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>←</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.shareButton} onPress={handleShare}>
          <Text style={styles.shareButtonText}>↗</Text>
        </TouchableOpacity>
      </View>

      {/* Before/After Slider (Hero) */}
      <View style={styles.sliderContainer}>
        <BeforeAfterSlider
          originalUrl={job.original_url || ''}
          processedUrl={job.result_url || ''}
          width={SCREEN_WIDTH}
          height={sliderHeight}
        />
      </View>

      {/* Metadata */}
      <View style={styles.metadataContainer}>
        <View style={styles.metadataItem}>
          <Text style={styles.metadataLabel}>Resolution</Text>
          <Text style={styles.metadataValue}>
            {job.result_width} × {job.result_height}
          </Text>
        </View>
        <View style={styles.metadataItem}>
          <Text style={styles.metadataLabel}>Processing Time</Text>
          <Text style={styles.metadataValue}>
            {job.processing_time_ms
              ? `${(job.processing_time_ms / 1000).toFixed(1)}s`
              : 'N/A'}
          </Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={handleSaveToDevice}>
          <Text style={styles.actionButtonText}>💾 Save</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
          <Text style={styles.actionButtonText}>📤 Share</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={handleReprocess}>
          <Text style={styles.actionButtonText}>🔄 Reprocess</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backButtonText: {
    color: '#fff',
    fontSize: 28,
  },
  shareButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  shareButtonText: {
    color: '#007AFF',
    fontSize: 28,
  },
  sliderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  metadataContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  metadataItem: {
    alignItems: 'center',
  },
  metadataLabel: {
    color: '#999',
    fontSize: 12,
    marginBottom: 4,
  },
  metadataValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  actionButton: {
    flex: 1,
    marginHorizontal: 8,
    paddingVertical: 12,
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 16,
  },
  progressText: {
    color: '#007AFF',
    fontSize: 14,
    marginTop: 8,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  errorIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  errorTitle: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  errorMessage: {
    color: '#999',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 12,
  },
  errorSuggestion: {
    color: '#007AFF',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 24,
  },
  errorActions: {
    width: '100%',
    paddingHorizontal: 32,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
