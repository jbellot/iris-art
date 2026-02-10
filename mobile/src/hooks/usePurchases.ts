/**
 * Purchase hook for managing RevenueCat purchases
 */
import {useEffect, useState} from 'react';
import Purchases, {
  CustomerInfo,
  PurchasesPackage,
} from 'react-native-purchases';
import {getCustomerInfo, restorePurchases as restorePurchasesService} from '../services/purchases';

interface UsePurchasesReturn {
  customerInfo: CustomerInfo | null;
  isLoading: boolean;
  isPremium: boolean;
  purchasePackage: (pkg: PurchasesPackage) => Promise<boolean>;
  restorePurchases: () => Promise<void>;
  refresh: () => Promise<void>;
}

/**
 * Hook for managing purchases and entitlements
 *
 * Provides:
 * - customerInfo: Current customer info from RevenueCat
 * - isLoading: Loading state
 * - isPremium: Whether user has active premium entitlement
 * - purchasePackage: Function to purchase a package
 * - restorePurchases: Function to restore previous purchases
 * - refresh: Function to refresh customer info
 */
export const usePurchases = (): UsePurchasesReturn => {
  const [customerInfo, setCustomerInfo] = useState<CustomerInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user has premium entitlement
  const isPremium =
    customerInfo?.entitlements?.active?.['pro'] !== undefined || false;

  // Fetch customer info
  const fetchCustomerInfo = async () => {
    try {
      setIsLoading(true);
      const info = await getCustomerInfo();
      setCustomerInfo(info);
    } catch (error) {
      console.error('Error fetching customer info:', error);
      // Set to null on error (degrades gracefully)
      setCustomerInfo(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Set up listener for customer info updates
  useEffect(() => {
    // Initial fetch
    fetchCustomerInfo();

    // Add listener for real-time updates
    let listenerHandle: any;
    try {
      listenerHandle = Purchases.addCustomerInfoUpdateListener(info => {
        setCustomerInfo(info);
      });
    } catch (error) {
      console.error('Error setting up customer info listener:', error);
    }

    // Cleanup
    return () => {
      if (listenerHandle) {
        try {
          listenerHandle.remove();
        } catch (error) {
          console.error('Error removing customer info listener:', error);
        }
      }
    };
  }, []);

  /**
   * Purchase a package
   *
   * @param pkg - Package to purchase
   * @returns true if successful, false if cancelled or failed
   */
  const purchasePackage = async (pkg: PurchasesPackage): Promise<boolean> => {
    try {
      const {customerInfo: updatedInfo} = await Purchases.purchasePackage(pkg);
      setCustomerInfo(updatedInfo);
      return true;
    } catch (error: any) {
      if (error.userCancelled) {
        console.log('User cancelled purchase');
        return false;
      }

      console.error('Error purchasing package:', error);
      throw error;
    }
  };

  /**
   * Restore previous purchases
   */
  const restorePurchases = async (): Promise<void> => {
    try {
      setIsLoading(true);
      const restoredInfo = await restorePurchasesService();
      setCustomerInfo(restoredInfo);
    } catch (error) {
      console.error('Error restoring purchases:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Refresh customer info
   */
  const refresh = async (): Promise<void> => {
    await fetchCustomerInfo();
  };

  return {
    customerInfo,
    isLoading,
    isPremium,
    purchasePackage,
    restorePurchases,
    refresh,
  };
};
