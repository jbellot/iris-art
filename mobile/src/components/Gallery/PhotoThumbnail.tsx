/**
 * Individual photo thumbnail with FastImage, upload progress overlay, and error state
 */
import React from 'react';
import { TouchableOpacity, StyleSheet, View } from 'react-native';
import FastImage from 'react-native-fast-image';
import { Photo } from '../../types/photo';
import { UploadItem } from '../../hooks/useUpload';
import { ProcessingJobState } from '../../store/processingStore';
import UploadProgressOverlay from './UploadProgressOverlay';
import ProcessingBadge from './ProcessingBadge';

interface PhotoThumbnailProps {
  photo: Photo;
  uploadState?: UploadItem;
  processingJob?: ProcessingJobState;
  onPress: (photo: Photo) => void;
  width: number;
}

export default function PhotoThumbnail({
  photo,
  uploadState,
  processingJob,
  onPress,
  width,
}: PhotoThumbnailProps) {
  // Calculate height from aspect ratio, default to square if no dimensions
  const aspectRatio = photo.width && photo.height ? photo.width / photo.height : 1;
  const height = width / aspectRatio;

  // Determine image URI - prefer thumbnail, fallback to original
  const imageUri = photo.thumbnail_url || photo.original_url;

  const handlePress = () => {
    // If failed upload, trigger retry via onPress with special handling
    // Otherwise, navigate to detail view
    onPress(photo);
  };

  return (
    <TouchableOpacity
      style={[styles.container, { width, height }]}
      onPress={handlePress}
      activeOpacity={0.8}>
      <FastImage
        source={{
          uri: imageUri,
          priority: FastImage.priority.normal,
          cache: FastImage.cacheControl.immutable,
        }}
        style={[styles.image, { width, height }]}
        resizeMode={FastImage.resizeMode.cover}
      />

      {/* Show upload overlay if uploading or failed */}
      {uploadState && uploadState.status !== 'completed' && (
        <UploadProgressOverlay
          progress={uploadState.progress}
          status={uploadState.status}
          error={uploadState.error}
        />
      )}

      {/* Show processing badge if processing */}
      {processingJob && (
        <ProcessingBadge
          status={processingJob.status}
          progress={processingJob.progress}
          step={processingJob.step}
        />
      )}

      {/* Shadow overlay for depth */}
      <View style={styles.shadow} />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 8,
    overflow: 'hidden',
    marginHorizontal: 4,
    marginBottom: 8,
    backgroundColor: '#1a1a1a',
  },
  image: {
    borderRadius: 8,
  },
  shadow: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
});
