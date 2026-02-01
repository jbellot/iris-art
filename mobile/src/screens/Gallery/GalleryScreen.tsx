/**
 * Gallery screen (placeholder - will be implemented in Plan 03)
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
import { MainStackParamList } from '../../navigation/types';
import { useAuthStore } from '../../store/authStore';

type GalleryScreenProps = {
  navigation: NativeStackNavigationProp<MainStackParamList, 'Gallery'>;
};

export default function GalleryScreen({ navigation }: GalleryScreenProps) {
  const { logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    // Navigation automatically switches to Auth stack
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Gallery</Text>
        <Text style={styles.subtitle}>Your iris photos will appear here</Text>
        <Text style={styles.placeholder}>(Placeholder - Plan 03)</Text>

        <TouchableOpacity
          style={styles.captureButton}
          onPress={() => navigation.navigate('Camera')}>
          <Text style={styles.captureButtonText}>+ Capture</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutButtonText}>Logout</Text>
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
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#999',
    marginBottom: 8,
  },
  placeholder: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
    marginBottom: 48,
  },
  captureButton: {
    backgroundColor: '#007AFF',
    width: 200,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  captureButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  logoutButton: {
    marginTop: 32,
  },
  logoutButtonText: {
    color: '#999',
    fontSize: 16,
  },
});
