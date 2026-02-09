/**
 * HDExportScreen - Export HD version with payment gate
 */

import React, {useEffect, useState} from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Image,
  Share,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {useNavigation, useRoute, RouteProp} from '@react-navigation/native';
import {NativeStackNavigationProp} from '@react-navigation/native-stack';
import {useHDExport} from '../../hooks/useHDExport';
import type {MainStackParamList} from '../../navigation/types';

// Placeholder CameraRoll
const CameraRoll = {
  save: async (uri: string, options?: any) => {
    throw new Error('CameraRoll not yet configured');
  },
};

type HDExportScreenRouteProp = RouteProp<MainStackParamList, 'HDExport'>;
type HDExportScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  'HDExport'
>;

export function HDExportScreen() {
  const route = useRoute<HDExportScreenRouteProp>();
  const navigation = useNavigation<HDExportScreenNavigationProp>();

  const {sourceType, sourceJobId, previewImageUrl} = route.params;

  const {requestExport, activeExport, isExporting} = useHDExport();

  const [exportSubmitted, setExportSubmitted] = useState(false);

  const handleRequestExport = async () => {
    if (exportSubmitted) {
      return;
    }

    try {
      await requestExport(sourceType, sourceJobId);
      setExportSubmitted(true);
    } catch (err) {
      console.error('Failed to request HD export:', err);
      Alert.alert('Error', 'Failed to request HD export. Please try again.');
    }
  };

  const handleDownload = async () => {
    if (!activeExport?.resultUrl) {
      Alert.alert('Not Ready', 'Please wait for export to complete.');
      return;
    }

    try {
      await CameraRoll.save(activeExport.resultUrl, {type: 'photo'});
      Alert.alert('Downloaded', 'HD export saved to your camera roll!');
    } catch (err) {
      console.error('Failed to download image:', err);
      Alert.alert('Error', 'Failed to download image. Please try again.');
    }
  };

  const handleShare = async () => {
    if (!activeExport?.resultUrl) {
      Alert.alert('Not Ready', 'Please wait for export to complete.');
      return;
    }

    try {
      await Share.share({
        url: activeExport.resultUrl,
        message: 'Check out my HD iris art!',
      });
    } catch (err) {
      console.error('Failed to share:', err);
    }
  };

  const handlePaymentGate = () => {
    // Phase 6: Wire to RevenueCat payment flow
    Alert.alert(
      'Coming Soon',
      'Watermark-free HD exports will be available with premium membership.',
    );
  };

  const isComplete = activeExport?.status === 'completed';
  const isFailed = activeExport?.status === 'failed';

  // Format file size
  const formatFileSize = (bytes: number | null): string => {
    if (!bytes) {
      return '';
    }
    const mb = bytes / (1024 * 1024);
    return mb.toFixed(2) + ' MB';
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.content}>
        {/* Preview */}
        <View style={styles.previewSection}>
          <Text style={styles.sectionTitle}>Current Resolution</Text>
          <Image
            source={{uri: previewImageUrl}}
            style={styles.previewImage}
            resizeMode="contain"
          />
          <Text style={styles.resolutionText}>1024×1024</Text>
        </View>

        {/* HD info */}
        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>Export in HD</Text>
          <Text style={styles.infoText}>
            Upscale your art to 2048×2048 HD resolution
          </Text>
        </View>

        {/* Payment gate placeholder */}
        {!exportSubmitted && (
          <View style={styles.paymentSection}>
            <View style={styles.paymentCard}>
              <View style={styles.freeBadge}>
                <Text style={styles.freeBadgeText}>Free Export</Text>
              </View>
              <Text style={styles.paymentNote}>
                Free exports include a watermark
              </Text>
              <TouchableOpacity
                style={styles.exportButton}
                onPress={handleRequestExport}>
                <Text style={styles.exportButtonText}>
                  Export HD (Free with watermark)
                </Text>
              </TouchableOpacity>
            </View>

            <View style={[styles.paymentCard, styles.paymentCardDisabled]}>
              <Text style={styles.paymentPrice}>4.99 EUR</Text>
              <Text style={styles.paymentNote}>
                Watermark-free HD export (Coming soon)
              </Text>
              <TouchableOpacity
                style={[styles.exportButton, styles.exportButtonDisabled]}
                onPress={handlePaymentGate}>
                <Text style={styles.exportButtonTextDisabled}>
                  Export HD without watermark
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Exporting state */}
        {isExporting && activeExport && (
          <View style={styles.exportingSection}>
            <ActivityIndicator size="large" color="#7C3AED" />
            <Text style={styles.progressText}>
              {activeExport.progress}% -{' '}
              {activeExport.currentStep || 'Exporting...'}
            </Text>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  {width: `${activeExport.progress}%`},
                ]}
              />
            </View>
          </View>
        )}

        {/* Complete state */}
        {isComplete && activeExport?.resultUrl && (
          <View style={styles.resultSection}>
            <Image
              source={{uri: activeExport.resultUrl}}
              style={styles.resultImage}
              resizeMode="contain"
            />

            {/* File info */}
            <View style={styles.fileInfo}>
              <Text style={styles.fileInfoText}>
                {activeExport.resultWidth}×{activeExport.resultHeight} •{' '}
                {formatFileSize(activeExport.fileSizeBytes)}
              </Text>
            </View>

            {/* Watermark notice */}
            {!activeExport.isPaid && (
              <View style={styles.watermarkNotice}>
                <Text style={styles.watermarkNoticeText}>
                  ⚠️ This export includes a watermark
                </Text>
              </View>
            )}

            {/* Actions */}
            <View style={styles.actionsRow}>
              <TouchableOpacity
                style={[styles.actionButton, styles.actionButtonPrimary]}
                onPress={handleDownload}>
                <Text
                  style={[
                    styles.actionButtonText,
                    styles.actionButtonTextPrimary,
                  ]}>
                  Download to Device
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.actionsRow}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={handleShare}>
                <Text style={styles.actionButtonText}>Share</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Failed state */}
        {isFailed && activeExport && (
          <View style={styles.errorSection}>
            <Text style={styles.errorText}>
              {activeExport.errorMessage || 'Export failed'}
            </Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={() => {
                setExportSubmitted(false);
                handleRequestExport();
              }}>
              <Text style={styles.retryButtonText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  previewSection: {
    alignItems: 'center',
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 12,
  },
  previewImage: {
    width: 200,
    height: 200,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  resolutionText: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 8,
  },
  infoSection: {
    alignItems: 'center',
    marginBottom: 24,
  },
  infoTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
  },
  paymentSection: {
    gap: 16,
  },
  paymentCard: {
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#fff',
  },
  paymentCardDisabled: {
    opacity: 0.6,
  },
  freeBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: '#10B981',
    marginBottom: 8,
  },
  freeBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  paymentPrice: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 8,
  },
  paymentNote: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 16,
  },
  exportButton: {
    backgroundColor: '#7C3AED',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  exportButtonDisabled: {
    backgroundColor: '#E5E7EB',
  },
  exportButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  exportButtonTextDisabled: {
    color: '#9CA3AF',
  },
  exportingSection: {
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
    height: 300,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    marginBottom: 16,
  },
  fileInfo: {
    marginBottom: 8,
  },
  fileInfoText: {
    fontSize: 14,
    color: '#6B7280',
  },
  watermarkNotice: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#FEF3C7',
    marginBottom: 16,
  },
  watermarkNoticeText: {
    fontSize: 14,
    color: '#92400E',
    textAlign: 'center',
  },
  actionsRow: {
    width: '100%',
    marginBottom: 12,
  },
  actionButton: {
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
