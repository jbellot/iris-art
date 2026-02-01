/**
 * Camera screen with Vision Camera, iris guide overlay, and controls
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Modal,
  ScrollView,
  Linking,
  SafeAreaView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useIsFocused } from '@react-navigation/native';
import { MainStackParamList } from '../../navigation/types';
import {
  Camera,
  useCameraDevice,
  PhotoFile,
} from 'react-native-vision-camera';
import Animated, {
  useAnimatedProps,
  useSharedValue,
} from 'react-native-reanimated';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import {
  checkCameraPermission,
  requestCameraPermission,
} from '../../utils/permissions';
import { useCamera } from '../../hooks/useCamera';
import {
  checkBiometricConsent,
  getJurisdictionInfo,
  grantBiometricConsent,
} from '../../services/consent';
import { useUiStore } from '../../store/uiStore';
import ShutterButton from '../../components/Camera/ShutterButton';
import FlashToggle from '../../components/Camera/FlashToggle';
import CameraSwitcher from '../../components/Camera/CameraSwitcher';
import IrisGuideOverlay from '../../components/Camera/IrisGuideOverlay';
import CaptureHint from '../../components/Camera/CaptureHint';

type CameraScreenProps = {
  navigation: NativeStackNavigationProp<MainStackParamList, 'Camera'>;
};

const AnimatedCamera = Animated.createAnimatedComponent(Camera);

export default function CameraScreen({ navigation }: CameraScreenProps) {
  const isFocused = useIsFocused();
  const cameraRef = useRef<Camera>(null);
  const { device, flash, zoom, minZoom, maxZoom, toggleFlash, toggleCamera } =
    useCamera();
  const startZoom = useRef(1);

  // Permission states
  const [cameraPermission, setCameraPermission] = useState<
    'granted' | 'denied' | 'blocked' | 'checking'
  >('checking');

  // Consent states
  const [consentChecked, setConsentChecked] = useState(false);
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [consentText, setConsentText] = useState('');
  const [consentVersion, setConsentVersion] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [consentAgreed, setConsentAgreed] = useState(false);
  const [grantingConsent, setGrantingConsent] = useState(false);

  // UI states
  const [capturing, setCapturing] = useState(false);
  const [showHint, setShowHint] = useState(true);

  const { setBiometricConsentGranted } = useUiStore();

  // Check biometric consent on mount
  useEffect(() => {
    async function checkConsent() {
      const hasConsent = await checkBiometricConsent();
      if (!hasConsent) {
        // Fetch jurisdiction info for consent flow
        const jurisdictionInfo = await getJurisdictionInfo();
        if (jurisdictionInfo) {
          setJurisdiction(jurisdictionInfo.jurisdiction);
          setConsentText(
            jurisdictionInfo.consent_requirements.consent_text
          );
          setConsentVersion(
            jurisdictionInfo.consent_requirements.consent_text_version
          );
          setShowConsentModal(true);
        } else {
          // Failed to fetch jurisdiction, show error
          console.error('Failed to fetch jurisdiction info');
        }
      }
      setConsentChecked(true);
    }

    checkConsent();
  }, []);

  // Check camera permission on mount and when focused
  useEffect(() => {
    async function checkPermission() {
      const status = await checkCameraPermission();
      if (status.granted) {
        setCameraPermission('granted');
      } else if (status.blocked) {
        setCameraPermission('blocked');
      } else {
        setCameraPermission('denied');
      }
    }

    if (isFocused) {
      checkPermission();
    }
  }, [isFocused]);

  const handleRequestPermission = async () => {
    const status = await requestCameraPermission();
    if (status.granted) {
      setCameraPermission('granted');
    } else if (status.blocked) {
      setCameraPermission('blocked');
    } else {
      setCameraPermission('denied');
    }
  };

  const handleOpenSettings = () => {
    Linking.openSettings();
  };

  const handleConsentDecline = () => {
    setShowConsentModal(false);
    navigation.goBack();
  };

  const handleConsentGrant = async () => {
    if (!consentAgreed) {
      return;
    }

    setGrantingConsent(true);
    const success = await grantBiometricConsent(jurisdiction, consentVersion);
    setGrantingConsent(false);

    if (success) {
      await setBiometricConsentGranted(true);
      setShowConsentModal(false);
    } else {
      // Show error - for now, just close modal
      console.error('Failed to grant consent');
    }
  };

  const handleCapture = useCallback(async () => {
    if (!cameraRef.current || !device || capturing) {
      return;
    }

    try {
      setCapturing(true);
      setShowHint(false); // Dismiss hint after first capture

      const photo: PhotoFile = await cameraRef.current.takePhoto({
        flash: flash,
        enableShutterSound: true,
      });

      // Navigate to PhotoReview with photo details
      navigation.navigate('PhotoReview', {
        photoPath: photo.path,
        photoWidth: photo.width,
        photoHeight: photo.height,
      });
    } catch (error) {
      console.error('Failed to capture photo:', error);
    } finally {
      setCapturing(false);
    }
  }, [device, flash, capturing, navigation]);

  // Pinch-to-zoom gesture
  const pinchGesture = Gesture.Pinch()
    .onUpdate((event) => {
      const newZoom = Math.max(
        minZoom,
        Math.min(event.scale * startZoom.current, maxZoom)
      );
      zoom.value = newZoom;
    })
    .onEnd(() => {
      startZoom.current = zoom.value;
    });

  // Animated props for camera zoom
  const animatedProps = useAnimatedProps(
    () => ({
      zoom: zoom.value,
    }),
    [zoom]
  );

  // Show consent modal
  if (!consentChecked || showConsentModal) {
    return (
      <Modal visible={true} animationType="slide">
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Biometric Consent Required</Text>
          </View>

          <ScrollView style={styles.modalContent}>
            <Text style={styles.consentText}>{consentText}</Text>
          </ScrollView>

          <View style={styles.modalFooter}>
            <TouchableOpacity
              style={styles.checkbox}
              onPress={() => setConsentAgreed(!consentAgreed)}>
              <View
                style={[
                  styles.checkboxBox,
                  consentAgreed && styles.checkboxChecked,
                ]}
              >
                {consentAgreed && <Text style={styles.checkmark}>✓</Text>}
              </View>
              <Text style={styles.checkboxLabel}>I agree</Text>
            </TouchableOpacity>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.declineButton}
                onPress={handleConsentDecline}>
                <Text style={styles.declineButtonText}>Decline</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.grantButton,
                  (!consentAgreed || grantingConsent) &&
                    styles.grantButtonDisabled,
                ]}
                onPress={handleConsentGrant}
                disabled={!consentAgreed || grantingConsent}>
                {grantingConsent ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.grantButtonText}>Grant Consent</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </SafeAreaView>
      </Modal>
    );
  }

  // Show permission request screen
  if (cameraPermission === 'denied') {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionTitle}>Camera Access Required</Text>
        <Text style={styles.permissionText}>
          IrisArt needs access to your camera to capture iris photos.
        </Text>
        <TouchableOpacity
          style={styles.permissionButton}
          onPress={handleRequestPermission}>
          <Text style={styles.permissionButtonText}>Grant Permission</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>Back to Gallery</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Show blocked permission screen
  if (cameraPermission === 'blocked') {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionTitle}>Camera Access Blocked</Text>
        <Text style={styles.permissionText}>
          Camera access is blocked in settings. Please enable it to continue.
        </Text>
        <TouchableOpacity
          style={styles.permissionButton}
          onPress={handleOpenSettings}>
          <Text style={styles.permissionButtonText}>Open Settings</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>Back to Gallery</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Show loading while checking permissions or device not ready
  if (cameraPermission === 'checking' || !device) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#fff" />
      </View>
    );
  }

  // Render camera
  return (
    <View style={styles.container}>
      <GestureDetector gesture={pinchGesture}>
        <AnimatedCamera
          ref={cameraRef}
          style={StyleSheet.absoluteFill}
          device={device}
          isActive={isFocused && cameraPermission === 'granted'}
          photo={true}
          photoQualityBalance="quality"
          animatedProps={animatedProps}
        />
      </GestureDetector>

      {/* Iris guide overlay */}
      <IrisGuideOverlay />

      {/* Capture hint */}
      {showHint && <CaptureHint onDismiss={() => setShowHint(false)} />}

      {/* Top controls */}
      <View style={styles.topControls}>
        <TouchableOpacity
          style={styles.closeButton}
          onPress={() => navigation.goBack()}>
          <Text style={styles.closeButtonText}>✕</Text>
        </TouchableOpacity>
        <FlashToggle flash={flash} onToggle={toggleFlash} />
      </View>

      {/* Bottom controls */}
      <View style={styles.bottomControls}>
        <CameraSwitcher onToggle={toggleCamera} />
        <ShutterButton onCapture={handleCapture} disabled={capturing} />
        <View style={styles.placeholder} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
    paddingHorizontal: 32,
  },
  permissionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
    textAlign: 'center',
  },
  permissionText: {
    fontSize: 16,
    color: '#999',
    marginBottom: 32,
    textAlign: 'center',
    lineHeight: 24,
  },
  permissionButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 12,
    marginBottom: 16,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  backButton: {
    paddingHorizontal: 32,
    paddingVertical: 12,
  },
  backButtonText: {
    color: '#999',
    fontSize: 16,
  },
  topControls: {
    position: 'absolute',
    top: 60,
    left: 16,
    right: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  closeButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '300',
  },
  bottomControls: {
    position: 'absolute',
    bottom: 40,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  placeholder: {
    width: 48,
  },
  // Consent modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  modalHeader: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  consentText: {
    fontSize: 14,
    color: '#ccc',
    lineHeight: 22,
  },
  modalFooter: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  checkbox: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  checkboxBox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: '#999',
    borderRadius: 4,
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  checkmark: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#fff',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  declineButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#333',
    marginRight: 12,
    alignItems: 'center',
  },
  declineButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  grantButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  grantButtonDisabled: {
    opacity: 0.5,
  },
  grantButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
