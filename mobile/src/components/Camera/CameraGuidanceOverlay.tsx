/**
 * Composite camera guidance overlay with all indicators
 */
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { GuidanceState } from '../../hooks/useIrisDetection';
import IrisAlignmentGuide from './IrisAlignmentGuide';
import FocusQualityIndicator from './FocusQualityIndicator';
import LightingIndicator from './LightingIndicator';

interface CameraGuidanceOverlayProps {
  guidanceState: GuidanceState;
}

export default function CameraGuidanceOverlay({
  guidanceState,
}: CameraGuidanceOverlayProps) {
  return (
    <View style={StyleSheet.absoluteFill}>
      <IrisAlignmentGuide
        irisDetected={guidanceState.irisDetected}
        irisCenter={guidanceState.irisCenter}
        irisRadius={guidanceState.irisRadius}
        distance={guidanceState.distance}
        isReady={guidanceState.isReady}
        readyToCapture={guidanceState.readyToCapture}
      />

      <FocusQualityIndicator
        irisDetected={guidanceState.irisDetected}
        focusQuality={guidanceState.focusQuality}
        isBlurry={guidanceState.isBlurry}
        isReady={guidanceState.isReady}
      />

      <LightingIndicator
        irisDetected={guidanceState.irisDetected}
        lightingStatus={guidanceState.lightingStatus}
        isReady={guidanceState.isReady}
      />
    </View>
  );
}
