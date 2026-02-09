/**
 * StyleThumbnail component - displays a single style preset
 */

import React from 'react';
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Dimensions,
} from 'react-native';
import FastImage from 'react-native-fast-image';
import type {StylePreset} from '../../types/styles';

interface StyleThumbnailProps {
  preset: StylePreset;
  onSelect: (preset: StylePreset) => void;
  onPremiumTap?: (preset: StylePreset) => void;
}

const {width} = Dimensions.get('window');
const CARD_SIZE = (width - 48) / 3; // 3 columns with 16px padding

export function StyleThumbnail({
  preset,
  onSelect,
  onPremiumTap,
}: StyleThumbnailProps) {
  const isPremium = preset.tier === 'premium';

  const handlePress = () => {
    if (isPremium && onPremiumTap) {
      onPremiumTap(preset);
    } else if (!isPremium) {
      onSelect(preset);
    }
  };

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={handlePress}
      activeOpacity={0.7}>
      {/* Thumbnail or gradient placeholder */}
      <View style={styles.imageContainer}>
        {preset.thumbnailUrl ? (
          <FastImage
            source={{uri: preset.thumbnailUrl}}
            style={styles.image}
            resizeMode={FastImage.resizeMode.cover}
          />
        ) : (
          <View style={[styles.placeholder, getGradientStyle(preset.category)]} />
        )}

        {/* Premium lock overlay */}
        {isPremium && (
          <View style={styles.lockOverlay}>
            <Text style={styles.lockIcon}>🔒</Text>
          </View>
        )}
      </View>

      {/* Style name */}
      <Text style={styles.name} numberOfLines={1}>
        {preset.displayName}
      </Text>

      {/* Category badge */}
      <View style={styles.badgeContainer}>
        <Text style={styles.badge}>{formatCategory(preset.category)}</Text>
        {isPremium && <Text style={styles.premiumBadge}>Premium</Text>}
      </View>
    </TouchableOpacity>
  );
}

// Helper to format category names
function formatCategory(category: string): string {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Helper to get gradient placeholder colors by category
function getGradientStyle(category: string) {
  const gradients: Record<string, {backgroundColor: string}> = {
    cosmic: {backgroundColor: '#4A148C'},
    watercolor: {backgroundColor: '#0277BD'},
    pop_art: {backgroundColor: '#E91E63'},
    minimalist: {backgroundColor: '#424242'},
    nature: {backgroundColor: '#2E7D32'},
    oil_painting: {backgroundColor: '#5D4037'},
    abstract: {backgroundColor: '#D84315'},
    geometric: {backgroundColor: '#1565C0'},
  };

  return gradients[category] || {backgroundColor: '#616161'};
}

const styles = StyleSheet.create({
  card: {
    width: CARD_SIZE,
    marginBottom: 16,
    borderRadius: 12,
    backgroundColor: '#1E1E1E',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  imageContainer: {
    width: '100%',
    height: CARD_SIZE,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  placeholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  lockOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  lockIcon: {
    fontSize: 32,
  },
  name: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    paddingHorizontal: 8,
    paddingTop: 8,
  },
  badgeContainer: {
    flexDirection: 'row',
    paddingHorizontal: 8,
    paddingBottom: 8,
    paddingTop: 4,
    gap: 4,
  },
  badge: {
    fontSize: 10,
    color: '#AAAAAA',
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  premiumBadge: {
    fontSize: 10,
    color: '#FFD700',
    backgroundColor: '#3A3A00',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontWeight: '600',
  },
});
