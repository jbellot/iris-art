/**
 * Root navigator with conditional navigation based on app state
 */
import React, { useEffect } from 'react';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuthStore } from '../store/authStore';
import { useUiStore } from '../store/uiStore';

// Onboarding screens
import WelcomeScreen from '../screens/Onboarding/WelcomeScreen';
import PrePermissionScreen from '../screens/Onboarding/PrePermissionScreen';
import BiometricConsentScreen from '../screens/Onboarding/BiometricConsentScreen';

// Auth screens
import LoginScreen from '../screens/Auth/LoginScreen';
import RegisterScreen from '../screens/Auth/RegisterScreen';

// Main app screens
import GalleryScreen from '../screens/Gallery/GalleryScreen';
import CameraScreen from '../screens/Camera/CameraScreen';
import PhotoReviewScreen from '../screens/Camera/PhotoReviewScreen';

import {
  OnboardingStackParamList,
  AuthStackParamList,
  MainStackParamList,
  RootStackParamList,
} from './types';

const RootStack = createNativeStackNavigator<RootStackParamList>();
const OnboardingStack = createNativeStackNavigator<OnboardingStackParamList>();
const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const MainStack = createNativeStackNavigator<MainStackParamList>();

// Onboarding Navigator
function OnboardingNavigator() {
  return (
    <OnboardingStack.Navigator screenOptions={{ headerShown: false }}>
      <OnboardingStack.Screen name="Welcome" component={WelcomeScreen} />
      <OnboardingStack.Screen
        name="PrePermission"
        component={PrePermissionScreen}
      />
      <OnboardingStack.Screen
        name="BiometricConsent"
        component={BiometricConsentScreen}
      />
    </OnboardingStack.Navigator>
  );
}

// Auth Navigator
function AuthNavigator() {
  return (
    <AuthStack.Navigator screenOptions={{ headerShown: false }}>
      <AuthStack.Screen name="Login" component={LoginScreen} />
      <AuthStack.Screen name="Register" component={RegisterScreen} />
    </AuthStack.Navigator>
  );
}

// Main App Navigator
function MainNavigator() {
  return (
    <MainStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: '#000' },
        headerTintColor: '#fff',
      }}>
      <MainStack.Screen
        name="Gallery"
        component={GalleryScreen}
        options={{ title: 'IrisArt' }}
      />
      <MainStack.Screen
        name="Camera"
        component={CameraScreen}
        options={{ headerShown: false }}
      />
      <MainStack.Screen
        name="PhotoReview"
        component={PhotoReviewScreen}
        options={{ headerShown: false }}
      />
    </MainStack.Navigator>
  );
}

// Root Navigator with conditional navigation
export default function RootNavigator() {
  const { isAuthenticated, checkAuth, isLoading: authLoading } = useAuthStore();
  const {
    isFirstLaunch,
    onboardingComplete,
    initializeUiState,
    isLoading: uiLoading,
  } = useUiStore();

  useEffect(() => {
    initializeUiState();
    checkAuth();
  }, []);

  // Show loading screen while initializing
  if (authLoading || uiLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <RootStack.Navigator screenOptions={{ headerShown: false }}>
        {/* Show onboarding if first launch and not completed */}
        {isFirstLaunch && !onboardingComplete ? (
          <RootStack.Screen name="Onboarding" component={OnboardingNavigator} />
        ) : !isAuthenticated ? (
          /* Show auth if not authenticated */
          <RootStack.Screen name="Auth" component={AuthNavigator} />
        ) : (
          /* Show main app if authenticated */
          <RootStack.Screen name="Main" component={MainNavigator} />
        )}
      </RootStack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
});
