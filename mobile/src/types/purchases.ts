/**
 * Purchase-related types for RevenueCat integration
 */

import {CustomerInfo} from 'react-native-purchases';

export interface PurchaseProduct {
  id: string;
  identifier: string;
  price: number;
  priceString: string;
  currencyCode: string;
  title: string;
  description: string;
}

export interface CustomerEntitlement {
  identifier: string;
  isActive: boolean;
  expirationDate: string | null;
}

export interface PurchaseState {
  isPremium: boolean;
  isLoading: boolean;
  customerInfo: CustomerInfo | null;
  offerings: any | null;
}

export interface RateLimitStatus {
  current_usage: number;
  limit: number;
  reset_date: string;
  is_premium: boolean;
}
