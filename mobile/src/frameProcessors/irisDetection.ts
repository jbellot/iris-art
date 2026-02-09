/**
 * Iris detection frame processor plugin
 */
import { VisionCameraProxy, Frame } from 'react-native-vision-camera';

const plugin = VisionCameraProxy.initFrameProcessorPlugin('detectIris', {});

export interface IrisDetectionResult {
  detected: boolean;
  centerX: number;
  centerY: number;
  radius: number;
  distance: number;
}

export function detectIris(frame: Frame): IrisDetectionResult {
  'worklet';
  if (!plugin) {
    return {
      detected: false,
      centerX: 0,
      centerY: 0,
      radius: 0,
      distance: 0,
    };
  }
  return plugin.call(frame) as any as IrisDetectionResult;
}
