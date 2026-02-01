/**
 * Auth service - calls Phase 1 backend auth endpoints
 */
import apiClient from './api';
import { storeTokens, clearTokens } from './storage';
import {
  TokenResponse,
  UserRead,
  LoginRequest,
  RegisterRequest,
} from '../types/api';

/**
 * Login with email and password
 */
export const login = async (
  email: string,
  password: string,
): Promise<UserRead> => {
  const payload: LoginRequest = { email, password };
  const response = await apiClient.post<TokenResponse>(
    '/auth/login/json',
    payload,
  );

  const { access_token, refresh_token } = response.data;
  await storeTokens(access_token, refresh_token);

  // Fetch user details
  const user = await getCurrentUser();
  return user;
};

/**
 * Register new user
 */
export const register = async (
  email: string,
  password: string,
): Promise<UserRead> => {
  const payload: RegisterRequest = { email, password };
  const response = await apiClient.post<UserRead>('/auth/register', payload);
  return response.data;
};

/**
 * Logout user
 */
export const logout = async (): Promise<void> => {
  try {
    await apiClient.post('/auth/logout');
  } catch (error) {
    // Ignore errors on logout
    console.warn('Logout error:', error);
  } finally {
    await clearTokens();
  }
};

/**
 * Get current authenticated user
 */
export const getCurrentUser = async (): Promise<UserRead> => {
  const response = await apiClient.get<UserRead>('/users/me');
  return response.data;
};

/**
 * Refresh access token
 * Note: This is typically called automatically by the axios interceptor
 */
export const refreshTokens = async (
  refreshToken: string,
): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  });

  const { access_token, refresh_token: new_refresh_token } = response.data;
  await storeTokens(access_token, new_refresh_token);

  return response.data;
};
