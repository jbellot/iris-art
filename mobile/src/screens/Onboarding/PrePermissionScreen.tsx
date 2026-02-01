/**
 * Pre-permission screen - explain camera access before system dialog
 */
import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { OnboardingStackParamList } from '../../navigation/types';
import { requestCameraPermission } from '../../utils/permissions';

type PrePermissionScreenProps = {
  navigation: NativeStackNavigationProp<
    OnboardingStackParamList,
    'PrePermission'
  >;
};

export default function PrePermissionScreen({
  navigation,
}: PrePermissionScreenProps) {
  const handleContinue = async () => {
    // Request permission (user can grant or deny)
    await requestCameraPermission();

    // Continue to biometric consent regardless of result
    // User can grant camera permission later
    navigation.navigate('BiometricConsent');
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.iconContainer}>
          <Text style={styles.icon}>📷</Text>
        </View>

        <Text style={styles.title}>Camera Access</Text>
        <Text style={styles.description}>
          IrisArt needs camera access to capture your iris photos. We'll ask for
          permission next.
        </Text>

        <TouchableOpacity style={styles.button} onPress={handleContinue}>
          <Text style={styles.buttonText}>Continue</Text>
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
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  iconContainer: {
    marginBottom: 32,
  },
  icon: {
    fontSize: 64,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  description: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 48,
  },
  button: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 48,
    paddingVertical: 16,
    borderRadius: 12,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});
