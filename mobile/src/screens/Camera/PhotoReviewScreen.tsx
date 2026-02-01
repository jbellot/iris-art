/**
 * Photo review screen - displays captured photo with Retake/Accept actions
 */
import React from 'react';
import {
  View,
  Image,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { MainStackParamList } from '../../navigation/types';
import { useUpload } from '../../hooks/useUpload';

type PhotoReviewScreenProps = {
  navigation: NativeStackNavigationProp<MainStackParamList, 'PhotoReview'>;
  route: RouteProp<MainStackParamList, 'PhotoReview'>;
};

export default function PhotoReviewScreen({
  navigation,
  route,
}: PhotoReviewScreenProps) {
  const { photoPath, photoWidth, photoHeight } = route.params;
  const { startUpload } = useUpload();

  const handleRetake = () => {
    // Navigate back to camera
    navigation.goBack();
  };

  const handleAccept = async () => {
    // Start upload in background
    await startUpload(photoPath, photoWidth, photoHeight);

    // Navigate to gallery immediately - upload continues in background
    navigation.navigate('Gallery');
  };

  const photoUri = photoPath.startsWith('file://')
    ? photoPath
    : `file://${photoPath}`;

  return (
    <SafeAreaView style={styles.container}>
      {/* Full-screen photo display */}
      <View style={styles.imageContainer}>
        <Image source={{ uri: photoUri }} style={styles.image} resizeMode="contain" />
      </View>

      {/* Bottom action bar */}
      <View style={styles.bottomBar}>
        <TouchableOpacity style={styles.retakeButton} onPress={handleRetake}>
          <Text style={styles.retakeButtonText}>Retake</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.acceptButton} onPress={handleAccept}>
          <Text style={styles.acceptButtonText}>Accept</Text>
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
  imageContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  bottomBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 24,
    backgroundColor: '#000',
  },
  retakeButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#333',
    marginRight: 12,
    alignItems: 'center',
  },
  retakeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  acceptButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  acceptButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
