/**
 * Lighting analysis frame processor plugin
 */
import { VisionCameraProxy, Frame } from 'react-native-vision-camera';

const plugin = VisionCameraProxy.initFrameProcessorPlugin('analyzeLighting', {});

export interface LightingAnalysisResult {
  brightness: number;
  status: 'too_dark' | 'too_bright' | 'good';
}

export function analyzeLighting(frame: Frame): LightingAnalysisResult {
  'worklet';
  if (!plugin) {
    return {
      brightness: 0,
      status: 'too_dark',
    };
  }
  return plugin.call(frame) as any as LightingAnalysisResult;
}
