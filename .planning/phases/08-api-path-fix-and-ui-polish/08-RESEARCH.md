# Phase 8: API Path Fix and UI Polish - Research

**Researched:** 2026-02-10
**Domain:** React Native API integration, mobile file system operations, iOS/Android permissions
**Confidence:** HIGH

## Summary

Phase 8 addresses two critical gap closures from the v1.0 milestone audit:

1. **API Path Double-Prefix Bug**: Six service files (circles, invites, fusion, artworkConsent, exports, styles) are making API calls with paths like `/api/v1/circles` when the axios baseURL is already set to `http://localhost:8000/api/v1`, resulting in doubled paths (`/api/v1/api/v1/circles`) and 404 errors.

2. **Save to Device Missing**: Three result screens (ProcessingResultScreen, StylePreviewScreen, FusionResultScreen) have placeholder "Save to Device" functionality that needs to be implemented with actual camera roll/media library integration.

The root cause of the API path issue is clear: the axios client in `mobile/src/services/api.ts` sets `baseURL` to include `/api/v1`, but service files are including `/api/v1` again in their endpoint paths. The backend FastAPI routers already include `/api/v1` prefix in their route definitions, so mobile services should use paths relative to `/api/v1` (e.g., `/circles` not `/api/v1/circles`).

**Primary recommendation:** Remove `/api/v1` prefix from all service file endpoints and implement `@react-native-camera-roll/camera-roll` with react-native-fs for downloading remote images before saving to camera roll.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @react-native-camera-roll/camera-roll | ^7.8+ | Save images to device photo library | Official React Native community package, successor to deprecated CameraRoll API |
| react-native-fs | ^2.20+ (already installed) | Download remote images to temp storage before saving | Most popular RN file system library, required for downloading URLs before CameraRoll.save |
| react-native-permissions | ^5.4.4 (already installed) | Request iOS/Android photo library permissions | Already in package.json, handles permission flows |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| axios | ^1.13.4 (already installed) | HTTP client with interceptors | Already configured in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @react-native-camera-roll/camera-roll | expo-media-library | Expo-specific, requires Expo ecosystem. Not suitable for bare React Native project |
| react-native-fs | rn-fetch-blob | rn-fetch-blob is more feature-rich but heavier. react-native-fs is simpler and already installed |

**Installation:**
```bash
# Only need to add camera-roll package
npm install @react-native-camera-roll/camera-roll
# Then link native modules
cd ios && pod install && cd ..
```

## Architecture Patterns

### Recommended Service File Structure
```
mobile/src/services/
├── api.ts                 # Axios instance with baseURL: '/api/v1'
├── circles.ts             # Endpoints like '/circles' (NOT '/api/v1/circles')
├── invites.ts             # Endpoints like '/invites/{token}/info'
├── fusion.ts              # Endpoints like '/fusion'
├── artworkConsent.ts      # Endpoints like '/consent/request'
├── exports.ts             # Endpoints like '/exports/hd'
└── styles.ts              # Endpoints like '/styles/presets'
```

### Pattern 1: Relative API Paths
**What:** All service files use paths relative to the baseURL defined in api.ts
**When to use:** Always, when using an axios instance with a baseURL
**Example:**
```typescript
// ❌ WRONG - Double prefix
import apiClient from './api'; // baseURL: 'http://localhost:8000/api/v1'
export const getCircles = async (): Promise<Circle[]> => {
  const response = await apiClient.get<Circle[]>('/api/v1/circles');
  // Results in: GET http://localhost:8000/api/v1/api/v1/circles (404)
  return response.data;
};

// ✅ CORRECT - Relative to baseURL
import apiClient from './api'; // baseURL: 'http://localhost:8000/api/v1'
export const getCircles = async (): Promise<Circle[]> => {
  const response = await apiClient.get<Circle[]>('/circles');
  // Results in: GET http://localhost:8000/api/v1/circles (200)
  return response.data;
};
```

### Pattern 2: Download-Then-Save for Remote Images
**What:** Remote images must be downloaded to local file system before CameraRoll.save
**When to use:** When saving images from backend URLs to device photo library
**Example:**
```typescript
// Source: react-native-fs + @react-native-camera-roll/camera-roll pattern
import RNFS from 'react-native-fs';
import {CameraRoll} from '@react-native-camera-roll/camera-roll';
import {Alert} from 'react-native';

const handleSaveToDevice = async (imageUrl: string) => {
  try {
    // 1. Download remote image to temp directory
    const tempPath = `${RNFS.TemporaryDirectoryPath}/${Date.now()}.jpg`;
    const download = await RNFS.downloadFile({
      fromUrl: imageUrl,
      toFile: tempPath,
    }).promise;

    if (download.statusCode !== 200) {
      throw new Error('Download failed');
    }

    // 2. Save local file to camera roll
    await CameraRoll.save(`file://${tempPath}`, {type: 'photo'});

    // 3. Clean up temp file
    await RNFS.unlink(tempPath);

    Alert.alert('Success', 'Image saved to camera roll!');
  } catch (error) {
    console.error('Failed to save image:', error);
    Alert.alert('Error', 'Failed to save image to device.');
  }
};
```

### Pattern 3: Permission Request Before Save
**What:** Check and request photo library permissions before attempting to save
**When to use:** Always, before any CameraRoll.save operation
**Example:**
```typescript
// Source: react-native-permissions + @react-native-camera-roll/camera-roll
import {Platform, Alert} from 'react-native';
import {check, request, PERMISSIONS, RESULTS} from 'react-native-permissions';
import {CameraRoll} from '@react-native-camera-roll/camera-roll';

const requestPhotoLibraryPermission = async (): Promise<boolean> => {
  const permission = Platform.select({
    ios: PERMISSIONS.IOS.PHOTO_LIBRARY_ADD_ONLY,
    android: Platform.Version >= 33
      ? PERMISSIONS.ANDROID.READ_MEDIA_IMAGES
      : PERMISSIONS.ANDROID.WRITE_EXTERNAL_STORAGE,
  });

  if (!permission) return false;

  const result = await check(permission);

  if (result === RESULTS.GRANTED) {
    return true;
  }

  if (result === RESULTS.DENIED) {
    const requestResult = await request(permission);
    return requestResult === RESULTS.GRANTED;
  }

  // BLOCKED or LIMITED
  Alert.alert(
    'Permission Required',
    'Please enable photo library access in Settings to save images.',
    [{text: 'OK'}]
  );
  return false;
};

// Use before save
const handleSave = async (imageUrl: string) => {
  const hasPermission = await requestPhotoLibraryPermission();
  if (!hasPermission) return;

  // Proceed with download-then-save...
};
```

### Anti-Patterns to Avoid
- **Hard-coding full URLs in service files**: Don't include protocol, domain, or `/api/v1` in endpoint paths when using an axios instance with baseURL
- **Saving remote URLs directly to CameraRoll**: iOS supports remote URLs but Android requires local file URIs. Always download first for cross-platform consistency
- **Missing permission checks**: CameraRoll.save will crash on iOS without proper Info.plist keys and permission grants

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image download and save | Custom native module with platform-specific code | react-native-fs + @react-native-camera-roll/camera-roll | Cross-platform permission handling, album selection, and file format detection are complex |
| Permission state management | Manual permission tracking | react-native-permissions | Handles all permission states (GRANTED, DENIED, BLOCKED, LIMITED), platform differences, and Settings navigation |
| HTTP client configuration | Custom fetch wrapper | axios with interceptors | Already configured in project with JWT refresh, error handling, and baseURL |

**Key insight:** File system operations and photo library access have significant platform differences (iOS supports NSPrivacy keys, Android 13+ uses scoped storage). Community packages handle these edge cases.

## Common Pitfalls

### Pitfall 1: Double API Path Prefix
**What goes wrong:** Service files include `/api/v1` in endpoint paths when baseURL already contains it, resulting in 404 errors
**Why it happens:** Backend route definitions show full paths with prefix (e.g., `router = APIRouter(prefix="/api/v1/circles")`), tempting developers to copy these paths directly to mobile service calls
**How to avoid:** Always use paths relative to the axios baseURL. If baseURL is `http://localhost:8000/api/v1`, use `/circles` not `/api/v1/circles`
**Warning signs:** 404 errors in E2E flows, doubled paths in network logs showing `/api/v1/api/v1/...`

### Pitfall 2: iOS Photo Library Permission Keys Missing
**What goes wrong:** App crashes on iOS when attempting to save to camera roll
**Why it happens:** iOS 14+ requires NSPhotoLibraryAddUsageDescription in Info.plist for write-only access
**How to avoid:** Add required keys to `mobile/ios/IrisArt/Info.plist` before testing save functionality:
```xml
<key>NSPhotoLibraryAddUsageDescription</key>
<string>Save your iris artwork to your photo library</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Access your photos to share iris artwork</string>
```
**Warning signs:** App exits immediately when CameraRoll.save is called on iOS without any error message

### Pitfall 3: Android Scoped Storage and File URIs
**What goes wrong:** CameraRoll.save fails on Android with "file not found" errors
**Why it happens:** Android 10+ (API 29) enforces scoped storage; CameraRoll.save requires `file://` URI prefix for local files
**How to avoid:** Use react-native-fs to download to `RNFS.TemporaryDirectoryPath`, then pass `file://${tempPath}` to CameraRoll.save. Clean up temp file after save
**Warning signs:** Save works on iOS but fails silently on Android, or "invalid URI" errors in Android logs

### Pitfall 4: Backend Route Inconsistency
**What goes wrong:** Some service files work, others get 404s, confusing debugging
**Why it happens:** Backend routers have inconsistent prefix application. Some routes define prefix in APIRouter(), others get prefix added by app.include_router() in main.py
**How to avoid:** Check backend route registration. Current state:
  - circles.router has prefix="/circles" (relies on main.py adding /api/v1)
  - invites.router has prefix="/circles" (invites under circles namespace)
  - consent.router has prefix="/consent" (relies on main.py adding /api/v1)
  - fusion.router has prefix="/api/v1" (includes full prefix)
  - styles.router has prefix="/api/v1/styles" (includes full prefix)
  - exports.router has prefix="/api/v1/exports" (includes full prefix)

Mobile services should match these by checking main.py include_router calls to see if additional prefix is added.

**Warning signs:** Some API calls work (styles, exports) while others fail (circles, invites) with identical code patterns

## Code Examples

Verified patterns from codebase analysis:

### Fix API Path in Service Files
```typescript
// File: mobile/src/services/circles.ts
// BEFORE (WRONG):
export const getCircles = async (): Promise<Circle[]> => {
  const response = await apiClient.get<Circle[]>('/api/v1/circles');
  return response.data;
};

// AFTER (CORRECT):
export const getCircles = async (): Promise<Circle[]> => {
  const response = await apiClient.get<Circle[]>('/circles');
  return response.data;
};

// File: mobile/src/services/invites.ts
// BEFORE (WRONG):
export const createInvite = async (circleId: string): Promise<InviteResponse> => {
  const response = await apiClient.post<InviteResponse>(
    `/api/v1/circles/${circleId}/invite`
  );
  return response.data;
};

// AFTER (CORRECT):
export const createInvite = async (circleId: string): Promise<InviteResponse> => {
  const response = await apiClient.post<InviteResponse>(
    `/circles/${circleId}/invite`
  );
  return response.data;
};
```

### Implement Save to Device
```typescript
// File: mobile/src/screens/Processing/ProcessingResultScreen.tsx
// BEFORE (PLACEHOLDER):
const handleSaveToDevice = async () => {
  if (!job || !job.result_url) {
    return;
  }

  try {
    // TODO: Implement save to device using CameraRoll or MediaLibrary
    Alert.alert(
      'Save to Device',
      'Image download and save functionality will be implemented with platform-specific permissions.',
    );
  } catch (error) {
    Alert.alert('Error', 'Failed to save image to device.');
  }
};

// AFTER (IMPLEMENTED):
import RNFS from 'react-native-fs';
import {CameraRoll} from '@react-native-camera-roll/camera-roll';
import {check, request, PERMISSIONS, RESULTS} from 'react-native-permissions';

const requestPhotoPermission = async (): Promise<boolean> => {
  const permission = Platform.select({
    ios: PERMISSIONS.IOS.PHOTO_LIBRARY_ADD_ONLY,
    android: Platform.Version >= 33
      ? PERMISSIONS.ANDROID.READ_MEDIA_IMAGES
      : PERMISSIONS.ANDROID.WRITE_EXTERNAL_STORAGE,
  });

  if (!permission) return false;

  const result = await check(permission);
  if (result === RESULTS.GRANTED) return true;

  if (result === RESULTS.DENIED) {
    const requestResult = await request(permission);
    return requestResult === RESULTS.GRANTED;
  }

  Alert.alert(
    'Permission Required',
    'Please enable photo library access in Settings to save images.',
  );
  return false;
};

const handleSaveToDevice = async () => {
  if (!job || !job.result_url) {
    return;
  }

  try {
    // 1. Request permission
    const hasPermission = await requestPhotoPermission();
    if (!hasPermission) return;

    // 2. Download remote image
    const tempPath = `${RNFS.TemporaryDirectoryPath}/iris_${Date.now()}.jpg`;
    const download = await RNFS.downloadFile({
      fromUrl: job.result_url,
      toFile: tempPath,
    }).promise;

    if (download.statusCode !== 200) {
      throw new Error('Download failed');
    }

    // 3. Save to camera roll
    await CameraRoll.save(`file://${tempPath}`, {type: 'photo'});

    // 4. Clean up
    await RNFS.unlink(tempPath);

    Alert.alert('Success', 'Iris artwork saved to your photo library!');
  } catch (error) {
    console.error('Failed to save image:', error);
    Alert.alert('Error', 'Failed to save image to device. Please try again.');
  }
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| @react-native-community/cameraroll | @react-native-camera-roll/camera-roll | 2021 | New org maintains package separately from core RN |
| react-native built-in CameraRoll | Community package @react-native-camera-roll/camera-roll | RN 0.59+ | Core API deprecated, moved to community package |
| WRITE_EXTERNAL_STORAGE on all Android versions | READ_MEDIA_IMAGES for Android 13+ (API 33) | Android 13 (2022) | Scoped storage requires different permissions |
| iOS NSPhotoLibraryUsageDescription (read/write) | iOS NSPhotoLibraryAddUsageDescription (write-only) | iOS 14 (2020) | Write-only permission more privacy-friendly |

**Deprecated/outdated:**
- **React Native built-in CameraRoll**: Deprecated in RN 0.59, removed in 0.60. Use @react-native-camera-roll/camera-roll instead
- **WRITE_EXTERNAL_STORAGE on Android 13+**: Use READ_MEDIA_IMAGES instead for scoped storage compliance

## Open Questions

1. **Backend route prefix inconsistency**
   - What we know: Some routers define full `/api/v1/prefix` while others rely on main.py to add it
   - What's unclear: Whether this is intentional design or accumulated inconsistency
   - Recommendation: Document expected pattern and fix mobile services to match current backend state

2. **Album selection for saved images**
   - What we know: CameraRoll.save accepts `album` parameter on iOS
   - What's unclear: Whether users expect images in a custom "IrisArt" album or default Photos
   - Recommendation: Start with default album (no album parameter), add custom album in future iteration if users request it

3. **HD export vs regular save behavior**
   - What we know: HDExportScreen exists for paid HD exports with watermark removal
   - What's unclear: Whether "Save to Device" on result screens should prompt for HD upgrade or save current resolution
   - Recommendation: Save current resolution shown on screen. HD export is separate feature accessed via "Export HD" button

## Sources

### Primary (HIGH confidence)
- **Codebase analysis** - mobile/src/services/*.ts, mobile/src/utils/constants.ts, backend/app/api/routes/*.py, backend/app/main.py
- **package.json** - mobile/package.json shows react-native-fs 2.20.0 and react-native-permissions 5.4.4 already installed
- [@react-native-camera-roll/camera-roll npm](https://www.npmjs.com/package/@react-native-camera-roll/camera-roll) - Official package documentation
- [@react-native-camera-roll/camera-roll GitHub](https://github.com/react-native-cameraroll/react-native-cameraroll) - Community repository

### Secondary (MEDIUM confidence)
- [Using react-native-cameraroll - LogRocket](https://blog.logrocket.com/using-react-native-cameraroll/) - Implementation patterns and permission handling
- [react-native-fs GitHub](https://github.com/itinance/react-native-fs) - Download file examples and API documentation
- [React Native permissions guide](https://www.npmjs.com/package/react-native-permissions) - Platform-specific permission handling

### Tertiary (LOW confidence)
- [How to save remote image with react native - GitHub Gist](https://gist.github.com/majiyd/cebfdfdc94a5d2d2a7af99bb27f887bf) - Community code snippet (not verified)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - @react-native-camera-roll/camera-roll is official community package, react-native-fs is most popular file system library and already installed
- Architecture: HIGH - Patterns verified against actual codebase service files and backend route definitions
- Pitfalls: HIGH - Double prefix issue confirmed in 6 service files, iOS permission keys documented in Apple guidelines

**Research date:** 2026-02-10
**Valid until:** 2026-03-12 (30 days - stable ecosystem)
