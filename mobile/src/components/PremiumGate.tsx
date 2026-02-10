/**
 * Premium gate component - shows locked overlay for premium features
 */
import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ViewStyle,
} from 'react-native';
import {usePurchases} from '../hooks/usePurchases';

interface PremiumGateProps {
  feature: string;
  onUpgrade: () => void;
  children: React.ReactNode;
  style?: ViewStyle;
}

/**
 * PremiumGate component conditionally renders children or locked overlay
 *
 * If user is premium: renders children directly
 * If user is not premium: renders locked overlay with upgrade prompt
 *
 * @param feature - Feature name to display in locked message
 * @param onUpgrade - Callback when user taps upgrade button
 * @param children - Content to show when premium (or behind overlay when not)
 * @param style - Additional container styles
 */
export default function PremiumGate({
  feature,
  onUpgrade,
  children,
  style,
}: PremiumGateProps) {
  const {isPremium, isLoading} = usePurchases();

  // Show children directly if premium
  if (isPremium) {
    return <>{children}</>;
  }

  // Show locked overlay if not premium (after loading)
  return (
    <View style={[styles.container, style]}>
      {/* Render children at reduced opacity behind overlay */}
      <View style={styles.childrenContainer}>{children}</View>

      {/* Locked overlay */}
      {!isLoading && (
        <View style={styles.overlay}>
          <View style={styles.lockCard}>
            <Text style={styles.lockIcon}>🔒</Text>
            <Text style={styles.featureName}>{feature}</Text>
            <Text style={styles.description}>
              Unlock {feature} with Premium
            </Text>
            <TouchableOpacity
              style={styles.upgradeButton}
              onPress={onUpgrade}
              activeOpacity={0.8}>
              <Text style={styles.upgradeButtonText}>See Premium Plans</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
  },
  childrenContainer: {
    opacity: 0.3,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  lockCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    maxWidth: 300,
    borderWidth: 1,
    borderColor: '#333',
  },
  lockIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  featureName: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 8,
    textAlign: 'center',
  },
  description: {
    fontSize: 14,
    color: '#999',
    marginBottom: 24,
    textAlign: 'center',
  },
  upgradeButton: {
    backgroundColor: '#7C3AED',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    minWidth: 200,
  },
  upgradeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    textAlign: 'center',
  },
});
