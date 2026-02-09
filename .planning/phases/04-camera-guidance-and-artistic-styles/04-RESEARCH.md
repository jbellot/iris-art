# Phase 4: Camera Guidance and Artistic Styles - Research

**Researched:** 2026-02-09
**Domain:** Real-time camera guidance, on-device ML inference, artistic style transfer, and AI-generated compositions
**Confidence:** HIGH

## Summary

Phase 4 implements three interconnected features: (1) real-time AI camera guidance with iris detection, alignment, and quality feedback, (2) fast neural style transfer for preset artistic styles, and (3) Stable Diffusion-based AI-generated unique compositions. The research confirms that the existing stack (React Native + Vision Camera + FastAPI backend) is well-suited for this phase with strategic additions.

The critical technical decisions are: (1) using React Native Vision Camera Frame Processors with worklets for real-time on-device processing (1ms overhead vs native), (2) deploying Fast Neural Style Transfer models via ONNX Runtime for mobile inference (real-time at 512×512 on modern devices), (3) using SDXL Turbo for fast backend inference (under 200ms for 1024×1024 on consumer GPUs), (4) implementing progressive image enhancement via FastAPI StreamingResponse for low-res preview followed by HD enhancement, and (5) applying watermarks server-side to prevent client-side circumvention.

The primary challenges are: (1) integrating MediaPipe or TensorFlow Lite for on-device iris detection (MediaPipe provides 478 face landmarks including 10 iris landmarks but may be heavyweight; TFLite offers better control), (2) optimizing frame processor performance to stay within 16-33ms budget at 30-60 FPS, (3) selecting and converting Fast Neural Style Transfer models to ONNX format (5-10MB models, ~50-200ms inference on mobile), (4) managing Real-ESRGAN memory requirements (4GB VRAM, 6s at 512×512→2048×2048 on high-end GPU), and (5) implementing best-frame selection from burst capture using blur detection (Laplacian variance is fast and proven).

**Primary recommendation:** Build camera guidance using Vision Camera Frame Processors + custom TFLite iris detection model (faster than MediaPipe's full face mesh), implement style transfer on-device with ONNX Runtime for free presets (instant preview), run premium styles and AI generation server-side (Celery tasks with Real-ESRGAN + SDXL Turbo), use progressive enhancement (low-res preview → HD streaming), and apply watermarks server-side during final export to protect paid features.

## Standard Stack

### Core - Mobile (Camera Guidance + On-Device Styles)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **react-native-vision-camera** | 4.7.3 | Camera + Frame Processors | Already in stack (Phase 1-2), supports 60+ FPS frame processing with 1ms overhead, native plugin ecosystem, worklets integration |
| **react-native-worklets-core** | 0.7.2 | JS runtime for frame processors | Already in stack (reanimated 4.2 peer dep), enables synchronous frame processing off main thread |
| **onnxruntime-react-native** | latest | On-device ML inference | Cross-platform ONNX model execution, 10-15MB binary (reducible to 4-5MB), CPU/GPU/XNNPACK acceleration |
| **react-native-fast-tflite** | latest | TensorFlow Lite inference | High-performance TFLite for React Native with GPU acceleration, faster than MediaPipe for single-task inference |
| **react-native-image-marker** | 1.2.9 | Watermark overlay (client-side preview) | Native performance for text/image watermarks on iOS/Android, used only for preview (server applies final watermark) |

### Core - Backend (Style Transfer + AI Generation)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Real-ESRGAN** | latest | HD upscaling (4x/8x) | Already planned (Phase 3), 4GB VRAM, 6s inference at 512→2048, battle-tested for quality enhancement |
| **Stable Diffusion (SDXL Turbo)** | latest | Fast AI art generation | 1-4 step inference, under 200ms at 1024×1024 on consumer GPU, 95% faster than vanilla SDXL with 98% visual fidelity |
| **diffusers** (Hugging Face) | latest | SD pipeline integration | Official Python library for Stable Diffusion, img2img support, ControlNet integration, Celery-compatible |
| **Pillow** | 11.x | Image watermarking (server) | Already in stack (Phase 3), server-side watermark prevents client bypass |

### Supporting - Mobile

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **react-native-progressive-fast-image** | latest | Progressive image loading | Display low-res preview while HD loads, blur-to-sharp transition for UX |
| **react-native-fs** | latest | HD image save to device | Export paid HD images to device gallery |
| **opencv-python** (frame analysis) | 4.10.x | Blur detection, brightness calc | Used in custom Frame Processor plugin for best-frame selection |

### Supporting - Backend

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **controlnet** (diffusers extension) | latest | Composition control for SD | Guide SD generation with iris edge/color maps for artistic coherence |
| **scikit-image** | 0.24.x | SSIM/PSNR quality metrics | Already in stack (Phase 3), measure quality between low-res and HD versions |

### AI Models by Feature

| Feature | Model | Deployment | Why Chosen | Confidence |
|---------|-------|-----------|------------|------------|
| **Iris Detection** | Custom TFLite iris detector OR MediaPipe Face Mesh | On-device mobile | TFLite: lightweight, single-task, <50ms. MediaPipe: 478 landmarks including 10 iris points, proven but heavier | HIGH |
| **Blur Detection** | Laplacian variance (OpenCV) | On-device in Frame Processor | Fast (<5ms), single float output, proven in production, threshold-tunable | HIGH |
| **Lighting Analysis** | Brightness calculation (luminance average) | On-device in Frame Processor | Sample 30-pixel subset in center, <5ms, threshold-based feedback | HIGH |
| **Free Style Presets** | Fast Neural Style Transfer (5-10 models) | On-device ONNX | Real-time 512×512 on mobile CPU, 5-10MB per model, pre-trained available | MEDIUM |
| **Premium Style Presets** | Fast NST OR Real-ESRGAN+style | Backend Celery | Server-side: no model size limits, higher quality, protects paid features | HIGH |
| **AI-Generated Art** | SDXL Turbo + ControlNet | Backend Celery | <200ms inference, composition control via iris edge maps, unique outputs | HIGH |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TFLite for iris detection | MediaPipe Face Mesh | MediaPipe heavier (478 landmarks vs ~5 iris points), but more feature-complete if face tracking needed later |
| ONNX Runtime mobile | PyTorch Mobile | PyTorch Mobile 10-15MB larger binary, ONNX better cross-platform tooling and optimization |
| SDXL Turbo | SDXL 1.0 (50 steps) | Vanilla SDXL 10-30s inference, Turbo <200ms but slightly lower fidelity (98% vs 100%) |
| Server-side watermark | Client-side only | Client-side can be bypassed via decompilation, server-side protects revenue |
| Fast NST on-device | All styles server-side | On-device gives instant preview for free styles, reduces server load, improves UX |

**Installation:**
```bash
# Mobile (React Native)
npm install onnxruntime-react-native
npm install react-native-fast-tflite
npm install react-native-image-marker
npm install react-native-progressive-fast-image
npm install react-native-fs

# Backend (Python) - add to requirements.txt
diffusers>=0.30.0
transformers>=4.40.0
accelerate>=0.30.0
xformers  # Optional: faster attention for SD
controlnet_aux  # ControlNet preprocessors
```

## Architecture Patterns

### Recommended Project Structure

```
mobile/
├── src/
│   ├── screens/
│   │   └── Camera/
│   │       ├── CameraScreen.tsx              # Existing
│   │       └── CameraGuidanceOverlay.tsx     # NEW: Real-time feedback overlay
│   │       └── StyleGalleryScreen.tsx        # NEW: Browse/apply styles
│   │       └── StylePreviewScreen.tsx        # NEW: Before/after + export
│   ├── components/
│   │   └── Camera/
│   │       ├── IrisAlignmentGuide.tsx        # NEW: Circular guide + distance
│   │       ├── FocusQualityIndicator.tsx     # NEW: Sharpness feedback
│   │       ├── LightingIndicator.tsx         # NEW: Too dark/bright warning
│   │       └── BurstCaptureButton.tsx        # NEW: Multi-frame capture
│   │   └── Styles/
│   │       ├── StyleThumbnail.tsx            # NEW: Preview thumbnail
│   │       ├── ProgressiveImage.tsx          # NEW: Low-res → HD transition
│   │       └── WatermarkOverlay.tsx          # NEW: Client preview watermark
│   ├── hooks/
│   │   └── useStyleTransfer.ts               # NEW: Apply styles, track progress
│   │   └── useIrisDetection.ts               # NEW: Frame processor integration
│   ├── services/
│   │   └── styles.ts                         # NEW: API calls for server styles
│   │   └── onnx.ts                           # NEW: ONNX model loading
│   └── frameProcessors/
│       ├── irisDetection.ts                  # NEW: TFLite/MediaPipe wrapper
│       ├── blurDetection.ts                  # NEW: Laplacian variance
│       ├── lightingAnalysis.ts               # NEW: Brightness calculation
│       └── bestFrameSelector.ts              # NEW: Score frames, select best

backend/
├── app/
│   ├── workers/
│   │   ├── models/
│   │   │   ├── model_cache.py                # Existing (Phase 3)
│   │   │   ├── style_transfer_model.py       # NEW: Fast NST wrapper
│   │   │   ├── sd_generator.py               # NEW: SDXL Turbo pipeline
│   │   │   └── controlnet_processor.py       # NEW: Edge/color extraction
│   │   └── tasks/
│   │       ├── processing.py                 # Existing (Phase 3)
│   │       ├── style_transfer.py             # NEW: Apply preset styles
│   │       ├── ai_generation.py              # NEW: SD unique art
│   │       └── hd_export.py                  # NEW: Upscale + watermark
│   ├── api/
│   │   └── routes/
│   │       ├── styles.py                     # NEW: List/apply styles
│   │       └── exports.py                    # NEW: HD export endpoint
│   ├── models/
│   │   ├── style_preset.py                   # NEW: Preset definitions
│   │   ├── style_job.py                      # NEW: Job tracking
│   │   └── export_job.py                     # NEW: Export tracking
│   └── services/
│       ├── watermark.py                      # NEW: Server-side watermark logic
│       └── progressive_export.py             # NEW: StreamingResponse helper
```

### Pattern 1: Frame Processor for Real-Time Guidance

**What:** Use Vision Camera Frame Processors with native plugins (Swift/Kotlin/C++) for iris detection, blur analysis, and lighting checks. Process frames at camera FPS (30-60), display overlay feedback.

**When to use:** Real-time camera guidance where latency <50ms is critical.

**Example:**
```typescript
// frameProcessors/irisDetection.ts
import { VisionCameraProxy } from 'react-native-vision-camera';

// Register native frame processor plugin (written in Swift/Kotlin)
const plugin = VisionCameraProxy.initFrameProcessorPlugin('detectIris');

export function detectIris(frame: Frame) {
  'worklet';
  if (plugin == null) return null;

  // Native plugin returns: { detected: boolean, centerX: number, centerY: number, radius: number, distance: number, sharpness: number }
  return plugin.call(frame) as IrisDetectionResult | null;
}

// CameraGuidanceOverlay.tsx
const frameProcessor = useFrameProcessor((frame) => {
  'worklet';
  const iris = detectIris(frame);
  const blur = detectBlur(frame);
  const lighting = analyzeLighting(frame);

  // Update UI state via runOnJS
  runOnJS(updateGuidanceState)({
    irisDetected: iris?.detected ?? false,
    irisDistance: iris?.distance ?? 0,
    focusQuality: blur?.sharpness ?? 0,
    lightingScore: lighting?.brightness ?? 0,
  });
}, []);
```

**Performance constraint:** At 30 FPS, you have 33ms per frame. At 60 FPS, only 16ms. Budget: iris detection <30ms, blur <5ms, lighting <5ms, overhead ~1ms = total ~41ms. **Must skip frames or reduce FPS to 30 to stay within budget.**

### Pattern 2: Burst Capture with Best-Frame Selection

**What:** Capture 3-5 frames rapidly (burst mode), analyze each for sharpness and alignment, auto-select best frame.

**When to use:** User taps shutter once, system ensures optimal quality without user retry.

**Example:**
```typescript
// BurstCaptureButton.tsx
async function captureWithBurst() {
  const frames: PhotoFile[] = [];

  // Capture 3 frames 200ms apart
  for (let i = 0; i < 3; i++) {
    const photo = await cameraRef.current?.takePhoto({ flash });
    if (photo) frames.push(photo);
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  // Analyze frames for quality
  const scores = await Promise.all(
    frames.map(async (frame) => {
      const sharpness = await analyzeSharpness(frame.path);
      const alignment = await analyzeIrisAlignment(frame.path);
      return { frame, score: sharpness * 0.7 + alignment * 0.3 };
    })
  );

  // Select best frame
  const best = scores.reduce((a, b) => a.score > b.score ? a : b);
  return best.frame;
}
```

**Source:** [Blur detection with OpenCV - PyImageSearch](https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv/) shows Laplacian variance for sharpness scoring.

### Pattern 3: On-Device Style Transfer with ONNX

**What:** Load Fast Neural Style Transfer models as ONNX files in app bundle, run inference on-device for instant preview of free styles.

**When to use:** Free preset styles where instant feedback is critical and model size <10MB per style is acceptable.

**Example:**
```typescript
// services/onnx.ts
import * as ort from 'onnxruntime-react-native';

let session: ort.InferenceSession | null = null;

export async function loadStyleModel(styleName: string) {
  const modelPath = `bundle://models/${styleName}.onnx`;
  session = await ort.InferenceSession.create(modelPath);
}

export async function applyStyleOnDevice(imageUri: string): Promise<string> {
  if (!session) throw new Error('Model not loaded');

  // Preprocess image to 512×512 tensor
  const inputTensor = await preprocessImage(imageUri, 512, 512);

  // Run inference (50-200ms on modern mobile CPU)
  const results = await session.run({ input: inputTensor });

  // Postprocess tensor to image URI
  return postprocessToUri(results.output);
}
```

**Source:** [Design and experimental research of on device style transfer models for mobile environments](https://www.nature.com/articles/s41598-025-98545-4) shows real-time 512×512 inference on mobile CPU.

### Pattern 4: Progressive Enhancement (Server-Side)

**What:** Generate low-res styled image (256×256) instantly, stream to client for preview. Then generate HD (2048×2048), stream progressively as chunks become available.

**When to use:** Premium styles and AI-generated art where quality trumps speed and server has better hardware.

**Example:**
```python
# backend/app/services/progressive_export.py
from fastapi.responses import StreamingResponse
import io

async def generate_progressive_styled_image(image_id: int, style_id: int):
    # Generate low-res preview (256×256, ~1-2s)
    preview = await generate_preview(image_id, style_id, size=256)
    yield encode_chunk(preview, quality=70)

    # Generate HD (2048×2048, ~10-20s with Real-ESRGAN)
    hd = await generate_hd(image_id, style_id, size=2048)

    # Stream HD in chunks (progressive JPEG)
    for chunk in stream_jpeg_progressive(hd):
        yield chunk

# app/api/routes/styles.py
@router.get("/styles/{job_id}/stream")
async def stream_styled_image(job_id: int):
    return StreamingResponse(
        generate_progressive_styled_image(...),
        media_type="image/jpeg"
    )
```

**Source:** [FastAPI Streaming Response](https://medium.com/@ab.hassanein/streaming-responses-in-fastapi-d6a3397a4b7b) shows chunked transfer with generators.

### Pattern 5: Server-Side Watermark for Paid Features

**What:** Apply watermark during final export on server, not client. Client shows watermark overlay for preview only. Server checks payment status before generating watermark-free HD export.

**When to use:** Protecting paid HD exports from client-side bypass.

**Example:**
```python
# backend/app/services/watermark.py
from PIL import Image, ImageDraw, ImageFont

def apply_watermark(image: Image.Image, is_paid: bool) -> Image.Image:
    if is_paid:
        return image  # No watermark for paid users

    # Add watermark for free users
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 48)
    draw.text((50, 50), "IrisArt - Free Preview", font=font, fill=(255, 255, 255, 128))
    return image

# app/workers/tasks/hd_export.py
@celery_app.task
def export_hd_image(user_id: int, image_id: int):
    user = get_user(user_id)
    image = load_processed_image(image_id)

    # Check if user has paid for HD export
    is_paid = check_hd_export_purchased(user_id, image_id)

    # Apply watermark based on payment status
    final = apply_watermark(image, is_paid=is_paid)

    # Upload to S3
    url = upload_to_s3(final, f"exports/{user_id}/{image_id}.jpg")
    return url
```

### Anti-Patterns to Avoid

- **Processing raw pixels in JS:** Frame Processors should call native plugins, not loop over pixel arrays in JS (1000x slower)
- **Client-side only watermark:** Can be bypassed by decompiling app, use server-side for revenue protection
- **All styles server-side:** Increases server load and latency, users expect instant preview for free styles
- **Skipping progressive enhancement:** 10-20s wait for HD feels broken, show preview immediately
- **Not skipping frames in guidance:** Trying to process every frame at 60 FPS will drop frames anyway, better to process every 2nd frame reliably

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Blur detection algorithm | Custom edge detection, gradient analysis | Laplacian variance (OpenCV) | Single function call, single float output, proven threshold-tunable approach, <5ms |
| Lighting assessment | Complex histogram analysis | Brightness average on 30-pixel sample | Simple mean calculation, <5ms, threshold-based, proven in production |
| Progressive image loading | Custom chunked decoder | react-native-progressive-fast-image | Handles blur transitions, memory management, caching, blur-to-sharp UX |
| ONNX model inference | Manual ONNX parsing and execution | onnxruntime-react-native | Hardware acceleration, cross-platform, 10-15MB binary, battle-tested |
| Stable Diffusion pipeline | Custom diffusion loop | diffusers (Hugging Face) | Scheduler, attention, safety checker, ControlNet support, community-proven |
| Watermarking | Canvas drawing, bitmap manipulation | Pillow (server) + react-native-image-marker (client preview) | Text rendering, alpha blending, positioning, font loading edge cases |
| Style transfer training | Training from scratch | Pre-trained Fast NST models from ONNX Model Zoo | Proven quality, ready-to-deploy, avoid weeks of training |

**Key insight:** Computer vision "simple algorithms" hide edge cases (color spaces, bit depth, EXIF orientation, memory leaks). Use battle-tested libraries to avoid weeks debugging platform-specific issues.

## Common Pitfalls

### Pitfall 1: Frame Processor Performance Overrun

**What goes wrong:** Frame processor takes >33ms at 30 FPS, camera drops frames, UI stutters, guidance feedback lags.

**Why it happens:** ML inference (iris detection) takes 50-100ms, combined with blur/lighting analysis exceeds frame budget.

**How to avoid:**
1. Use native plugins (Swift/Kotlin/C++), not JS processing
2. Skip frames: process every 2nd or 3rd frame instead of every frame
3. Reduce camera resolution to match ML model input size (e.g., 720p instead of 4K)
4. Use TFLite single-task model instead of MediaPipe full face mesh (10x faster for iris-only)

**Warning signs:** Console logs "frame processor took Xms" where X > 33ms, camera preview stuttering, guidance overlay updates lag behind camera movement.

### Pitfall 2: ONNX Model Not Optimized for Mobile

**What goes wrong:** Fast NST model takes 2-5 seconds on mobile instead of 50-200ms, users abandon feature.

**Why it happens:** Model not quantized (FP32 instead of FP16/INT8), wrong input size (1024×1024 instead of 512×512), no XNNPACK acceleration.

**How to avoid:**
1. Convert models to FP16 precision: `python -m onnxruntime.quantization.preprocess --input model.onnx --output model_fp16.onnx`
2. Train/export models at 512×512 resolution for mobile, 1024×1024 for server
3. Enable XNNPACK execution provider in ONNX Runtime config
4. Test on mid-range device (e.g., Galaxy S21, iPhone 12), not flagship

**Warning signs:** >500ms inference time, high CPU usage (>80%), app thermal throttling during style preview.

### Pitfall 3: Real-ESRGAN VRAM Out-of-Memory

**What goes wrong:** Real-ESRGAN task fails with CUDA OOM error during HD upscaling, job marked failed.

**Why it happens:** 4GB VRAM minimum required, other models (segmentation, SDXL) loaded simultaneously, insufficient memory.

**How to avoid:**
1. Use tiling for large images: `RealESRGANer(tile=256, tile_pad=10)`
2. Unload unused models before loading Real-ESRGAN: `ModelCache.clear_segmentation()`
3. Use FP16 precision: `model.half()`
4. Process HD export on dedicated worker with exclusive GPU access

**Warning signs:** "CUDA out of memory" errors in logs, worker restarts mid-task, inconsistent success rate (works sometimes, fails others).

### Pitfall 4: Watermark Easy to Remove Client-Side

**What goes wrong:** Users decompile app, disable watermark overlay, export HD for free.

**Why it happens:** Watermark applied client-side before upload, client has unwatermarked source image.

**How to avoid:**
1. Apply watermark server-side during final export, after payment check
2. Client watermark is overlay only (React Native View), not applied to actual image file
3. Server never returns unwatermarked HD to unpaid users
4. Store HD export as separate S3 object, generate on-demand with payment check

**Warning signs:** Users reporting "I removed the watermark", piracy forums sharing bypass methods, revenue not matching HD export usage.

### Pitfall 5: Burst Capture Fills Device Storage

**What goes wrong:** Burst capture saves 3-5 frames per capture, users take 100+ photos, device runs out of storage.

**Why it happens:** All burst frames saved to disk, best frame selected but others not deleted.

**How to avoid:**
1. Save burst frames to temp cache directory, not permanent storage
2. Delete all burst frames except selected best frame immediately after selection
3. Use `react-native-fs.moveFile()` to move best frame to permanent storage, delete temp directory
4. Set cache expiry (24 hours) for any orphaned burst frames

**Warning signs:** User complaints about storage usage, app storage grows >1GB after 100 captures, temp directory never cleared.

## Code Examples

Verified patterns from official sources:

### Example 1: Frame Processor with Iris Detection (React Native)

```typescript
// src/frameProcessors/irisDetection.ts
import { VisionCameraProxy, Frame } from 'react-native-vision-camera';

interface IrisResult {
  detected: boolean;
  centerX: number;
  centerY: number;
  radius: number;
  distance: number; // cm from camera
  sharpness: number; // 0-1, higher = sharper
}

// Register native plugin (implemented in Swift/Kotlin)
const plugin = VisionCameraProxy.initFrameProcessorPlugin('detectIris');

export function detectIris(frame: Frame): IrisResult | null {
  'worklet';
  if (plugin == null) return null;
  return plugin.call(frame) as IrisResult | null;
}

// src/components/Camera/CameraGuidanceOverlay.tsx
import { useFrameProcessor } from 'react-native-vision-camera';
import { runOnJS } from 'react-native-reanimated';

export default function CameraGuidanceOverlay() {
  const [guidance, setGuidance] = useState({
    irisDetected: false,
    distance: 0,
    focusQuality: 0,
    lightingScore: 0,
  });

  const frameProcessor = useFrameProcessor((frame) => {
    'worklet';
    // Process every 2nd frame to stay within 33ms budget
    if (frame.timestamp % 2 !== 0) return;

    const iris = detectIris(frame);
    const blur = detectBlur(frame);
    const lighting = analyzeLighting(frame);

    runOnJS(setGuidance)({
      irisDetected: iris?.detected ?? false,
      distance: iris?.distance ?? 0,
      focusQuality: blur?.sharpness ?? 0,
      lightingScore: lighting?.brightness ?? 0,
    });
  }, []);

  return (
    <View style={styles.overlay}>
      {guidance.irisDetected ? (
        <Text>✓ Iris detected - Hold still</Text>
      ) : (
        <Text>Move closer to camera</Text>
      )}
      {guidance.focusQuality < 0.5 && <Text>⚠️ Image may be blurry</Text>}
      {guidance.lightingScore < 0.3 && <Text>⚠️ Needs more light</Text>}
      <Camera frameProcessor={frameProcessor} />
    </View>
  );
}
```

**Source:** [Frame Processors | VisionCamera](https://react-native-vision-camera.com/docs/guides/frame-processors)

### Example 2: Laplacian Variance Blur Detection (Native Plugin)

```swift
// ios/FrameProcessors/BlurDetectionPlugin.swift
import VisionCamera
import CoreImage

@objc(BlurDetectionPlugin)
public class BlurDetectionPlugin: FrameProcessorPlugin {
  public override func callback(_ frame: Frame, withArguments arguments: [AnyHashable: Any]?) -> Any? {
    let image = frame.image

    // Convert to grayscale
    let gray = CIImage(cvPixelBuffer: image).applyingFilter("CIColorControls", parameters: [
      "inputSaturation": 0.0
    ])

    // Apply Laplacian kernel
    let laplacian = gray.applyingFilter("CIConvolution9Horizontal", parameters: [
      "inputWeights": CIVector(values: [0, 1, 0, 1, -4, 1, 0, 1, 0], count: 9)
    ])

    // Calculate variance
    let variance = calculateVariance(laplacian)

    return [
      "sharpness": variance,
      "isBlurry": variance < 100.0  // Threshold tunable per device
    ]
  }
}
```

**Source:** [Blur detection with OpenCV - PyImageSearch](https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv/)

### Example 3: On-Device Style Transfer (ONNX)

```typescript
// src/services/onnx.ts
import * as ort from 'onnxruntime-react-native';
import { Image } from 'react-native';
import RNFS from 'react-native-fs';

let cachedSessions: Map<string, ort.InferenceSession> = new Map();

export async function loadStyleModel(styleName: string) {
  if (cachedSessions.has(styleName)) return;

  const modelPath = `${RNFS.MainBundlePath}/models/${styleName}.onnx`;
  const session = await ort.InferenceSession.create(modelPath, {
    executionProviders: ['xnnpack', 'cpu'],  // Try XNNPACK first
  });

  cachedSessions.set(styleName, session);
}

export async function applyStyleOnDevice(
  imageUri: string,
  styleName: string
): Promise<string> {
  await loadStyleModel(styleName);
  const session = cachedSessions.get(styleName)!;

  // Preprocess: resize to 512×512, normalize to [-1, 1], convert to CHW format
  const input = await preprocessImage(imageUri, 512, 512);
  const inputTensor = new ort.Tensor('float32', input, [1, 3, 512, 512]);

  // Inference (50-200ms on mobile CPU)
  const results = await session.run({ input: inputTensor });
  const outputTensor = results.output as ort.Tensor;

  // Postprocess: denormalize, CHW to HWC, save as JPEG
  return postprocessToUri(outputTensor);
}
```

**Source:** [React Native | onnxruntime](https://onnxruntime.ai/docs/get-started/with-javascript/react-native.html)

### Example 4: SDXL Turbo for Fast AI Generation (Backend)

```python
# backend/app/workers/models/sd_generator.py
from diffusers import AutoPipelineForImage2Image, ControlNetModel
import torch
from PIL import Image

class SDXLTurboGenerator:
    def __init__(self):
        self.pipeline = None
        self.controlnet = None

    def load(self):
        # Load SDXL Turbo pipeline
        self.pipeline = AutoPipelineForImage2Image.from_pretrained(
            "stabilityai/sdxl-turbo",
            torch_dtype=torch.float16,
            variant="fp16"
        ).to("cuda")

        # Enable xformers for faster attention
        self.pipeline.enable_xformers_memory_efficient_attention()

        # Load ControlNet for edge guidance
        self.controlnet = ControlNetModel.from_pretrained(
            "diffusers/controlnet-canny-sdxl-1.0",
            torch_dtype=torch.float16
        ).to("cuda")

    def generate(self, iris_image: Image.Image, prompt: str, num_steps: int = 4):
        # Extract edges from iris for composition control
        edges = extract_canny_edges(iris_image)

        # Generate with ControlNet guidance (1-4 steps)
        result = self.pipeline(
            prompt=prompt,
            image=iris_image,
            control_image=edges,
            num_inference_steps=num_steps,
            guidance_scale=0.0,  # Turbo doesn't need guidance
            strength=0.8,  # How much to transform input
        ).images[0]

        return result

# backend/app/workers/tasks/ai_generation.py
from app.workers.celery_app import celery_app
from app.workers.models.model_cache import ModelCache

@celery_app.task(bind=True, queue='high_priority')
def generate_ai_art(self, user_id: int, iris_image_id: int, prompt: str):
    generator = ModelCache.get_sd_generator()

    # Load iris image from S3
    iris_image = load_from_s3(iris_image_id)

    # Generate unique composition (1-4 steps, <200ms on consumer GPU)
    result = generator.generate(
        iris_image=iris_image,
        prompt=prompt,
        num_steps=4
    )

    # Save result to S3
    result_url = upload_to_s3(result, f"ai_art/{user_id}/{iris_image_id}.jpg")
    return result_url
```

**Source:** [SDXL Turbo | Hugging Face](https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/sdxl_turbo)

### Example 5: Progressive Enhancement with Streaming

```python
# backend/app/services/progressive_export.py
from fastapi.responses import StreamingResponse
import io
from PIL import Image

async def generate_progressive_hd_export(
    user_id: int,
    image_id: int,
    style_id: int
):
    # 1. Generate low-res preview (256×256, ~1-2s)
    preview = await generate_styled_preview(image_id, style_id, size=256)
    preview_bytes = io.BytesIO()
    preview.save(preview_bytes, format="JPEG", quality=70)
    yield preview_bytes.getvalue()

    # 2. Generate HD (2048×2048, ~10-20s with Real-ESRGAN)
    hd = await generate_styled_hd(image_id, style_id, size=2048)

    # 3. Apply watermark if not paid
    is_paid = await check_hd_export_purchased(user_id, image_id)
    final = apply_watermark(hd, is_paid=is_paid)

    # 4. Stream HD progressively (chunks sent as encoded)
    hd_bytes = io.BytesIO()
    final.save(hd_bytes, format="JPEG", quality=95, progressive=True)
    yield hd_bytes.getvalue()

# backend/app/api/routes/exports.py
from fastapi import APIRouter, Depends
from app.services.progressive_export import generate_progressive_hd_export

router = APIRouter()

@router.get("/exports/{image_id}/hd")
async def export_hd_image(
    image_id: int,
    style_id: int,
    user_id: int = Depends(get_current_user_id)
):
    return StreamingResponse(
        generate_progressive_hd_export(user_id, image_id, style_id),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked"
        }
    )
```

**Source:** [FastAPI Streaming Response](https://medium.com/@ab.hassanein/streaming-responses-in-fastapi-d6a3397a4b7b)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MediaPipe JS (TensorFlow.js) | MediaPipe native OR TFLite custom | 2024-2025 | Native 10-100x faster, JS suitable for web only |
| Stable Diffusion 1.5 (50 steps) | SDXL Turbo (1-4 steps) | Nov 2023 | 95% faster inference (<200ms), 98% visual fidelity maintained |
| PyTorch Mobile | ONNX Runtime Mobile | 2023-2024 | Smaller binary (10-15MB vs 25-30MB), better cross-platform tooling |
| Client-side watermark only | Server-side watermark enforcement | Industry standard | Revenue protection, prevents bypass via decompilation |
| Real-ESRGAN (original) | Real-ESRGAN with tiling + FP16 | 2024-2025 | 50% memory reduction, 30% speed improvement, handles 4K+ images |

**Deprecated/outdated:**
- **react-native-camera**: Deprecated in favor of react-native-vision-camera (5x faster frame processors, better Android support)
- **TensorFlow Lite React Native community library**: Unmaintained, use react-native-fast-tflite (actively maintained by mrousavy)
- **Stable Diffusion WebUI API for mobile**: Too slow (10-30s), use SDXL Turbo API with FastAPI backend

## Open Questions

### 1. TFLite Iris Detection Model Availability

**What we know:** MediaPipe provides full face mesh (478 landmarks), but for iris-only detection a lightweight TFLite model would be faster.

**What's unclear:** Are pre-trained iris detection TFLite models publicly available? Or do we need to train one from scratch?

**Recommendation:** Start with MediaPipe Face Mesh (proven, ready to use), extract iris landmarks only (indices 469-477). If performance inadequate (<30ms), explore training custom TFLite iris detector using MediaPipe's training pipeline and iris datasets (e.g., University of Notre Dame iris dataset).

**Confidence:** MEDIUM - MediaPipe works but may be overkill, custom TFLite is optimal but requires more effort.

### 2. Fast NST Model Quality vs File Size Tradeoff

**What we know:** Fast NST models range 5-50MB depending on architecture. Smaller models faster but lower quality.

**What's unclear:** What's the optimal model size for mobile app bundle? How many free styles can we ship before app size becomes prohibitive?

**Recommendation:** Ship 5 free styles at 8-10MB each (~50MB total), download additional styles on-demand (user selects "Download Style Pack" button). Premium styles server-only (no download).

**Confidence:** MEDIUM - App size limits vary by user tolerance and region (emerging markets more sensitive), on-demand download is safer.

### 3. SDXL Turbo vs SDXL 1.0 Quality Perception

**What we know:** SDXL Turbo achieves 98% visual fidelity vs SDXL 1.0 in benchmarks.

**What's unclear:** For artistic iris compositions, is 2% quality loss noticeable to users? Would they pay for SDXL 1.0 (10-30s) over Turbo (<1s)?

**Recommendation:** Launch with SDXL Turbo for all AI-generated art (speed is wow factor). If user feedback indicates quality concerns, offer "Ultra HD" tier with SDXL 1.0 at higher price point (e.g., 7.99 EUR vs 4.99 EUR).

**Confidence:** MEDIUM - Benchmark fidelity doesn't always match user perception, need real-world feedback.

### 4. ControlNet Preprocessing for Iris Edges

**What we know:** ControlNet uses Canny edge detection to guide composition. Iris has circular structure with radial patterns.

**What's unclear:** Does standard Canny work well for iris edges, or do we need custom preprocessing (e.g., emphasize radial patterns, suppress reflections)?

**Recommendation:** Start with standard Canny edge detection from `controlnet_aux`. If results lack iris-specific artistic coherence, implement custom edge extractor emphasizing radial patterns using OpenCV polar transforms.

**Confidence:** LOW - Iris structure is unique, may need experimentation. Canny is baseline, custom processing is Plan B.

## Sources

### Primary (HIGH confidence)

- [Frame Processors | VisionCamera](https://react-native-vision-camera.com/docs/guides/frame-processors) - Frame processor architecture, performance metrics (1ms overhead vs native), worklets integration
- [ONNX Runtime React Native](https://onnxruntime.ai/docs/get-started/with-javascript/react-native.html) - Installation, configuration, execution providers
- [SDXL Turbo | Hugging Face](https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/sdxl_turbo) - API, performance characteristics (1-4 steps, <200ms)
- [Blur detection with OpenCV - PyImageSearch](https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv/) - Laplacian variance algorithm, thresholds, implementation
- [FastAPI Streaming Response](https://medium.com/@ab.hassanein/streaming-responses-in-fastapi-d6a3397a4b7b) - StreamingResponse patterns, chunked transfer encoding
- [MediaPipe Face Mesh iris landmarks](https://github.com/google/mediapipe/blob/master/docs/solutions/iris.md) - 478 landmarks including 10 iris points, output format
- [Design and experimental research of on device style transfer models for mobile environments](https://www.nature.com/articles/s41598-025-98545-4) - Mobile NST optimization, real-time 512×512 inference, model size vs quality

### Secondary (MEDIUM confidence)

- [High-performance hand landmark detection in React Native using Vision Camera and Skia frame processor](https://medium.com/@lukasz.kurant/high-performance-hand-landmark-detection-in-react-native-using-vision-camera-and-skia-frame-9ddec89362bc) - Frame processor plugin architecture patterns
- [Deploy any machine learning model for real-time frame processing with React Native Vision Camera and ONNX Runtime](https://medium.com/technoid-community/deploy-any-machine-learning-model-for-real-time-frame-processing-with-react-native-vision-camera-571fbf2948d1) - ONNX integration with Vision Camera
- [Real-ESRGAN aims at developing Practical Algorithms for General Image/Video Restoration](https://github.com/xinntao/Real-ESRGAN) - Model variants, VRAM requirements (4GB), tiling strategies
- [Fastest ESRGAN Upscaling Models - Quality Comparison 2025](https://apatero.com/blog/fastest-esrgan-upscaling-models-quality-comparison-2025) - Performance benchmarks (6s for 512→2048 on RTX 4090)
- [react-native-image-marker](https://github.com/JimmyDaddy/react-native-image-marker) - Watermark API, native performance for text/image overlays
- [Lighting detection camera image quality React Native](https://medium.com/@dv21578/to-efficiently-detect-if-an-image-taken-by-the-camera-is-too-dark-on-the-device-without-sending-ae12f59ff7dd) - Brightness calculation, 30-pixel sampling approach

### Tertiary (LOW confidence - needs validation)

- [TensorFlow Lite React Native integration 2026](https://github.com/mrousavy/react-native-fast-tflite) - Active maintenance status, GPU acceleration claims (need performance benchmarks)
- [SDXL Turbo inference <200ms](https://johal.in/fastapi-fooocus-distill-sdxl-turbo-inference-2026-2/) - 200ms claim on consumer GPU (need to verify hardware specs, optimization techniques)
- [Progressive image loading React Native libraries](https://github.com/DylanVann/react-native-progressive-image) - Maintenance status unclear, need to verify active development

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries proven in production, ONNX Runtime and Vision Camera are industry standard
- Architecture patterns: HIGH - Frame processors documented by Vision Camera team, SDXL/Real-ESRGAN patterns from official Hugging Face docs
- Pitfalls: HIGH - Performance overruns, VRAM OOM, watermark bypass are well-documented production issues
- On-device models: MEDIUM - Fast NST mobile performance is research-backed but app-specific tuning needed
- AI-generated art: MEDIUM - SDXL Turbo performance proven but iris-specific ControlNet preprocessing is unverified

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (30 days - ML ecosystem moves fast but core libraries stable)
