/**
 * Full-screen photo detail view with pinch-to-zoom and delete
 */
import React from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  Alert,
  Dimensions,
  Text,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { GestureDetector, Gesture } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';
import FastImage from 'react-native-fast-image';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { MainStackParamList } from '../../navigation/types';
import api from '../../services/api';
import { Photo } from '../../types/photo';
import { useProcessing } from '../../hooks/useProcessing';
import { useProcessingStore } from '../../store/processingStore';
import { useJobProgress } from '../../hooks/useJobProgress';

type PhotoDetailScreenProps = {
  navigation: NativeStackNavigationProp<MainStackParamList, 'PhotoDetail'>;
  route: RouteProp<MainStackParamList, 'PhotoDetail'>;
};

const SCREEN_WIDTH = Dimensions.get('window').width;
const SCREEN_HEIGHT = Dimensions.get('window').height;

export default function PhotoDetailScreen({
  navigation,
  route,
}: PhotoDetailScreenProps) {
  const { photoId } = route.params;
  const queryClient = useQueryClient();
  const { startProcessing } = useProcessing();
  const processingJob = useProcessingStore((state) =>
    state.getJobForPhoto(photoId),
  );
  const { updateJob } = useProcessingStore();

  // WebSocket progress updates
  const jobProgress = useJobProgress(processingJob?.jobId || null);

  // Update store when WebSocket sends updates
  React.useEffect(() => {
    if (processingJob && jobProgress.status) {
      updateJob(processingJob.jobId, {
        status: jobProgress.status as any,
        progress: jobProgress.progress,
        step: jobProgress.step,
        error: jobProgress.error,
        result: jobProgress.result,
      });

      // Invalidate photos cache when completed
      if (jobProgress.status === 'completed') {
        queryClient.invalidateQueries({ queryKey: ['photos'] });
      }
    }
  }, [
    processingJob,
    jobProgress.status,
    jobProgress.progress,
    jobProgress.step,
    jobProgress.error,
    jobProgress.result,
  ]);

  // Fetch photo details (or use cached data)
  const { data: photo, isLoading } = useQuery({
    queryKey: ['photos', photoId],
    queryFn: async () => {
      const response = await api.get<Photo>(`/photos/${photoId}`);
      return response.data;
    },
    staleTime: 60_000,
  });

  // Pinch-to-zoom state
  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);

  const pinchGesture = Gesture.Pinch()
    .onUpdate((event) => {
      scale.value = Math.max(1, Math.min(savedScale.value * event.scale, 5));
    })
    .onEnd(() => {
      savedScale.value = scale.value;
      // Animate back to 1x if below threshold
      if (scale.value < 1.1) {
        scale.value = withSpring(1);
        savedScale.value = 1;
      }
    });

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ scale: scale.value }],
    };
  });

  const handleDelete = () => {
    Alert.alert(
      'Delete Photo?',
      'This action cannot be undone.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/photos/${photoId}`);
              // Invalidate photos cache to refresh gallery
              queryClient.invalidateQueries({ queryKey: ['photos'] });
              navigation.goBack();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete photo. Please try again.');
            }
          },
        },
      ],
      { cancelable: true }
    );
  };

  const handleProcess = async () => {
    try {
      const jobId = await startProcessing(photoId);
      console.log('Processing started:', jobId);
    } catch (error) {
      Alert.alert('Error', 'Failed to start processing. Please try again.');
    }
  };

  const handleViewResult = () => {
    if (processingJob && processingJob.jobId) {
      navigation.navigate('ProcessingResult', {
        jobId: processingJob.jobId,
        photoId: photoId,
      });
    }
  };

  if (isLoading || !photo) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      </SafeAreaView>
    );
  }

  // Determine button state
  const showProcessButton =
    !processingJob || processingJob.status === 'failed';
  const showProgressIndicator =
    processingJob &&
    (processingJob.status === 'pending' || processingJob.status === 'processing');
  const showViewResultButton =
    processingJob && processingJob.status === 'completed';

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.headerButton}
          onPress={() => navigation.goBack()}>
          <Text style={styles.headerButtonText}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerRight}>
          {showProcessButton && (
            <TouchableOpacity
              style={styles.processButton}
              onPress={handleProcess}>
              <Text style={styles.processButtonText}>✨ Process</Text>
            </TouchableOpacity>
          )}
          {showProgressIndicator && (
            <View style={styles.progressIndicator}>
              <ActivityIndicator size="small" color="#007AFF" />
              <Text style={styles.progressText}>
                {Math.round(processingJob.progress)}%
              </Text>
            </View>
          )}
          {showViewResultButton && (
            <TouchableOpacity
              style={styles.viewResultButton}
              onPress={handleViewResult}>
              <Text style={styles.viewResultButtonText}>View Result</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity style={styles.headerButton} onPress={handleDelete}>
            <Text style={styles.headerButtonText}>🗑</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Photo with pinch-to-zoom */}
      <View style={styles.photoContainer}>
        <GestureDetector gesture={pinchGesture}>
          <Animated.View style={[styles.imageWrapper, animatedStyle]}>
            <FastImage
              source={{
                uri: photo.original_url,
                priority: FastImage.priority.high,
                cache: FastImage.cacheControl.immutable,
              }}
              style={styles.image}
              resizeMode={FastImage.resizeMode.contain}
            />
          </Animated.View>
        </GestureDetector>
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
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerButtonText: {
    color: '#fff',
    fontSize: 24,
  },
  processButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  processButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  progressIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  progressText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
  },
  viewResultButton: {
    backgroundColor: '#34C759',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  viewResultButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  photoContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  imageWrapper: {
    width: SCREEN_WIDTH,
    height: SCREEN_HEIGHT - 100,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
