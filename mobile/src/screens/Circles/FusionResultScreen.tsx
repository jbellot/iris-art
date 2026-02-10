/**
 * Fusion Result screen - displays real-time progress and completed fusion result
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  Alert,
  SafeAreaView,
  Share,
  Platform,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { CirclesStackParamList } from '../../navigation/types';
import { useFusion } from '../../hooks/useFusion';
import { saveImageToDevice } from '../../utils/saveToDevice';

type Props = {
  navigation: NativeStackNavigationProp<CirclesStackParamList, 'FusionResult'>;
  route: RouteProp<CirclesStackParamList, 'FusionResult'>;
};

export default function FusionResultScreen({ navigation, route }: Props) {
  const { fusionId } = route.params;
  const { status, progress, currentStep, resultUrl, thumbnailUrl, error, isConnected } =
    useFusion(fusionId);
  const [saving, setSaving] = useState(false);

  const handleSaveToGallery = async () => {
    if (!resultUrl || saving) return;
    setSaving(true);
    try {
      await saveImageToDevice(resultUrl);
    } finally {
      setSaving(false);
    }
  };

  const handleShare = async () => {
    if (!resultUrl) return;

    try {
      await Share.share({
        message: 'Check out my iris fusion artwork!',
        url: Platform.OS === 'ios' ? resultUrl : undefined,
      });
    } catch (error) {
      console.error('Share error:', error);
    }
  };

  const handleBackToCircle = () => {
    // Navigate back to circle detail
    // Note: We need to extract circleId from navigation history or pass it as param
    navigation.popToTop();
  };

  const handleTryAgain = () => {
    // Go back to previous screen (builder)
    navigation.goBack();
  };

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorTitle}>Fusion Failed</Text>
          <Text style={styles.errorMessage}>{error}</Text>
          <TouchableOpacity style={styles.tryAgainButton} onPress={handleTryAgain}>
            <Text style={styles.tryAgainButtonText}>Try Again</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.backButton}
            onPress={handleBackToCircle}>
            <Text style={styles.backButtonText}>Back to Circle</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  if (status === 'pending' || status === 'processing') {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.processingContainer}>
          <View style={styles.progressSection}>
            <Text style={styles.progressTitle}>Creating your fusion...</Text>
            {currentStep && (
              <Text style={styles.currentStep}>{currentStep}</Text>
            )}
            <View style={styles.progressBarContainer}>
              <View
                style={[styles.progressBarFill, { width: `${progress}%` }]}
              />
            </View>
            <Text style={styles.progressText}>{Math.round(progress)}%</Text>
            {!isConnected && (
              <Text style={styles.connectionWarning}>
                Reconnecting...
              </Text>
            )}
          </View>

          {/* Source artworks placeholder */}
          <View style={styles.sourceArtworksSection}>
            <Text style={styles.sourceArtworksTitle}>Source Artworks</Text>
            <View style={styles.sourceArtworksRow}>
              {[1, 2, 3, 4].map((index) => (
                <View key={index} style={styles.sourceArtworkPlaceholder}>
                  <Text style={styles.sourceArtworkPlaceholderText}>
                    {index}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  if (status === 'completed' && resultUrl) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.resultScrollContent}>
          {/* Result Image */}
          <View style={styles.resultImageContainer}>
            <Image
              source={{ uri: resultUrl }}
              style={styles.resultImage}
              resizeMode="contain"
            />
          </View>

          {/* Source artworks */}
          <View style={styles.resultSourceArtworks}>
            <Text style={styles.resultSourceTitle}>Created from:</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.resultSourceRow}>
              {[1, 2, 3, 4].map((index) => (
                <View key={index} style={styles.resultSourceItem}>
                  <View style={styles.resultSourcePlaceholder}>
                    <Text style={styles.resultSourcePlaceholderText}>
                      {index}
                    </Text>
                  </View>
                </View>
              ))}
            </ScrollView>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionsSection}>
            <TouchableOpacity
              style={[styles.actionButton, saving && styles.actionButtonDisabled]}
              onPress={handleSaveToGallery}
              disabled={saving}>
              <Text style={styles.actionButtonText}>
                {saving ? '💾 Saving...' : '💾 Save to Gallery'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.actionButton, styles.actionButtonSecondary]}
              onPress={handleShare}>
              <Text style={styles.actionButtonText}>🔗 Share</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.actionButton, styles.actionButtonOutline]}
              onPress={handleBackToCircle}>
              <Text style={styles.actionButtonOutlineText}>Back to Circle</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading fusion...</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  processingContainer: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  progressSection: {
    alignItems: 'center',
    marginBottom: 60,
  },
  progressTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 16,
  },
  currentStep: {
    fontSize: 16,
    color: '#999',
    marginBottom: 24,
    textAlign: 'center',
  },
  progressBarContainer: {
    width: '100%',
    height: 8,
    backgroundColor: '#222',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 12,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 14,
    color: '#999',
  },
  connectionWarning: {
    marginTop: 12,
    fontSize: 12,
    color: '#ff9500',
  },
  sourceArtworksSection: {
    alignItems: 'center',
  },
  sourceArtworksTitle: {
    fontSize: 14,
    color: '#999',
    marginBottom: 12,
  },
  sourceArtworksRow: {
    flexDirection: 'row',
    gap: 8,
  },
  sourceArtworkPlaceholder: {
    width: 60,
    height: 60,
    backgroundColor: '#222',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sourceArtworkPlaceholderText: {
    color: '#666',
    fontSize: 12,
  },
  resultScrollContent: {
    paddingBottom: 40,
  },
  resultImageContainer: {
    width: '100%',
    aspectRatio: 1,
    backgroundColor: '#111',
  },
  resultImage: {
    width: '100%',
    height: '100%',
  },
  resultSourceArtworks: {
    paddingHorizontal: 16,
    paddingVertical: 24,
  },
  resultSourceTitle: {
    fontSize: 14,
    color: '#999',
    marginBottom: 12,
  },
  resultSourceRow: {
    gap: 8,
  },
  resultSourceItem: {
    width: 80,
  },
  resultSourcePlaceholder: {
    width: 80,
    height: 80,
    backgroundColor: '#222',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  resultSourcePlaceholderText: {
    color: '#666',
    fontSize: 12,
  },
  actionsSection: {
    paddingHorizontal: 16,
    gap: 12,
  },
  actionButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionButtonSecondary: {
    backgroundColor: '#5856D6',
  },
  actionButtonOutline: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#666',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  actionButtonDisabled: {
    opacity: 0.5,
  },
  actionButtonOutlineText: {
    color: '#999',
    fontSize: 16,
    fontWeight: '600',
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
    fontSize: 22,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 12,
  },
  errorMessage: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
    marginBottom: 32,
  },
  tryAgainButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 8,
    marginBottom: 12,
  },
  tryAgainButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  backButton: {
    paddingVertical: 14,
    paddingHorizontal: 32,
  },
  backButtonText: {
    color: '#999',
    fontSize: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#999',
  },
});
