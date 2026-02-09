/**
 * Composition Builder screen - configure and submit side-by-side/grid composition
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { CirclesStackParamList } from '../../navigation/types';
import { fusionService } from '../../services/fusion';
import { LayoutType } from '../../types/fusion';

type Props = {
  navigation: NativeStackNavigationProp<CirclesStackParamList, 'CompositionBuilder'>;
  route: RouteProp<CirclesStackParamList, 'CompositionBuilder'>;
};

interface LayoutOption {
  value: LayoutType;
  label: string;
  description: string;
  icon: string;
  minArtworks: number;
  maxArtworks: number;
}

const LAYOUT_OPTIONS: LayoutOption[] = [
  {
    value: 'horizontal',
    label: 'Side by Side',
    description: 'Horizontal arrangement',
    icon: '[ | ]',
    minArtworks: 2,
    maxArtworks: 4,
  },
  {
    value: 'vertical',
    label: 'Stacked',
    description: 'Vertical arrangement',
    icon: '[―]',
    minArtworks: 2,
    maxArtworks: 4,
  },
  {
    value: 'grid_2x2',
    label: 'Grid',
    description: '2x2 grid layout',
    icon: '[▦]',
    minArtworks: 3,
    maxArtworks: 4,
  },
];

export default function CompositionBuilderScreen({ navigation, route }: Props) {
  const { artworkIds, circleId } = route.params;
  const [selectedLayout, setSelectedLayout] = useState<LayoutType>('horizontal');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Validate artwork count
    if (artworkIds.length < 2 || artworkIds.length > 4) {
      Alert.alert(
        'Invalid Selection',
        'Please select 2-4 artworks to create a composition.',
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    }
  }, [artworkIds]);

  const isLayoutEnabled = (layout: LayoutOption): boolean => {
    return (
      artworkIds.length >= layout.minArtworks &&
      artworkIds.length <= layout.maxArtworks
    );
  };

  const handleSubmit = async () => {
    if (artworkIds.length < 2 || artworkIds.length > 4) {
      Alert.alert('Invalid Selection', 'Please select 2-4 artworks to create a composition.');
      return;
    }

    const layout = LAYOUT_OPTIONS.find((l) => l.value === selectedLayout);
    if (layout && !isLayoutEnabled(layout)) {
      Alert.alert(
        'Invalid Layout',
        `${layout.label} requires ${layout.minArtworks}-${layout.maxArtworks} artworks.`
      );
      return;
    }

    setSubmitting(true);
    try {
      const response = await fusionService.createComposition(
        artworkIds,
        circleId,
        selectedLayout
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
        'Composition Failed',
        error.response?.data?.detail || 'Failed to create composition. Please try again.'
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

        {/* Layout Selector */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Layout</Text>
          {LAYOUT_OPTIONS.map((layout) => {
            const enabled = isLayoutEnabled(layout);
            return (
              <TouchableOpacity
                key={layout.value}
                style={[
                  styles.layoutOption,
                  selectedLayout === layout.value && styles.layoutOptionSelected,
                  !enabled && styles.layoutOptionDisabled,
                ]}
                onPress={() => enabled && setSelectedLayout(layout.value)}
                disabled={!enabled}>
                <View style={styles.layoutHeader}>
                  <View style={styles.layoutHeaderLeft}>
                    <Text style={styles.layoutIcon}>{layout.icon}</Text>
                    <View>
                      <Text
                        style={[
                          styles.layoutLabel,
                          selectedLayout === layout.value && styles.layoutLabelSelected,
                          !enabled && styles.layoutLabelDisabled,
                        ]}>
                        {layout.label}
                      </Text>
                      <Text style={styles.layoutDescription}>
                        {layout.description}
                      </Text>
                    </View>
                  </View>
                  {enabled && selectedLayout === layout.value && (
                    <View style={styles.checkmark}>
                      <Text style={styles.checkmarkText}>✓</Text>
                    </View>
                  )}
                  {!enabled && (
                    <Text style={styles.disabledHint}>
                      {layout.minArtworks}-{layout.maxArtworks} artworks
                    </Text>
                  )}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Info Section */}
        <View style={styles.infoSection}>
          <Text style={styles.infoText}>
            Your composition will arrange the selected iris artworks in your chosen layout.
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
            <Text style={styles.submitButtonText}>Create Composition</Text>
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
  layoutOption: {
    backgroundColor: '#111',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: '#222',
  },
  layoutOptionSelected: {
    borderColor: '#5856D6',
    backgroundColor: '#1a1833',
  },
  layoutOptionDisabled: {
    opacity: 0.5,
  },
  layoutHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  layoutHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  layoutIcon: {
    fontSize: 32,
    color: '#fff',
  },
  layoutLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  layoutLabelSelected: {
    color: '#5856D6',
  },
  layoutLabelDisabled: {
    color: '#666',
  },
  layoutDescription: {
    fontSize: 13,
    color: '#999',
    marginTop: 2,
  },
  checkmark: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#5856D6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmarkText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  disabledHint: {
    fontSize: 12,
    color: '#666',
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
    backgroundColor: '#5856D6',
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
