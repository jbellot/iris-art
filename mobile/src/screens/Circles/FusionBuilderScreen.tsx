/**
 * Fusion Builder screen - configure and submit fusion artwork
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  Alert,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { CirclesStackParamList } from '../../navigation/types';
import { fusionService } from '../../services/fusion';
import { BlendMode } from '../../types/fusion';

type Props = {
  navigation: NativeStackNavigationProp<CirclesStackParamList, 'FusionBuilder'>;
  route: RouteProp<CirclesStackParamList, 'FusionBuilder'>;
};

const BLEND_MODES = [
  {
    value: 'poisson' as BlendMode,
    label: 'Seamless Blend',
    description: 'Gradient-based blending for seamless results',
  },
  {
    value: 'alpha' as BlendMode,
    label: 'Simple Blend',
    description: 'Quick blend with transparency overlay',
  },
];

export default function FusionBuilderScreen({ navigation, route }: Props) {
  const { artworkIds, circleId } = route.params;
  const [selectedBlendMode, setSelectedBlendMode] = useState<BlendMode>('poisson');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Validate artwork count
    if (artworkIds.length < 2 || artworkIds.length > 4) {
      Alert.alert(
        'Invalid Selection',
        'Please select 2-4 artworks to create a fusion.',
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    }
  }, [artworkIds]);

  const handleSubmit = async () => {
    if (artworkIds.length < 2 || artworkIds.length > 4) {
      Alert.alert('Invalid Selection', 'Please select 2-4 artworks to create a fusion.');
      return;
    }

    setSubmitting(true);
    try {
      const response = await fusionService.createFusion(
        artworkIds,
        circleId,
        selectedBlendMode
      );

      if (response.status === 'consent_required' && response.pending) {
        // Show consent required dialog
        const pendingConsents = response.pending
          .map((c) => c.owner_name)
          .join(', ');
        Alert.alert(
          'Consent Needed',
          `Consent requests have been sent to: ${pendingConsents}.\n\nYou'll be notified when they approve.`,
          [{ text: 'OK', onPress: () => navigation.navigate('CircleDetail', { circleId }) }]
        );
      } else if (response.fusion_id) {
        // Navigate to result screen
        navigation.navigate('FusionResult', { fusionId: response.fusion_id });
      }
    } catch (error: any) {
      Alert.alert(
        'Fusion Failed',
        error.response?.data?.detail || 'Failed to create fusion. Please try again.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Artwork Preview */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Selected Artworks</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.artworkPreviewContainer}>
            {artworkIds.map((artworkId, index) => (
              <View key={artworkId} style={styles.artworkPreviewItem}>
                <View style={styles.artworkPlaceholder}>
                  <Text style={styles.artworkPlaceholderText}>
                    Artwork {index + 1}
                  </Text>
                </View>
              </View>
            ))}
          </ScrollView>
          <Text style={styles.artworkCount}>
            {artworkIds.length} artwork{artworkIds.length !== 1 ? 's' : ''} selected
          </Text>
        </View>

        {/* Blend Mode Selector */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Blend Mode</Text>
          {BLEND_MODES.map((mode) => (
            <TouchableOpacity
              key={mode.value}
              style={[
                styles.blendModeOption,
                selectedBlendMode === mode.value && styles.blendModeOptionSelected,
              ]}
              onPress={() => setSelectedBlendMode(mode.value)}>
              <View style={styles.blendModeHeader}>
                <Text
                  style={[
                    styles.blendModeLabel,
                    selectedBlendMode === mode.value && styles.blendModeLabelSelected,
                  ]}>
                  {mode.label}
                </Text>
                {selectedBlendMode === mode.value && (
                  <View style={styles.checkmark}>
                    <Text style={styles.checkmarkText}>✓</Text>
                  </View>
                )}
              </View>
              <Text style={styles.blendModeDescription}>{mode.description}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Info Section */}
        <View style={styles.infoSection}>
          <Text style={styles.infoText}>
            Your fusion will combine the selected iris artworks into a single seamless
            image using advanced blending algorithms.
          </Text>
        </View>
      </ScrollView>

      {/* Submit Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
          onPress={handleSubmit}
          disabled={submitting}>
          {submitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.submitButtonText}>Create Fusion</Text>
          )}
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
  scrollContent: {
    paddingBottom: 100,
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 16,
  },
  artworkPreviewContainer: {
    gap: 12,
  },
  artworkPreviewItem: {
    width: 120,
  },
  artworkPlaceholder: {
    width: 120,
    height: 120,
    backgroundColor: '#222',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  artworkPlaceholderText: {
    color: '#666',
    fontSize: 12,
  },
  artworkCount: {
    marginTop: 12,
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  blendModeOption: {
    backgroundColor: '#111',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: '#222',
  },
  blendModeOptionSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#001a33',
  },
  blendModeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  blendModeLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  blendModeLabelSelected: {
    color: '#007AFF',
  },
  blendModeDescription: {
    fontSize: 14,
    color: '#999',
  },
  checkmark: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmarkText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  infoSection: {
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  infoText: {
    fontSize: 14,
    color: '#999',
    lineHeight: 20,
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
    backgroundColor: '#000',
    borderTopWidth: 1,
    borderTopColor: '#222',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#555',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
