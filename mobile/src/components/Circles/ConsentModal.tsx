/**
 * Modal for approving or denying consent requests
 */
import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import FastImage from '@d11/react-native-fast-image';
import { PendingConsent } from '../../types/consent';
import { decideConsent } from '../../services/artworkConsent';

interface ConsentModalProps {
  visible: boolean;
  pendingConsents: PendingConsent[];
  onClose: () => void;
  onDecisionMade: () => void;
}

const SCREEN_WIDTH = Dimensions.get('window').width;
const PREVIEW_SIZE = SCREEN_WIDTH * 0.6;

export default function ConsentModal({
  visible,
  pendingConsents,
  onClose,
  onDecisionMade,
}: ConsentModalProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentConsent = pendingConsents[currentIndex];

  const handleDecision = async (decision: 'granted' | 'denied') => {
    if (!currentConsent || loading) return;

    setLoading(true);
    setError(null);

    try {
      await decideConsent(currentConsent.id, decision);

      // Move to next consent or close if this was the last one
      if (currentIndex < pendingConsents.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else {
        onDecisionMade();
        onClose();
        setCurrentIndex(0);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to process consent decision');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setCurrentIndex(0);
      setError(null);
      onClose();
    }
  };

  if (!currentConsent) {
    return null;
  }

  const purposeText =
    currentConsent.purpose === 'fusion'
      ? 'wants to use your iris art for fusion'
      : 'wants to use your iris art in a side-by-side composition';

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}>
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Consent Request</Text>
            <Text style={styles.counter}>
              {currentIndex + 1} of {pendingConsents.length}
            </Text>
          </View>

          {/* Content */}
          <ScrollView
            style={styles.content}
            contentContainerStyle={styles.contentContainer}>
            {/* Artwork Preview */}
            <View style={styles.previewContainer}>
              <FastImage
                source={{
                  uri: currentConsent.artwork_preview_url,
                  priority: FastImage.priority.high,
                }}
                style={styles.preview}
                resizeMode={FastImage.resizeMode.cover}
              />
            </View>

            {/* Request Details */}
            <View style={styles.detailsContainer}>
              <Text style={styles.requesterText}>
                {currentConsent.grantee_email}
              </Text>
              <Text style={styles.purposeText}>{purposeText}</Text>
              <Text style={styles.circleText}>
                in circle: {currentConsent.circle_name}
              </Text>
            </View>

            {/* Error Message */}
            {error && (
              <View style={styles.errorContainer}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}
          </ScrollView>

          {/* Action Buttons */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[styles.button, styles.denyButton]}
              onPress={() => handleDecision('denied')}
              disabled={loading}>
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Deny</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.allowButton]}
              onPress={() => handleDecision('granted')}
              disabled={loading}>
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Allow</Text>
              )}
            </TouchableOpacity>
          </View>

          {/* Close Button */}
          <TouchableOpacity
            style={styles.closeButton}
            onPress={handleClose}
            disabled={loading}>
            <Text style={styles.closeText}>Close</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContainer: {
    width: SCREEN_WIDTH * 0.9,
    maxHeight: '80%',
    backgroundColor: '#1c1c1e',
    borderRadius: 12,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#38383a',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  counter: {
    fontSize: 14,
    color: '#8e8e93',
  },
  content: {
    maxHeight: 400,
  },
  contentContainer: {
    padding: 20,
  },
  previewContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  preview: {
    width: PREVIEW_SIZE,
    height: PREVIEW_SIZE,
    borderRadius: 8,
    backgroundColor: '#2c2c2e',
  },
  detailsContainer: {
    alignItems: 'center',
  },
  requesterText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
  },
  purposeText: {
    fontSize: 14,
    color: '#8e8e93',
    textAlign: 'center',
    marginBottom: 4,
  },
  circleText: {
    fontSize: 12,
    color: '#636366',
    textAlign: 'center',
  },
  errorContainer: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#3a0a0a',
    borderRadius: 8,
  },
  errorText: {
    color: '#ff453a',
    fontSize: 14,
    textAlign: 'center',
  },
  buttonContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  button: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  denyButton: {
    backgroundColor: '#ff453a',
  },
  allowButton: {
    backgroundColor: '#30d158',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  closeButton: {
    padding: 16,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#38383a',
  },
  closeText: {
    color: '#0a84ff',
    fontSize: 16,
  },
});
