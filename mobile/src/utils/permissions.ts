/**
 * Permission helpers for camera access
 */
import { Platform } from 'react-native';
import {
  check,
  request,
  PERMISSIONS,
  RESULTS,
  Permission,
} from 'react-native-permissions';

export type PermissionStatus = {
  granted: boolean;
  blocked: boolean;
  denied: boolean;
};

const getCameraPermission = (): Permission => {
  return Platform.select({
    ios: PERMISSIONS.IOS.CAMERA,
    android: PERMISSIONS.ANDROID.CAMERA,
  }) as Permission;
};

/**
 * Check camera permission status
 */
export const checkCameraPermission = async (): Promise<PermissionStatus> => {
  const permission = getCameraPermission();
  const result = await check(permission);

  return {
    granted: result === RESULTS.GRANTED,
    blocked: result === RESULTS.BLOCKED,
    denied: result === RESULTS.DENIED,
  };
};

/**
 * Request camera permission
 */
export const requestCameraPermission = async (): Promise<PermissionStatus> => {
  const permission = getCameraPermission();
  const result = await request(permission);

  return {
    granted: result === RESULTS.GRANTED,
    blocked: result === RESULTS.BLOCKED,
    denied: result === RESULTS.DENIED,
  };
};
