/**
 * Artwork card with owner badge and selection mode
 */
import React from 'react';
import {
  TouchableOpacity,
  StyleSheet,
  View,
  Text,
  Dimensions,
} from 'react-native';
import FastImage from '@d11/react-native-fast-image';
import { CircleArtwork } from '../../hooks/useCircleGallery';

interface ArtworkCardProps {
  artwork: CircleArtwork;
  isSelected?: boolean;
  onPress?: (artwork: CircleArtwork) => void;
  onLongPress?: (artwork: CircleArtwork) => void;
  showOwner?: boolean;
  width: number;
  isOwnArtwork?: boolean;
}

const CHECK_ICON = '\u2713'; // Checkmark

export default function ArtworkCard({
  artwork,
  isSelected = false,
  onPress,
  onLongPress,
  showOwner = true,
  width,
  isOwnArtwork = false,
}: ArtworkCardProps) {
  // Use square aspect ratio for grid layout
  const height = width;

  const handlePress = () => {
    if (onPress) {
      onPress(artwork);
    }
  };

  const handleLongPress = () => {
    if (onLongPress) {
      onLongPress(artwork);
    }
  };

  return (
    <TouchableOpacity
      style={[
        styles.container,
        { width, height },
        isSelected && styles.selectedBorder,
      ]}
      onPress={handlePress}
      onLongPress={handleLongPress}
      activeOpacity={0.8}>
      <FastImage
        source={{
          uri: artwork.thumbnail_url,
          priority: FastImage.priority.normal,
          cache: FastImage.cacheControl.immutable,
        }}
        style={[styles.image, { width, height }]}
        resizeMode={FastImage.resizeMode.cover}
      />

      {/* Selection checkmark overlay */}
      {isSelected && (
        <View style={styles.selectionOverlay}>
          <View style={styles.checkmarkContainer}>
            <Text style={styles.checkmark}>{CHECK_ICON}</Text>
          </View>
        </View>
      )}

      {/* Owner badge at bottom */}
      {showOwner && (
        <View style={styles.ownerBadge}>
          <Text style={styles.ownerText} numberOfLines={1}>
            {isOwnArtwork
              ? 'Your Art'
              : artwork.owner_name || artwork.owner_email}
          </Text>
        </View>
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
    borderWidth: 2,
    borderColor: 'transparent',
  },
  selectedBorder: {
    borderColor: '#007AFF',
  },
  image: {
    borderRadius: 8,
  },
  selectionOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 122, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmarkContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmark: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  ownerBadge: {
    position: 'absolute',
    bottom: 8,
    left: 8,
    right: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 4,
  },
  ownerText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '500',
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
