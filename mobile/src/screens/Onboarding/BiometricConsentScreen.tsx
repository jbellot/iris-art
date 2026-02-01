/**
 * Biometric consent screen - informational (actual consent on first camera access)
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { OnboardingStackParamList } from '../../navigation/types';
import { useUiStore } from '../../store/uiStore';
import apiClient from '../../services/api';
import { ConsentRequirements } from '../../types/api';

type BiometricConsentScreenProps = {
  navigation: NativeStackNavigationProp<
    OnboardingStackParamList,
    'BiometricConsent'
  >;
};

export default function BiometricConsentScreen({
  navigation,
}: BiometricConsentScreenProps) {
  const { setOnboardingComplete } = useUiStore();
  const [consentInfo, setConsentInfo] = useState<ConsentRequirements | null>(
    null,
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConsentRequirements();
  }, []);

  const fetchConsentRequirements = async () => {
    try {
      // Fetch jurisdiction-specific consent info
      // Note: This endpoint doesn't require auth
      const response = await apiClient.get<ConsentRequirements>(
        '/privacy/jurisdiction',
      );
      setConsentInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch consent requirements:', error);
      // Use generic consent if fetch fails
      setConsentInfo({
        jurisdiction: 'GENERIC',
        requires_explicit_consent: true,
        consent_text:
          'By using IrisArt, you consent to the capture and processing of your iris biometric data for the purpose of creating personalized artwork. Your data will be securely stored and never shared without your permission.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = async () => {
    // Mark onboarding as complete
    await setOnboardingComplete(true);

    // Navigation will automatically switch to Auth stack
    // (actual consent grant happens when user first opens camera after auth)
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}>
        <Text style={styles.title}>Privacy & Consent</Text>

        <View style={styles.jurisdictionBadge}>
          <Text style={styles.jurisdictionText}>
            {consentInfo?.jurisdiction || 'GENERIC'}
          </Text>
        </View>

        <Text style={styles.sectionTitle}>What we collect:</Text>
        <Text style={styles.description}>
          IrisArt captures and processes your iris biometric data to create
          personalized artwork.
        </Text>

        <Text style={styles.sectionTitle}>Your consent:</Text>
        <View style={styles.consentBox}>
          <Text style={styles.consentText}>
            {consentInfo?.consent_text ||
              'By using IrisArt, you consent to biometric data processing.'}
          </Text>
        </View>

        {consentInfo?.data_retention_days && (
          <Text style={styles.additionalInfo}>
            Data retention: {consentInfo.data_retention_days} days
          </Text>
        )}

        {consentInfo?.withdrawal_notice_days && (
          <Text style={styles.additionalInfo}>
            Withdrawal notice: {consentInfo.withdrawal_notice_days} days
          </Text>
        )}

        <Text style={styles.note}>
          You'll be asked to grant explicit consent when you first access the
          camera.
        </Text>

        <TouchableOpacity style={styles.button} onPress={handleContinue}>
          <Text style={styles.buttonText}>I understand, continue</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 24,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  jurisdictionBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#007AFF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginBottom: 24,
  },
  jurisdictionText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginTop: 16,
    marginBottom: 8,
  },
  description: {
    fontSize: 16,
    color: '#999',
    lineHeight: 24,
    marginBottom: 8,
  },
  consentBox: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  consentText: {
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
  },
  additionalInfo: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  note: {
    fontSize: 14,
    color: '#007AFF',
    textAlign: 'center',
    marginVertical: 24,
    fontStyle: 'italic',
  },
  button: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});
