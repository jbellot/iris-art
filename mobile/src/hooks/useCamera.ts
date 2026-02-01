/**
 * Camera hook for device selection, flash, and zoom control
 */
import { useState } from 'react';
import { useSharedValue } from 'react-native-reanimated';
import { useCameraDevice } from 'react-native-vision-camera';

export type CameraPosition = 'back' | 'front';
export type FlashMode = 'off' | 'on';

export function useCamera() {
  const [cameraPosition, setCameraPosition] = useState<CameraPosition>('back');
  const [flash, setFlash] = useState<FlashMode>('off');
  const zoom = useSharedValue(1);
  const device = useCameraDevice(cameraPosition);

  const toggleFlash = () => {
    setFlash(f => (f === 'off' ? 'on' : 'off'));
  };

  const toggleCamera = () => {
    setCameraPosition(p => (p === 'back' ? 'front' : 'back'));
  };

  // Min/max zoom from device capabilities
  const minZoom = device?.minZoom ?? 1;
  const maxZoom = Math.min(device?.maxZoom ?? 1, 10); // Cap at 10x for usability

  return {
    device,
    cameraPosition,
    flash,
    zoom,
    minZoom,
    maxZoom,
    toggleFlash,
    toggleCamera,
  };
}
