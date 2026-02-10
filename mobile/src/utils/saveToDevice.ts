import RNFS from 'react-native-fs';
import { CameraRoll } from '@react-native-camera-roll/camera-roll';
import { Platform, Alert } from 'react-native';
import { check, request, PERMISSIONS, RESULTS } from 'react-native-permissions';

const requestPhotoPermission = async (): Promise<boolean> => {
  const permission = Platform.select({
    ios: PERMISSIONS.IOS.PHOTO_LIBRARY_ADD_ONLY,
    android: Number(Platform.Version) >= 33
      ? PERMISSIONS.ANDROID.READ_MEDIA_IMAGES
      : PERMISSIONS.ANDROID.WRITE_EXTERNAL_STORAGE,
  });

  if (!permission) return false;

  const result = await check(permission);
  if (result === RESULTS.GRANTED || result === RESULTS.LIMITED) return true;

  if (result === RESULTS.DENIED) {
    const requestResult = await request(permission);
    return requestResult === RESULTS.GRANTED || requestResult === RESULTS.LIMITED;
  }

  Alert.alert(
    'Permission Required',
    'Please enable photo library access in Settings to save images.',
    [{ text: 'OK' }],
  );
  return false;
};

export const saveImageToDevice = async (imageUrl: string): Promise<boolean> => {
  const hasPermission = await requestPhotoPermission();
  if (!hasPermission) return false;

  const tempPath = `${RNFS.TemporaryDirectoryPath}/iris_${Date.now()}.jpg`;

  try {
    const download = await RNFS.downloadFile({
      fromUrl: imageUrl,
      toFile: tempPath,
    }).promise;

    if (download.statusCode !== 200) {
      throw new Error(`Download failed with status ${download.statusCode}`);
    }

    await CameraRoll.save(`file://${tempPath}`, { type: 'photo' });

    // Clean up temp file
    try {
      await RNFS.unlink(tempPath);
    } catch {
      // Ignore cleanup errors
    }

    Alert.alert('Saved', 'Image saved to your photo library!');
    return true;
  } catch (error) {
    // Clean up on failure too
    try {
      await RNFS.unlink(tempPath);
    } catch {
      // Ignore
    }

    console.error('Failed to save image:', error);
    Alert.alert('Error', 'Failed to save image to device. Please try again.');
    return false;
  }
};
