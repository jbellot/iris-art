/**
 * Storage service for secure and non-secure data
 * Uses EncryptedStorage for sensitive data (tokens)
 * Uses AsyncStorage for non-sensitive data (flags, preferences)
 */
import EncryptedStorage from 'react-native-encrypted-storage';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { STORAGE_KEYS } from '../utils/constants';

// Token Storage (Encrypted)
export const storeTokens = async (
  accessToken: string,
  refreshToken: string,
): Promise<void> => {
  await EncryptedStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
  await EncryptedStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
};

export const getAccessToken = async (): Promise<string | null> => {
  return await EncryptedStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
};

export const getRefreshToken = async (): Promise<string | null> => {
  return await EncryptedStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
};

export const clearTokens = async (): Promise<void> => {
  await EncryptedStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  await EncryptedStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
};

// App State Storage (Non-encrypted)
export const setHasLaunched = async (value: boolean): Promise<void> => {
  await AsyncStorage.setItem(STORAGE_KEYS.HAS_LAUNCHED, value.toString());
};

export const getHasLaunched = async (): Promise<boolean> => {
  const value = await AsyncStorage.getItem(STORAGE_KEYS.HAS_LAUNCHED);
  return value === 'true';
};

export const setOnboardingComplete = async (value: boolean): Promise<void> => {
  await AsyncStorage.setItem(
    STORAGE_KEYS.ONBOARDING_COMPLETE,
    value.toString(),
  );
};

export const getOnboardingComplete = async (): Promise<boolean> => {
  const value = await AsyncStorage.getItem(STORAGE_KEYS.ONBOARDING_COMPLETE);
  return value === 'true';
};

export const setBiometricConsentGranted = async (
  value: boolean,
): Promise<void> => {
  await AsyncStorage.setItem(
    STORAGE_KEYS.BIOMETRIC_CONSENT_GRANTED,
    value.toString(),
  );
};

export const getBiometricConsentGranted = async (): Promise<boolean> => {
  const value = await AsyncStorage.getItem(
    STORAGE_KEYS.BIOMETRIC_CONSENT_GRANTED,
  );
  return value === 'true';
};

// User Data Storage (Encrypted)
export const storeUserData = async (userData: string): Promise<void> => {
  await EncryptedStorage.setItem(STORAGE_KEYS.USER_DATA, userData);
};

export const getUserData = async (): Promise<string | null> => {
  return await EncryptedStorage.getItem(STORAGE_KEYS.USER_DATA);
};

export const clearUserData = async (): Promise<void> => {
  await EncryptedStorage.removeItem(STORAGE_KEYS.USER_DATA);
};

// Clear all storage
export const clearAllStorage = async (): Promise<void> => {
  await clearTokens();
  await clearUserData();
  await AsyncStorage.clear();
};
