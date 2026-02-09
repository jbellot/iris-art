import Foundation
import CoreVideo
import VisionCamera

@objc(LightingAnalysisPlugin)
public class LightingAnalysisPlugin: FrameProcessorPlugin {
  public override init(proxy: VisionCameraProxyHolder, options: [AnyHashable: Any]! = [:]) {
    super.init(proxy: proxy, options: options)
  }

  public override func callback(_ frame: Frame, withArguments arguments: [AnyHashable: Any]?) -> Any? {
    let image = frame.image
    let imageBuffer = CMSampleBufferGetImageBuffer(image)

    guard let pixelBuffer = imageBuffer else {
      return [
        "brightness": 0.0,
        "status": "too_dark"
      ]
    }

    CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
    defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }

    let width = CVPixelBufferGetWidth(pixelBuffer)
    let height = CVPixelBufferGetHeight(pixelBuffer)
    let bytesPerRow = CVPixelBufferGetBytesPerRow(pixelBuffer)

    guard let baseAddress = CVPixelBufferGetBaseAddress(pixelBuffer) else {
      return [
        "brightness": 0.0,
        "status": "too_dark"
      ]
    }

    // Sample 30 pixels from center region
    let centerX = width / 2
    let centerY = height / 2
    let sampleRadius = 50

    var brightnessSum = 0.0
    var sampleCount = 0

    let pixelFormat = CVPixelBufferGetPixelFormatType(pixelBuffer)

    // Handle different pixel formats
    if pixelFormat == kCVPixelFormatType_32BGRA {
      // BGRA format - common on iOS
      let buffer = baseAddress.assumingMemoryBound(to: UInt8.self)

      for _ in 0..<30 {
        // Random sample within center region
        let x = centerX + Int.random(in: -sampleRadius...sampleRadius)
        let y = centerY + Int.random(in: -sampleRadius...sampleRadius)

        guard x >= 0 && x < width && y >= 0 && y < height else { continue }

        let pixelIndex = y * bytesPerRow + x * 4
        let b = Double(buffer[pixelIndex])
        let g = Double(buffer[pixelIndex + 1])
        let r = Double(buffer[pixelIndex + 2])

        // Calculate luminance: Y = 0.299*R + 0.587*G + 0.114*B
        let luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        brightnessSum += luminance
        sampleCount += 1
      }
    } else if pixelFormat == kCVPixelFormatType_420YpCbCr8BiPlanarFullRange ||
              pixelFormat == kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange {
      // YUV format - Y plane is luminance
      let buffer = baseAddress.assumingMemoryBound(to: UInt8.self)

      for _ in 0..<30 {
        let x = centerX + Int.random(in: -sampleRadius...sampleRadius)
        let y = centerY + Int.random(in: -sampleRadius...sampleRadius)

        guard x >= 0 && x < width && y >= 0 && y < height else { continue }

        let pixelIndex = y * bytesPerRow + x
        let luminance = Double(buffer[pixelIndex]) / 255.0
        brightnessSum += luminance
        sampleCount += 1
      }
    }

    guard sampleCount > 0 else {
      return [
        "brightness": 0.0,
        "status": "too_dark"
      ]
    }

    let avgBrightness = brightnessSum / Double(sampleCount)

    let status: String
    if avgBrightness < 0.25 {
      status = "too_dark"
    } else if avgBrightness > 0.85 {
      status = "too_bright"
    } else {
      status = "good"
    }

    return [
      "brightness": Float(avgBrightness),
      "status": status
    ]
  }
}
