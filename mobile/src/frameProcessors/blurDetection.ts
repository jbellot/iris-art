/**
 * Blur detection frame processor plugin
 */
import { VisionCameraProxy, Frame } from 'react-native-vision-camera';

const plugin = VisionCameraProxy.initFrameProcessorPlugin('detectBlur', {});

export interface BlurDetectionResult {
  sharpness: number;
  isBlurry: boolean;
}

export function detectBlur(frame: Frame): BlurDetectionResult {
  'worklet';
  if (!plugin) {
    return {
      sharpness: 0,
      isBlurry: true,
    };
  }
  return plugin.call(frame) as any as BlurDetectionResult;
}
