# Phase 2: Camera Capture and Image Upload - Research

**Researched:** 2026-02-01
**Domain:** React Native mobile app development with camera capture
**Confidence:** HIGH

## Summary

Phase 2 introduces the React Native mobile app for the first time, implementing camera capture for iris photography with full-resolution upload to S3 and a masonry gallery. The backend from Phase 1 (FastAPI, PostgreSQL, S3/MinIO, JWT auth) is ready; this phase focuses entirely on the mobile frontend.

The standard approach for high-quality camera apps in 2026 is **React Native 0.76+ with Vision Camera 4.x**, using React Navigation 7 for routing, React Native Reanimated 3 for smooth animations, and React Native Gesture Handler for pinch-to-zoom. FastImage provides optimized gallery performance, while react-native-permissions handles permission flows. TypeScript is default for new React Native projects, and Jest + Detox form the standard testing stack.

**Primary recommendation:** Build with bare React Native workflow (not Expo Go) using Vision Camera 4.x for advanced camera control, implement pre-permission screens before system dialogs, upload original full-resolution photos immediately on accept (no background queue yet), use FlashList with masonry for gallery performance, and validate on real iOS 12+ and Android 12MP+ devices (not just simulators).

## Standard Stack

The established libraries/tools for React Native camera apps:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **React Native** | 0.76.x | Cross-platform mobile framework | Defaults to TypeScript, mature ecosystem, superior camera library support vs Flutter. Latest stable as of Jan 2026. |
| **react-native-vision-camera** | 4.x | High-performance camera library | Industry standard (350K+ weekly downloads), Frame Processors for real-time guidance (Phase 4), GPU acceleration, 30-240 FPS support. Replacement for deprecated react-native-camera. |
| **@react-navigation/native** | 7.x | Navigation framework | Official React Native recommendation, native stack navigator uses UINavigationController/Fragment for native performance. Version 7.1.28 (Jan 2026). |
| **@react-navigation/native-stack** | 6.x | Native stack navigator | Uses native APIs (no JS bridge), optimal performance for screen transitions. |
| **React Native Reanimated** | 3.x | UI thread animations | Required for smooth zoom, camera overlays, 60+ FPS gestures. Runs animations on UI thread, not JS thread. |
| **React Native Gesture Handler** | 2.x | Touch gesture system | Handles pinch-to-zoom, pan gestures for camera controls. Native gesture recognition. |
| **react-native-permissions** | 4.x | Unified permission API | Cross-platform permission handling (iOS, Android, Windows). Status: GRANTED, DENIED, BLOCKED, UNAVAILABLE. |
| **@shopify/flash-list** | 1.x | High-performance lists | Masonry layout support built-in, ~50MB memory for 1000+ items vs FlatList's ~500MB+. Shopify-maintained. |
| **react-native-fast-image** | 8.x | Optimized image loading | Wrapper around SDWebImage (iOS) and Glide (Android). Built-in caching, progressive loading, memory management. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **react-native-encrypted-storage** | 4.x | Secure token storage | Store JWT tokens securely. Wraps iOS Keychain and Android EncryptedSharedPreferences. |
| **@react-native-async-storage/async-storage** | 1.x | Non-sensitive persistence | Onboarding flags, UI preferences, non-sensitive app state. NOT for tokens. |
| **react-native-image-resizer** | 3.x | Image compression | If Phase 2 adds compression (CONTEXT says no compression). EXIF preservation for JPEG. |
| **react-native-compressor** | 1.x | WhatsApp-style compression | Alternative to image-resizer, returns EXIF metadata. |
| **react-native-screens** | 3.x | Native screen optimization | Required by React Navigation, uses native container views. |
| **react-native-safe-area-context** | 4.x | Safe area insets | Required by React Navigation, handles notches, status bars, home indicators. |
| **axios** | 1.x | HTTP client | API calls to FastAPI backend, upload progress tracking, interceptors for JWT refresh. |
| **@tanstack/react-query** | 5.x | Server state management | API caching, optimistic updates, background refetch for gallery sync. |
| **zustand** | 4.x | Client state management | Lightweight, camera settings, capture flow, local UI state. Alternative to Redux. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vision Camera 4 | Expo Camera | Expo Camera lacks Frame Processors and advanced controls needed for Phase 4 AI guidance. Vision Camera is more powerful. |
| FlashList | FlatList with masonry lib | FlatList uses 10x more memory for large lists. FlashList has built-in masonry. |
| react-native-permissions | Platform.select with native APIs | Manual permission handling is error-prone. react-native-permissions unifies cross-platform. |
| FastImage | Built-in Image | Native Image component has poor caching, memory leaks on large galleries. FastImage is production-proven. |
| React Navigation | react-native-navigation (Wix) | Wix library is fully native but more complex setup. React Navigation is community standard. |
| axios | fetch | fetch lacks interceptors, progress callbacks. axios is simpler for JWT refresh and upload progress. |

**Installation:**

```bash
# Initialize React Native project (TypeScript by default)
npx @react-native-community/cli@latest init IrisArt --version 0.76.x

# Core navigation
npm install @react-navigation/native @react-navigation/native-stack
npm install react-native-screens react-native-safe-area-context

# Camera and gestures
npm install react-native-vision-camera
npm install react-native-reanimated react-native-gesture-handler

# Permissions and storage
npm install react-native-permissions
npm install react-native-encrypted-storage @react-native-async-storage/async-storage

# Gallery and image loading
npm install @shopify/flash-list react-native-fast-image

# HTTP and state
npm install axios @tanstack/react-query zustand

# iOS pod install
cd ios && pod install && cd ..

# Android permissions (add to AndroidManifest.xml)
# Camera, storage permissions - see official docs
```

## Architecture Patterns

### Recommended Project Structure

```
mobile/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Camera/        # Camera controls, zoom, flash
│   │   ├── Gallery/       # Masonry grid, image items
│   │   └── Common/        # Buttons, loaders, overlays
│   ├── screens/           # Full-screen views
│   │   ├── Onboarding/    # Welcome, pre-permission, consent
│   │   ├── Camera/        # Camera viewfinder
│   │   ├── PhotoReview/   # Retake/accept after capture
│   │   ├── Gallery/       # Photo list screen
│   │   └── PhotoDetail/   # Full-screen photo view
│   ├── navigation/        # React Navigation setup
│   │   ├── RootNavigator.tsx
│   │   └── types.ts       # TypeScript navigation types
│   ├── services/          # API clients, storage
│   │   ├── api.ts         # axios instance, interceptors
│   │   ├── auth.ts        # Token refresh, JWT handling
│   │   ├── upload.ts      # S3 upload with progress
│   │   └── storage.ts     # Secure storage wrappers
│   ├── hooks/             # Custom React hooks
│   │   ├── useCamera.ts   # Camera device, permissions
│   │   ├── useUpload.ts   # Upload queue, retry logic
│   │   └── useGallery.ts  # React Query for gallery
│   ├── store/             # Zustand stores
│   │   ├── cameraStore.ts # Camera settings, flash, zoom
│   │   └── uiStore.ts     # Loading states, modals
│   ├── types/             # TypeScript definitions
│   │   ├── api.ts         # API request/response types
│   │   └── photo.ts       # Photo models
│   ├── utils/             # Helpers
│   │   ├── permissions.ts # Permission flow helpers
│   │   └── constants.ts   # App-wide constants
│   └── App.tsx            # Root component
├── android/               # Android native code
├── ios/                   # iOS native code
├── __tests__/             # Jest unit tests
├── e2e/                   # Detox E2E tests
├── tsconfig.json          # TypeScript config
├── jest.config.js         # Jest config
└── package.json
```

### Pattern 1: Pre-Permission Screen Flow

**What:** Show custom explanation screen BEFORE system permission dialog

**When to use:** For camera, photo library, and biometric consent (required by CONTEXT)

**Example:**

```typescript
// Source: https://blog.logrocket.com/react-native-permissions/
import { check, request, PERMISSIONS, RESULTS } from 'react-native-permissions';

async function requestCameraPermission() {
  const permission = Platform.select({
    ios: PERMISSIONS.IOS.CAMERA,
    android: PERMISSIONS.ANDROID.CAMERA,
  });

  const result = await check(permission);

  if (result === RESULTS.BLOCKED) {
    // Show "Permission denied" screen with settings link
    return { granted: false, blocked: true };
  }

  if (result === RESULTS.DENIED) {
    // Show pre-permission screen with explanation
    // User taps "Continue" -> trigger system dialog
    const requestResult = await request(permission);
    return { granted: requestResult === RESULTS.GRANTED, blocked: false };
  }

  return { granted: result === RESULTS.GRANTED, blocked: false };
}
```

### Pattern 2: Photo Capture with Review Screen

**What:** Capture → Review → Retake or Accept flow (like iPhone camera)

**When to use:** User captures iris photo (CONTEXT decision)

**Example:**

```typescript
// Source: https://react-native-vision-camera.com/docs/guides/taking-photos
import { Camera, useCameraDevice } from 'react-native-vision-camera';

function CameraScreen({ navigation }) {
  const camera = useRef<Camera>(null);
  const device = useCameraDevice('back');

  const takePhoto = async () => {
    if (!camera.current) return;

    const photo = await camera.current.takePhoto({
      flash: flashMode, // 'on' | 'off' | 'auto'
      enableShutterSound: true,
    });

    // Navigate to review screen with photo
    navigation.navigate('PhotoReview', { photoPath: photo.path });
  };

  return (
    <Camera
      ref={camera}
      device={device}
      isActive={true}
      photo={true}
      photoQualityBalance="quality" // prioritize quality over speed
      style={StyleSheet.absoluteFill}
    />
  );
}
```

### Pattern 3: Upload with Progress and Retry

**What:** Upload full-resolution photo to S3 with exponential backoff retry

**When to use:** After user accepts photo in review screen (CONTEXT decision)

**Example:**

```typescript
// Source: https://medium.com/@istvanistvan/react-native-custom-image-picker-with-upload-progress-5444e955455c
import axios from 'axios';

async function uploadPhotoWithRetry(
  photoUri: string,
  onProgress: (percent: number) => void,
  maxRetries = 3
) {
  let attempt = 0;

  while (attempt < maxRetries) {
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: photoUri,
        type: 'image/jpeg',
        name: 'iris-photo.jpg',
      });

      const response = await axios.post('/api/photos/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round(
            (progressEvent.loaded / progressEvent.total) * 100
          );
          onProgress(percent);
        },
      });

      return response.data; // Success

    } catch (error) {
      attempt++;
      if (attempt >= maxRetries) {
        throw new Error('Upload failed after retries');
      }

      // Exponential backoff: 1s, 2s, 4s
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)));
    }
  }
}
```

### Pattern 4: Masonry Gallery with FlashList

**What:** Pinterest-style variable-height photo grid

**When to use:** Gallery screen displaying all user photos (CONTEXT decision)

**Example:**

```typescript
// Source: https://shopify.github.io/flash-list/docs/usage
import { FlashList } from '@shopify/flash-list';
import FastImage from 'react-native-fast-image';

function GalleryScreen() {
  const { data: photos } = useQuery({
    queryKey: ['photos'],
    queryFn: fetchPhotos,
  });

  const renderItem = ({ item }) => (
    <FastImage
      source={{ uri: item.thumbnailUrl, priority: FastImage.priority.normal }}
      style={{ width: item.width, height: item.height }}
      resizeMode={FastImage.resizeMode.cover}
    />
  );

  return (
    <FlashList
      data={photos}
      renderItem={renderItem}
      estimatedItemSize={200}
      numColumns={2}
      // Masonry layout: set masonry={true} for variable heights
      // Note: As of Jan 2026, FlashList masonry is in beta
    />
  );
}
```

### Pattern 5: Pinch-to-Zoom Camera Control

**What:** Smooth pinch gesture for camera zoom

**When to use:** Camera viewfinder screen (CONTEXT decision: zoom control required)

**Example:**

```typescript
// Source: https://react-native-vision-camera.com/docs/guides/zooming
import Animated, { useSharedValue, useAnimatedProps } from 'react-native-reanimated';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';

const ReanimatedCamera = Animated.createAnimatedComponent(Camera);
Animated.addWhitelistedNativeProps({ zoom: true });

function CameraWithZoom() {
  const zoom = useSharedValue(1);
  const device = useCameraDevice('back');

  const pinchGesture = Gesture.Pinch()
    .onUpdate((e) => {
      zoom.value = Math.max(device.minZoom, Math.min(e.scale, device.maxZoom));
    });

  const animatedProps = useAnimatedProps(() => ({
    zoom: zoom.value,
  }));

  return (
    <GestureDetector gesture={pinchGesture}>
      <ReanimatedCamera
        device={device}
        isActive={true}
        photo={true}
        animatedProps={animatedProps}
      />
    </GestureDetector>
  );
}
```

### Anti-Patterns to Avoid

- **Using Expo Go workflow:** Cannot use Vision Camera native modules. Use bare React Native with selective Expo modules.
- **Storing JWT in AsyncStorage:** Use react-native-encrypted-storage (Keychain/Keystore) for tokens.
- **Compressing photos before upload:** CONTEXT explicitly says "no compression" for AI pipeline quality.
- **Background upload on capture:** CONTEXT says "immediate upload" after accept. Background queue is future optimization.
- **FlatList for large galleries:** Use FlashList for 10x better memory performance on 100+ photos.
- **Hardcoding API keys:** Never embed secrets. Use environment variables with react-native-config.
- **Testing only on simulators:** Real devices catch camera hardware, sensor, and performance issues.
- **Skipping pre-permission screens:** iOS/Android restrict re-asking permissions. Explain first.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Permission management | Platform.select with PermissionsAndroid/iOS APIs | react-native-permissions | Unified API, handles BLOCKED state, Windows support. 150+ platforms/permissions. |
| Secure token storage | AsyncStorage + encryption lib | react-native-encrypted-storage | Native Keychain/Keystore, FIPS-compliant, handles keychain migration. |
| Image caching | fetch + custom cache logic | react-native-fast-image | Native SDWebImage/Glide, memory management, disk/memory cache, progressive loading. |
| Upload retry logic | Manual setTimeout + counter | axios with axios-retry or custom backoff | Exponential backoff, jitter, conditional retry (5xx only), tested in production. |
| Camera zoom gestures | Custom PanResponder zoom | Vision Camera enableZoomGesture or Reanimated | Native gesture handling, smooth UI thread animation, logarithmic scale handling. |
| Gallery infinite scroll | FlatList + onEndReached | FlashList with React Query | 10x memory efficiency, automatic prefetching, background refetch. |
| Deep linking | Manual URL parsing | React Navigation Linking config | Type-safe routes, nested navigation, prefixes, query params. |
| Form validation | Custom validators | React Hook Form + Zod | Schema validation, TypeScript types, async validation, error messages. |

**Key insight:** React Native's ecosystem has mature solutions for camera, permissions, and media upload. Custom implementations miss edge cases (permission BLOCKED, iOS/Android differences, memory leaks, gesture conflicts). Use battle-tested libraries.

## Common Pitfalls

### Pitfall 1: Permission Denied After First Rejection

**What goes wrong:** User denies camera permission once, app repeatedly shows broken camera screen with no way forward.

**Why it happens:** iOS/Android prevent re-prompting for same permission. Status becomes `BLOCKED` after user denies. App doesn't handle BLOCKED state.

**How to avoid:**
- Check permission status before rendering camera
- Show different UI for DENIED (can request) vs BLOCKED (must go to settings)
- Provide "Open Settings" button with Linking API for BLOCKED
- Show fallback mode (e.g., gallery-only) if permission never granted

**Warning signs:**
- User taps "Don't Allow" and sees blank screen forever
- No "Open Settings" button when permission is blocked
- App crashes trying to use camera without permission

### Pitfall 2: Memory Leaks from Large Gallery Images

**What goes wrong:** App loads 100+ full-resolution photos into gallery, uses 500MB+ memory, crashes on older devices.

**Why it happens:**
- Using built-in `<Image>` without caching or resizing
- Loading full 12MP photos as thumbnails
- Not clearing memory cache when gallery unmounts
- FlatList loads all images upfront

**How to avoid:**
- Use FastImage for automatic caching and memory management
- Load thumbnails in gallery (backend generates on upload)
- Use FlashList with `estimatedItemSize` for recycling
- Clear FastImage memory cache on unmount: `FastImage.clearMemoryCache()`
- Test on iPhone 12 and Android devices with 4GB RAM

**Warning signs:**
- App slows down after scrolling gallery
- "Memory warning" in Xcode console
- Android kills app in background after visiting gallery

### Pitfall 3: Upload Fails on Poor Network, No Retry

**What goes wrong:** User captures photo on spotty WiFi, upload fails silently or shows permanent error with no retry option.

**Why it happens:**
- No retry logic on network failure
- No exponential backoff (immediate retry overwhelms server)
- Not distinguishing temporary (network) vs permanent (auth) errors
- Upload progress lost, user must recapture

**How to avoid:**
- Implement exponential backoff: 1s, 2s, 4s delays
- Retry only on network errors and 5xx server errors (not 4xx)
- Show manual retry button after auto-retry exhausted
- Consider upload queue for Phase 2.5 if many failures

**Warning signs:**
- Upload fails immediately on slow network
- No "Retry" button, user must recapture photo
- Server logs show hundreds of retries in 1 second

### Pitfall 4: Vision Camera Not Initialized Before takePhoto

**What goes wrong:** App calls `camera.current.takePhoto()` immediately on mount, crashes with "camera is null" or "camera not ready."

**Why it happens:**
- Camera device initialization is asynchronous
- `useCameraDevice('back')` may return null initially
- Camera component needs time to mount and connect to hardware
- No check for `camera.current` or device availability

**How to avoid:**
- Check `if (!device) return <Loading />` before rendering Camera
- Disable shutter button until camera initialized
- Use `onInitialized` callback from Camera component
- Check `camera.current !== null` before calling methods

**Warning signs:**
- Crashes on first photo capture
- "TypeError: Cannot read property 'takePhoto' of null"
- Camera works on second app launch but not first

### Pitfall 5: iOS/Android Platform Differences Not Tested

**What goes wrong:** App works perfectly on iOS simulator, crashes or behaves differently on Android device (or vice versa).

**Why it happens:**
- Simulator doesn't replicate real hardware (camera, sensors)
- iOS and Android have different permission flows
- File paths differ (iOS: file://, Android: content://)
- Android requires additional manifest permissions and MainActivity changes
- Vision Camera behavior differs (e.g., takeSnapshot requires video on iOS)

**How to avoid:**
- Test on real iOS AND Android devices from day 1
- Use Platform.select sparingly, only when necessary
- Check Vision Camera docs for platform-specific notes
- Test permission flows on both platforms (Android asks at runtime)
- Run on device matrix: iPhone 12+, Samsung Galaxy S21+, Pixel 6+

**Warning signs:**
- Works on iOS simulator, crashes on Android emulator
- Camera permission works on Android, broken on iOS
- Photos save on iOS, fail on Android with file URI error

### Pitfall 6: JWT Token Expiry During Long Session

**What goes wrong:** User captures 10 photos over 30 minutes, upload #10 fails with 401 Unauthorized because JWT expired.

**Why it happens:**
- JWT tokens expire (Phase 1: likely 15-60min expiry)
- axios doesn't automatically refresh tokens
- Upload continues with expired token
- No interceptor to refresh token before retry

**How to avoid:**
- Implement axios interceptor for 401 responses
- Refresh JWT using refresh token before retry
- Store refresh token in encrypted storage (Phase 1 backend provides this)
- React Query can auto-retry with fresh token

**Warning signs:**
- Uploads work initially, fail after app open 20+ minutes
- 401 errors in backend logs after JWT expiry time
- User must log out and log back in to upload again

## Code Examples

Verified patterns from official sources:

### Camera Initialization with Permission Check

```typescript
// Source: https://react-native-vision-camera.com/docs/guides
import { Camera, useCameraDevice, useCameraPermission } from 'react-native-vision-camera';

function CameraScreen() {
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice('back');

  if (!hasPermission) {
    return (
      <View>
        <Text>Camera access is required for iris capture</Text>
        <Button title="Grant Permission" onPress={requestPermission} />
      </View>
    );
  }

  if (!device) {
    return <ActivityIndicator />;
  }

  return (
    <Camera
      device={device}
      isActive={true}
      photo={true}
      style={StyleSheet.absoluteFill}
    />
  );
}
```

### S3 Upload with Progress Indicator

```typescript
// Source: https://instamobile.io/react-native-tutorials/react-native-aws-s3/
import axios from 'axios';

async function uploadToS3(photoUri: string, presignedUrl: string) {
  const [uploadProgress, setUploadProgress] = useState(0);

  // Get presigned URL from backend
  const { data: { uploadUrl } } = await axios.post('/api/photos/presign', {
    filename: 'iris-photo.jpg',
    contentType: 'image/jpeg',
  });

  // Upload directly to S3
  const response = await fetch(photoUri);
  const blob = await response.blob();

  await axios.put(uploadUrl, blob, {
    headers: { 'Content-Type': 'image/jpeg' },
    onUploadProgress: (progressEvent) => {
      const percent = Math.round(
        (progressEvent.loaded / progressEvent.total) * 100
      );
      setUploadProgress(percent);
    },
  });
}
```

### Secure Token Storage

```typescript
// Source: https://medium.com/@shahidrogers/react-native-basics-mastering-secure-storage-solutions-071a0fc75201
import EncryptedStorage from 'react-native-encrypted-storage';

async function storeTokens(accessToken: string, refreshToken: string) {
  try {
    await EncryptedStorage.setItem('access_token', accessToken);
    await EncryptedStorage.setItem('refresh_token', refreshToken);
  } catch (error) {
    console.error('Failed to store tokens', error);
  }
}

async function getAccessToken(): Promise<string | null> {
  try {
    return await EncryptedStorage.getItem('access_token');
  } catch (error) {
    console.error('Failed to retrieve token', error);
    return null;
  }
}
```

### React Query for Gallery Data

```typescript
// Source: https://tanstack.com/query/latest/docs/framework/react/overview
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function useGallery() {
  const queryClient = useQueryClient();

  const { data: photos, isLoading } = useQuery({
    queryKey: ['photos'],
    queryFn: async () => {
      const response = await axios.get('/api/photos');
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });

  const uploadMutation = useMutation({
    mutationFn: (photoUri: string) => uploadPhotoWithRetry(photoUri),
    onSuccess: () => {
      // Invalidate and refetch gallery
      queryClient.invalidateQueries({ queryKey: ['photos'] });
    },
  });

  return { photos, isLoading, uploadPhoto: uploadMutation.mutate };
}
```

### First-Launch Detection with AsyncStorage

```typescript
// Source: https://medium.com/@rafiulansari/building-a-react-native-app-part-iv-onboarding-screens-6ef48caefd6c
import AsyncStorage from '@react-native-async-storage/async-storage';

async function checkFirstLaunch(): Promise<boolean> {
  try {
    const hasLaunched = await AsyncStorage.getItem('has_launched');
    if (hasLaunched === null) {
      // First launch
      await AsyncStorage.setItem('has_launched', 'true');
      return true;
    }
    return false;
  } catch (error) {
    console.error('Failed to check first launch', error);
    return false;
  }
}

// Usage in App.tsx
function App() {
  const [isFirstLaunch, setIsFirstLaunch] = useState<boolean | null>(null);

  useEffect(() => {
    checkFirstLaunch().then(setIsFirstLaunch);
  }, []);

  if (isFirstLaunch === null) return <SplashScreen />;
  if (isFirstLaunch) return <OnboardingFlow />;
  return <MainApp />;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| react-native-camera | react-native-vision-camera | 2020 (deprecated) | Vision Camera is 3-5x faster, Frame Processors enable real-time AI (Phase 4) |
| Expo Go for camera apps | Bare React Native + selective Expo modules | 2024+ | Expo Go can't use Vision Camera. Bare workflow required for advanced camera. |
| FlatList for galleries | FlashList | 2022 (Shopify) | 10x memory efficiency, built-in masonry, better performance for 100+ photos |
| Manual permission handling | react-native-permissions | 2018+ (standard) | Unified API, handles BLOCKED state, 150+ permissions across platforms |
| AsyncStorage for tokens | react-native-encrypted-storage | 2020+ (security) | Keychain/Keystore encryption, FIPS-compliant, prevents token theft |
| Redux for server state | React Query (TanStack Query) | 2020+ | Automatic caching, background refetch, optimistic updates, less boilerplate |
| JavaScript | TypeScript (default) | 2023+ (RN 0.71+) | Type safety, better IDE support, catch errors at compile-time. Default since RN 0.71. |
| Image component | FastImage | 2017+ (production standard) | Native caching (SDWebImage/Glide), memory management, progressive loading |

**Deprecated/outdated:**
- **react-native-camera**: Unmaintained since 2020, replaced by Vision Camera 4
- **Expo Go for Vision Camera**: Cannot use native modules, use bare workflow instead
- **FlatList for large media galleries**: Use FlashList for 10x memory improvement
- **AsyncStorage for JWT tokens**: Security risk, use encrypted storage (Keychain/Keystore)

## Open Questions

Things that couldn't be fully resolved:

1. **FlashList Masonry Layout Stability**
   - What we know: FlashList 1.x has built-in masonry support with `masonry={true}` prop (as of mid-2025)
   - What's unclear: Production stability of masonry layout in Jan 2026, edge cases with variable heights
   - Recommendation: Test FlashList masonry early. Fallback to react-native-masonry if unstable.

2. **Vision Camera Photo Quality vs Native Camera**
   - What we know: GitHub issue #3008 discusses photo quality differences from native camera app on iOS
   - What's unclear: Whether Vision Camera 4.x (Jan 2026) achieves parity with native iPhone camera for iris photography
   - Recommendation: Validate photo quality on iPhone 12+ with iris samples. Use `photoQualityBalance="quality"` and max resolution format.

3. **Upload Timing Strategy (Immediate vs Background)**
   - What we know: CONTEXT says "immediate upload" after accept. No background queue in Phase 2.
   - What's unclear: If immediate upload blocks user (show spinner?) or returns to gallery immediately and uploads in background
   - Recommendation: Clarify with user in Phase 2 planning. Suggest: Navigate to gallery immediately, show progress bar on photo thumbnail (CONTEXT says this).

4. **Photo Detail View on Tap**
   - What we know: CONTEXT leaves this to Claude's discretion: "full-screen with zoom vs detail card"
   - What's unclear: User preference, impact on Phase 3 AI processing results display
   - Recommendation: Full-screen with zoom (standard gallery pattern). Phase 3 can add AI metadata overlay.

5. **Camera Permission Denied Fallback**
   - What we know: CONTEXT leaves to Claude's discretion: "blocked screen with settings link vs gallery-only fallback"
   - What's unclear: If app is useful without camera (can view existing photos but not capture)
   - Recommendation: Show blocked screen with "Open Settings" button + gallery-only mode. Iris art app needs camera.

## Sources

### Primary (HIGH confidence)

- **Vision Camera Official Docs** - https://react-native-vision-camera.com/
  - Taking Photos: https://react-native-vision-camera.com/docs/guides/taking-photos
  - Camera Devices: https://react-native-vision-camera.com/docs/guides/devices
  - Zooming: https://react-native-vision-camera.com/docs/guides/zooming
  - Performance: https://react-native-vision-camera.com/docs/guides/performance
  - Frame Processors: https://react-native-vision-camera.com/docs/guides/frame-processors
- **React Navigation Official Docs** - https://reactnavigation.org/
  - Getting Started: https://reactnavigation.org/docs/getting-started/
  - Native Stack Navigator: https://reactnavigation.org/docs/native-stack-navigator/
- **React Native Official Docs**
  - Security: https://reactnative.dev/docs/security
  - Testing Overview: https://reactnative.dev/docs/testing-overview
  - TypeScript: https://reactnative.dev/docs/typescript
  - Running On Device: https://reactnative.dev/docs/running-on-device
- **react-native-permissions GitHub** - https://github.com/zoontek/react-native-permissions
- **FlashList Docs** - https://shopify.github.io/flash-list/
- **React Query Docs** - https://tanstack.com/query/latest/docs/framework/react/overview

### Secondary (MEDIUM confidence)

- **LogRocket: Implementing camera functionality in React Native** (2024) - https://blog.logrocket.com/implementing-camera-functionality-react-native/
- **LogRocket: Managing app permissions in React Native** (2024) - https://blog.logrocket.com/react-native-permissions/
- **LogRocket: React Native end-to-end testing with Detox** - https://blog.logrocket.com/react-native-end-to-end-testing-detox/
- **Medium: React Native Custom Image Picker With Upload Progress** - https://medium.com/@istvanistvan/react-native-custom-image-picker-with-upload-progress-5444e955455c
- **Medium: React Native Basics: Mastering Secure Storage Solutions** (2024) - https://medium.com/@shahidrogers/react-native-basics-mastering-secure-storage-solutions-071a0fc75201
- **Medium: Building a React Native App: Part IV, Onboarding Screens** - https://medium.com/@rafiulansari/building-a-react-native-app-part-iv-onboarding-screens-6ef48caefd6c
- **Instamobile: Upload Images & Videos to AWS S3 Bucket in React Native** - https://instamobile.io/react-native-tutorials/react-native-aws-s3/
- **BrowserStack: Testing React Native Apps on iOS and Android [2026]** - https://www.browserstack.com/guide/test-react-native-apps-ios-android
- **Copyprogramming: React Native Background Upload: Complete Guide with Latest Features and Best Practices 2026** - https://copyprogramming.com/howto/react-native-background-upload
- **DEV Community: Simple Step-by-Step Setup Detox for React Native Android E2E Testing | 2026** (Jan 2026) - https://medium.com/@svbala99/simple-step-by-step-setup-detox-for-react-native-android-e2e-testing-2026-ed497fd9d301
- **DEV Community: Mastering Media Uploads in React Native — Images, Videos & Smart Compression (2026 Guide)** - https://dev.to/fasthedeveloper/mastering-media-uploads-in-react-native-images-videos-smart-compression-2026-guide-5g2i

### Tertiary (LOW confidence)

- **React Native folder structure discussions** (2025-2026) - Various Medium articles and dev blogs
- **React Native app onboarding patterns** (2025-2026) - Vocal.media and OpenReplay
- **React Native optimization guides** (2025-2026) - Multiple blogs discussing performance

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - Vision Camera, React Navigation, FlashList are industry standard with recent 2026 versions verified
- Architecture: **HIGH** - Patterns verified from official docs (Vision Camera, React Navigation, React Native Security)
- Pitfalls: **MEDIUM** - Common issues documented in GitHub issues and community blogs, need validation in practice
- Upload strategy: **MEDIUM** - Immediate upload approach standard, but CONTEXT leaves timing unclear (block UI vs background)
- Masonry gallery: **MEDIUM** - FlashList masonry is recent feature (mid-2025), production stability needs validation

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (30 days - React Native ecosystem is stable, major changes unlikely in 1 month)

---

**Next Steps for Planning:**

1. **Validate Vision Camera photo quality**: Capture test iris photos on iPhone 12 and compare to native camera app (GitHub issue #3008)
2. **Test FlashList masonry layout**: Build prototype gallery with 50+ variable-height images to validate performance and layout
3. **Clarify upload timing**: Decide if immediate upload blocks UI (spinner) or shows progress on thumbnail (CONTEXT mentions progress bar on thumbnail)
4. **Device matrix definition**: Define exact iOS and Android devices for testing (CONTEXT: iPhone 12+, 12MP+ Android)
5. **Photo detail view decision**: Full-screen with zoom vs detail card (CONTEXT: Claude's discretion)
6. **Permission denied UX decision**: Blocked screen only vs gallery-only fallback mode (CONTEXT: Claude's discretion)
