/**
 * AIGenerateScreen - Generate unique AI art from processed iris
 */

import React, {useState} from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
  Image,
  Share,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {useNavigation, useRoute, RouteProp} from '@react-navigation/native';
import {NativeStackNavigationProp} from '@react-navigation/native-stack';
import {ProgressiveImage} from '../../components/Styles/ProgressiveImage';
import {useAIGeneration} from '../../hooks/useAIGeneration';
import type {MainStackParamList} from '../../navigation/types';

// Placeholder CameraRoll
const CameraRoll = {
  save: async (uri: string, options?: any) => {
    throw new Error('CameraRoll not yet configured');
  },
};

type AIGenerateScreenRouteProp = RouteProp<MainStackParamList, 'AIGenerate'>;
type AIGenerateScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  'AIGenerate'
>;

const STYLE_HINTS = [
  {label: 'Cosmic', value: 'cosmic'},
  {label: 'Abstract', value: 'abstract'},
  {label: 'Watercolor', value: 'watercolor'},
  {label: 'Oil Painting', value: 'oil'},
  {label: 'Geometric', value: 'geometric'},
  {label: 'Minimalist', value: 'minimal'},
];

export function AIGenerateScreen() {
  const route = useRoute<AIGenerateScreenRouteProp>();
  const navigation = useNavigation<AIGenerateScreenNavigationProp>();

  const {photoId, processingJobId, originalImageUrl} = route.params;

  const {generate, activeJob, isGenerating} = useAIGeneration({
    photoId,
    processingJobId,
  });

  const [prompt, setPrompt] = useState('');
  const [selectedHint, setSelectedHint] = useState<string | null>(null);

  const handleGenerate = async () => {
    try {
      await generate(prompt || undefined, selectedHint || undefined);
    } catch (err) {
      console.error('Failed to generate AI art:', err);
      Alert.alert('Error', 'Failed to generate AI art. Please try again.');
    }
  };

  const handleGenerateAgain = () => {
    // Reset job state and allow regeneration
    handleGenerate();
  };

  const handleExportHD = () => {
    if (!activeJob?.id || !activeJob.resultUrl) {
      Alert.alert('Not Ready', 'Please wait for generation to complete.');
      return;
    }

    navigation.navigate('HDExport', {
      sourceType: 'ai_generated',
      sourceJobId: activeJob.id,
      previewImageUrl: activeJob.resultUrl,
    });
  };

  const handleSave = async () => {
    if (!activeJob?.resultUrl) {
      Alert.alert('Not Ready', 'Please wait for generation to complete.');
      return;
    }

    try {
      await CameraRoll.save(activeJob.resultUrl, {type: 'photo'});
      Alert.alert('Saved', 'AI art saved to your camera roll!');
    } catch (err) {
      console.error('Failed to save image:', err);
      Alert.alert('Error', 'Failed to save image. Please try again.');
    }
  };

  const handleShare = async () => {
    if (!activeJob?.resultUrl) {
      Alert.alert('Not Ready', 'Please wait for generation to complete.');
      return;
    }

    try {
      await Share.share({
        url: activeJob.resultUrl,
        message: 'Check out my unique AI-generated iris art!',
      });
    } catch (err) {
      console.error('Failed to share:', err);
    }
  };

  const isComplete = activeJob?.status === 'completed';
  const isFailed = activeJob?.status === 'failed';

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled">
        {/* Source iris thumbnail */}
        <View style={styles.sourceSection}>
          <Text style={styles.sectionTitle}>Your Iris</Text>
          <Image
            source={{uri: originalImageUrl}}
            style={styles.sourceThumbnail}
          />
        </View>

        {/* Result or generation UI */}
        {!activeJob || (!isGenerating && !isComplete && !isFailed) ? (
          /* Initial state: prompt and generate */
          <>
            <View style={styles.promptSection}>
              <Text style={styles.sectionTitle}>Describe Your Vision</Text>
              <TextInput
                style={styles.promptInput}
                placeholder="Describe your vision... (optional)"
                placeholderTextColor="#999"
                multiline
                numberOfLines={3}
                value={prompt}
                onChangeText={setPrompt}
              />
            </View>

            <View style={styles.hintsSection}>
              <Text style={styles.sectionTitle}>Style Hint</Text>
              <View style={styles.hintsGrid}>
                {STYLE_HINTS.map(hint => (
                  <TouchableOpacity
                    key={hint.value}
                    style={[
                      styles.hintChip,
                      selectedHint === hint.value && styles.hintChipSelected,
                    ]}
                    onPress={() =>
                      setSelectedHint(
                        selectedHint === hint.value ? null : hint.value,
                      )
                    }>
                    <Text
                      style={[
                        styles.hintText,
                        selectedHint === hint.value && styles.hintTextSelected,
                      ]}>
                      {hint.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <TouchableOpacity
              style={styles.generateButton}
              onPress={handleGenerate}>
              <Text style={styles.generateButtonText}>Generate AI Art</Text>
            </TouchableOpacity>
          </>
        ) : isGenerating ? (
          /* Generating state */
          <View style={styles.generatingSection}>
            <ActivityIndicator size="large" color="#7C3AED" />
            <Text style={styles.progressText}>
              {activeJob.progress}% - {activeJob.currentStep || 'Processing...'}
            </Text>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  {width: `${activeJob.progress}%`},
                ]}
              />
            </View>
          </View>
        ) : isComplete && activeJob.resultUrl ? (
          /* Complete state */
          <View style={styles.resultSection}>
            <Text style={styles.sectionTitle}>Your AI Art</Text>
            <ProgressiveImage
              previewUrl={activeJob.previewUrl || activeJob.resultUrl}
              fullUrl={activeJob.resultUrl}
              style={styles.resultImage}
            />

            {/* Comparison with source */}
            <View style={styles.comparisonRow}>
              <Image
                source={{uri: originalImageUrl}}
                style={styles.comparisonThumbnail}
              />
              <Text style={styles.arrowText}>→</Text>
              <Image
                source={{uri: activeJob.resultUrl}}
                style={styles.comparisonThumbnail}
              />
            </View>

            {/* Actions */}
            <View style={styles.actionsRow}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={handleGenerateAgain}>
                <Text style={styles.actionButtonText}>Generate Again</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.actionButtonPrimary]}
                onPress={handleExportHD}>
                <Text
                  style={[
                    styles.actionButtonText,
                    styles.actionButtonTextPrimary,
                  ]}>
                  Export HD
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.actionsRow}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={handleSave}>
                <Text style={styles.actionButtonText}>Save</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.actionButton}
                onPress={handleShare}>
                <Text style={styles.actionButtonText}>Share</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : isFailed ? (
          /* Failed state */
          <View style={styles.errorSection}>
            <Text style={styles.errorText}>
              {activeJob.errorMessage || 'Generation failed'}
            </Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={handleGenerateAgain}>
              <Text style={styles.retryButtonText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollContent: {
    padding: 16,
  },
  sourceSection: {
    alignItems: 'center',
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 12,
  },
  sourceThumbnail: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#F3F4F6',
  },
  promptSection: {
    marginBottom: 24,
  },
  promptInput: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1F2937',
    minHeight: 80,
    textAlignVertical: 'top',
  },
  hintsSection: {
    marginBottom: 24,
  },
  hintsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  hintChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#fff',
  },
  hintChipSelected: {
    backgroundColor: '#7C3AED',
    borderColor: '#7C3AED',
  },
  hintText: {
    fontSize: 14,
    color: '#6B7280',
  },
  hintTextSelected: {
    color: '#fff',
  },
  generateButton: {
    backgroundColor: '#7C3AED',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  generateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  generatingSection: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  progressText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 16,
    marginBottom: 8,
  },
  progressBar: {
    width: '100%',
    height: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#7C3AED',
  },
  resultSection: {
    alignItems: 'center',
  },
  resultImage: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 8,
    marginBottom: 16,
  },
  comparisonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  comparisonThumbnail: {
    width: 80,
    height: 80,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  arrowText: {
    fontSize: 24,
    color: '#9CA3AF',
    marginHorizontal: 16,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
    marginBottom: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  actionButtonPrimary: {
    backgroundColor: '#7C3AED',
    borderColor: '#7C3AED',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  actionButtonTextPrimary: {
    color: '#fff',
  },
  errorSection: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  errorText: {
    fontSize: 16,
    color: '#EF4444',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#7C3AED',
  },
  retryButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
});
