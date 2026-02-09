/**
 * StyleGalleryScreen - browse and select artistic style presets
 */

import React from 'react';
import {StyleSheet, View, Text, Alert, Image} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {useNavigation, useRoute, RouteProp} from '@react-navigation/native';
import {NativeStackNavigationProp} from '@react-navigation/native-stack';
import {StyleGrid} from '../../components/Styles/StyleGrid';
import {useStyleTransfer} from '../../hooks/useStyleTransfer';
import type {MainStackParamList} from '../../navigation/types';
import type {StylePreset} from '../../types/styles';

type StyleGalleryScreenRouteProp = RouteProp<
  MainStackParamList,
  'StyleGallery'
>;
type StyleGalleryScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  'StyleGallery'
>;

export function StyleGalleryScreen() {
  const route = useRoute<StyleGalleryScreenRouteProp>();
  const navigation = useNavigation<StyleGalleryScreenNavigationProp>();

  const {photoId, processingJobId, originalImageUrl} = route.params;

  const {presets, presetsLoading, presetsError} = useStyleTransfer({
    photoId,
    processingJobId,
  });

  const handleStyleSelect = (preset: StylePreset) => {
    navigation.navigate('StylePreview', {
      photoId,
      stylePresetId: preset.id,
      processingJobId,
      originalImageUrl,
    });
  };

  const handlePremiumTap = (preset: StylePreset) => {
    Alert.alert(
      'Premium Style',
      `${preset.displayName} is a premium style. Premium styles will be available in a future update!`,
      [{text: 'OK'}],
    );
  };

  if (presetsError) {
    return (
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>
            Failed to load styles. Please try again.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      {/* Header with source image thumbnail */}
      <View style={styles.header}>
        <Image
          source={{uri: originalImageUrl}}
          style={styles.thumbnail}
          resizeMode="cover"
        />
        <View style={styles.headerTextContainer}>
          <Text style={styles.title}>Choose a Style</Text>
          <Text style={styles.subtitle}>
            Transform your iris into art
          </Text>
        </View>
      </View>

      {/* Style grid */}
      <StyleGrid
        freeStyles={presets?.free || []}
        premiumStyles={presets?.premium || []}
        onSelect={handleStyleSelect}
        onPremiumTap={handlePremiumTap}
        isLoading={presetsLoading}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
    gap: 12,
  },
  thumbnail: {
    width: 64,
    height: 64,
    borderRadius: 12,
    backgroundColor: '#1E1E1E',
  },
  headerTextContainer: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#AAAAAA',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorText: {
    fontSize: 16,
    color: '#FF6B6B',
    textAlign: 'center',
  },
});
