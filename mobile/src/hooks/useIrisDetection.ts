/**
 * Hook for iris detection with frame processor integration
 */
import { useCallback, useState, useRef } from 'react';
import { useFrameProcessor } from 'react-native-vision-camera';
import { runOnJS } from 'react-native-reanimated';
import { detectIris, IrisDetectionResult } from '../frameProcessors/irisDetection';
import { detectBlur, BlurDetectionResult } from '../frameProcessors/blurDetection';
import { analyzeLighting, LightingAnalysisResult } from '../frameProcessors/lightingAnalysis';

export interface GuidanceState {
  irisDetected: boolean;
  irisCenter: { x: number; y: number };
  irisRadius: number;
  distance: number;
  focusQuality: number;
  isBlurry: boolean;
  brightness: number;
  lightingStatus: 'too_dark' | 'too_bright' | 'good';
  isReady: boolean;
  readyToCapture: boolean;
}

const DEFAULT_STATE: GuidanceState = {
  irisDetected: false,
  irisCenter: { x: 0.5, y: 0.5 },
  irisRadius: 0,
  distance: 0,
  focusQuality: 0,
  isBlurry: true,
  brightness: 0,
  lightingStatus: 'too_dark',
  isReady: false,
  readyToCapture: false,
};

export function useIrisDetection() {
  const [guidanceState, setGuidanceState] = useState<GuidanceState>(DEFAULT_STATE);
  const frameCountRef = useRef(0);
  const readyTimestampRef = useRef<number | null>(null);

  const updateGuidanceState = useCallback((
    iris: IrisDetectionResult,
    blur: BlurDetectionResult,
    lighting: LightingAnalysisResult
  ) => {
    const isGoodDistance = iris.distance >= 0.3 && iris.distance <= 0.7;
    const isGoodFocus = !blur.isBlurry && blur.sharpness > 150;
    const isGoodLighting = lighting.status === 'good';

    // Check if ready to capture (all conditions met)
    const isReady = iris.detected && isGoodDistance && isGoodFocus && isGoodLighting;

    // Apply 500ms debounce: must stay ready for 500ms
    let readyToCapture = false;
    const now = Date.now();

    if (isReady) {
      if (readyTimestampRef.current === null) {
        readyTimestampRef.current = now;
      } else if (now - readyTimestampRef.current >= 500) {
        readyToCapture = true;
      }
    } else {
      readyTimestampRef.current = null;
    }

    setGuidanceState({
      irisDetected: iris.detected,
      irisCenter: { x: iris.centerX, y: iris.centerY },
      irisRadius: iris.radius,
      distance: iris.distance,
      focusQuality: blur.sharpness,
      isBlurry: blur.isBlurry,
      brightness: lighting.brightness,
      lightingStatus: lighting.status,
      isReady: true, // After first detection completes
      readyToCapture,
    });
  }, []);

  const frameProcessor = useFrameProcessor((frame) => {
    'worklet';

    // Skip frames: process every 3rd frame to stay within 33ms budget
    frameCountRef.current += 1;
    if (frameCountRef.current % 3 !== 0) {
      return;
    }

    try {
      // Run all three detections
      const irisResult = detectIris(frame);
      const blurResult = detectBlur(frame);
      const lightingResult = analyzeLighting(frame);

      // Bridge to JS thread for state update
      runOnJS(updateGuidanceState)(irisResult, blurResult, lightingResult);
    } catch (error) {
      // Silently ignore errors in frame processing
    }
  }, [updateGuidanceState]);

  return {
    guidanceState,
    frameProcessor,
  };
}
