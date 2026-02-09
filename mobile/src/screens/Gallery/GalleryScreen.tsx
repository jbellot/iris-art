/**
 * Gallery screen with masonry layout, upload progress, and photo management
 */
import React, { useMemo } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  Dimensions,
  Text,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainStackParamList } from '../../navigation/types';
import { useGallery } from '../../hooks/useGallery';
import { useUpload, useUploadStore } from '../../hooks/useUpload';
import { useProcessingStore } from '../../store/processingStore';
import { Photo } from '../../types/photo';
import PhotoThumbnail from '../../components/Gallery/PhotoThumbnail';
import EmptyGallery from '../../components/Gallery/EmptyGallery';

type GalleryScreenProps = {
  navigation: NativeStackNavigationProp<MainStackParamList, 'Gallery'>;
};

const SCREEN_WIDTH = Dimensions.get('window').width;
const PADDING = 4;
const COLUMN_WIDTH = (SCREEN_WIDTH - PADDING * 3) / 2;

export default function GalleryScreen({ navigation }: GalleryScreenProps) {
  const {
    photos,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useGallery();

  const { retryUpload } = useUpload();
  const uploads = useUploadStore((state) => state.getAllUploads());
  const processingJobs = useProcessingStore((state) => state.getAllJobs());

  // Merge upload state with API photos
  const galleryItems = useMemo(() => {
    // Get uploads that are still in progress or failed
    const activeUploads = uploads.filter(
      (upload) => upload.status === 'uploading' || upload.status === 'failed'
    );

    // Create temporary Photo objects for active uploads
    const uploadPhotos: Photo[] = activeUploads.map((upload) => ({
      id: upload.photoId || upload.id, // Use photoId if available, else local ID
      user_id: '',
      s3_key: '',
      original_url: upload.photoPath, // Use local file:// URI
      thumbnail_url: upload.photoPath,
      width: upload.width,
      height: upload.height,
      upload_status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }));

    // Prepend uploading photos to the list (newest first)
    return [...uploadPhotos, ...photos];
  }, [uploads, photos]);

  const handlePhotoPress = (photo: Photo) => {
    // Find if this photo has an upload state
    const uploadState = uploads.find(
      (u) => u.photoId === photo.id || u.id === photo.id
    );

    // If failed, trigger retry
    if (uploadState && uploadState.status === 'failed') {
      retryUpload(uploadState.id);
      return;
    }

    // Otherwise, navigate to detail view (only for completed photos)
    if (!uploadState || uploadState.status === 'completed') {
      navigation.navigate('PhotoDetail', { photoId: photo.id });
    }
  };

  const handleCapture = () => {
    navigation.navigate('Camera');
  };

  const handleEndReached = () => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  const getUploadState = (photo: Photo) => {
    return uploads.find((u) => u.photoId === photo.id || u.id === photo.id);
  };

  const getProcessingJob = (photo: Photo) => {
    return processingJobs.find((job) => job.photoId === photo.id);
  };

  const renderItem = ({ item }: { item: Photo }) => (
    <PhotoThumbnail
      photo={item}
      uploadState={getUploadState(item)}
      processingJob={getProcessingJob(item)}
      onPress={handlePhotoPress}
      width={COLUMN_WIDTH}
    />
  );

  const renderEmpty = () => {
    if (isLoading) {
      return (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading photos...</Text>
        </View>
      );
    }
    return <EmptyGallery onStartCapture={handleCapture} />;
  };

  return (
    <SafeAreaView style={styles.container}>
      <FlashList
        data={galleryItems}
        renderItem={renderItem}
        numColumns={2}
        onEndReached={handleEndReached}
        onEndReachedThreshold={0.5}
        onRefresh={refetch}
        ListEmptyComponent={renderEmpty}
        contentContainerStyle={styles.listContent}
      />

      {/* Floating Action Button for Capture */}
      <TouchableOpacity
        style={styles.fab}
        onPress={handleCapture}
        activeOpacity={0.8}>
        <Text style={styles.fabIcon}>+</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  listContent: {
    padding: PADDING,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 64,
  },
  loadingText: {
    color: '#999',
    fontSize: 16,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  fabIcon: {
    color: '#fff',
    fontSize: 32,
    fontWeight: '300',
    lineHeight: 32,
  },
});
