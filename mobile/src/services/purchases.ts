/**
 * RevenueCat purchase service
 */
import {Platform} from 'react-native';
import Purchases, {CustomerInfo, PurchasesOfferings} from 'react-native-purchases';
import apiClient from './api';
import {RateLimitStatus} from '../types/purchases';

// RevenueCat API keys (empty strings for dev mode - SDK will fail gracefully)
const REVENUECAT_PUBLIC_API_KEY_IOS = '';
const REVENUECAT_PUBLIC_API_KEY_ANDROID = '';

/**
 * Initialize RevenueCat SDK
 * Configures SDK with platform-specific API key and logs in user
 *
 * @param userId - User ID to identify in RevenueCat
 */
export const initializePurchases = async (userId: string): Promise<void> => {
  try {
    const apiKey =
      Platform.OS === 'ios'
        ? REVENUECAT_PUBLIC_API_KEY_IOS
        : REVENUECAT_PUBLIC_API_KEY_ANDROID;

    if (!apiKey) {
      console.warn('RevenueCat API key not configured, purchases disabled');
      return;
    }

    // Configure Purchases SDK
    await Purchases.configure({apiKey});

    // Log in user to RevenueCat
    await Purchases.logIn(userId);

    console.log('RevenueCat initialized for user:', userId);
  } catch (error) {
    console.error('Error initializing RevenueCat:', error);
    // Don't throw - degrade gracefully without purchases
  }
};

/**
 * Get available offerings (products available for purchase)
 *
 * @returns PurchasesOfferings or null if not available
 */
export const getOfferings = async (): Promise<PurchasesOfferings | null> => {
  try {
    const offerings = await Purchases.getOfferings();
    return offerings;
  } catch (error) {
    console.error('Error fetching offerings:', error);
    return null;
  }
};

/**
 * Purchase HD export (consumable)
 *
 * @param exportJobId - Export job ID to associate with purchase
 * @returns CustomerInfo if successful, null otherwise
 */
export const purchaseHDExport = async (
  exportJobId: string,
): Promise<CustomerInfo | null> => {
  try {
    const offerings = await getOfferings();
    if (!offerings?.current) {
      console.error('No current offering available');
      return null;
    }

    // Find HD export package
    const hdExportPackage = offerings.current.availablePackages.find(
      pkg => pkg.identifier === 'hd_export',
    );

    if (!hdExportPackage) {
      console.error('HD export package not found');
      return null;
    }

    // Make purchase
    const {customerInfo} = await Purchases.purchasePackage(hdExportPackage);

    // Notify backend of purchase (associate with export job)
    try {
      await apiClient.post('/purchases/hd-export', {
        export_job_id: exportJobId,
      });
    } catch (backendError) {
      console.error('Error notifying backend of purchase:', backendError);
      // Continue even if backend notification fails - webhook will handle it
    }

    return customerInfo;
  } catch (error: any) {
    // Check if user cancelled
    if (error.userCancelled) {
      console.log('User cancelled purchase');
      return null;
    }

    console.error('Error purchasing HD export:', error);
    throw error;
  }
};

/**
 * Purchase premium styles (non-consumable)
 *
 * @returns CustomerInfo if successful, null otherwise
 */
export const purchasePremiumStyles = async (): Promise<CustomerInfo | null> => {
  try {
    const offerings = await getOfferings();
    if (!offerings?.current) {
      console.error('No current offering available');
      return null;
    }

    // Find premium styles package
    const premiumPackage = offerings.current.availablePackages.find(
      pkg => pkg.identifier === 'premium_styles',
    );

    if (!premiumPackage) {
      console.error('Premium styles package not found');
      return null;
    }

    // Make purchase
    const {customerInfo} = await Purchases.purchasePackage(premiumPackage);

    return customerInfo;
  } catch (error: any) {
    // Check if user cancelled
    if (error.userCancelled) {
      console.log('User cancelled purchase');
      return null;
    }

    console.error('Error purchasing premium styles:', error);
    throw error;
  }
};

/**
 * Restore previous purchases
 *
 * @returns CustomerInfo with restored purchases
 */
export const restorePurchases = async (): Promise<CustomerInfo> => {
  const customerInfo = await Purchases.restorePurchases();
  return customerInfo;
};

/**
 * Get current customer info (entitlements, purchases)
 *
 * @returns CustomerInfo or null if not available
 */
export const getCustomerInfo = async (): Promise<CustomerInfo | null> => {
  try {
    const customerInfo = await Purchases.getCustomerInfo();
    return customerInfo;
  } catch (error) {
    console.error('Error fetching customer info:', error);
    return null;
  }
};

/**
 * Get rate limit status from backend
 *
 * @returns RateLimitStatus
 */
export const getRateLimitStatus = async (): Promise<RateLimitStatus> => {
  const response = await apiClient.get<RateLimitStatus>(
    '/purchases/rate-limit-status',
  );
  return response.data;
};
