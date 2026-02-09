import Foundation
import CoreImage
import Accelerate
import VisionCamera

@objc(BlurDetectionPlugin)
public class BlurDetectionPlugin: FrameProcessorPlugin {
  private let context = CIContext()

  public override init(proxy: VisionCameraProxyHolder, options: [AnyHashable: Any]! = [:]) {
    super.init(proxy: proxy, options: options)
  }

  public override func callback(_ frame: Frame, withArguments arguments: [AnyHashable: Any]?) -> Any? {
    let image = frame.image
    let imageBuffer = CMSampleBufferGetImageBuffer(image)

    guard let pixelBuffer = imageBuffer else {
      return [
        "sharpness": 0.0,
        "isBlurry": true
      ]
    }

    // Convert to CIImage
    let ciImage = CIImage(cvPixelBuffer: pixelBuffer)

    // Convert to grayscale
    guard let grayscaleFilter = CIFilter(name: "CIColorControls") else {
      return [
        "sharpness": 0.0,
        "isBlurry": true
      ]
    }
    grayscaleFilter.setValue(ciImage, forKey: kCIInputImageKey)
    grayscaleFilter.setValue(0.0, forKey: kCIInputSaturationKey)

    guard let grayscaleImage = grayscaleFilter.outputImage else {
      return [
        "sharpness": 0.0,
        "isBlurry": true
      ]
    }

    // Apply Laplacian kernel using CIConvolution3X3
    guard let convolutionFilter = CIFilter(name: "CIConvolution3X3") else {
      return [
        "sharpness": 0.0,
        "isBlurry": true
      ]
    }

    // Laplacian kernel: [0, 1, 0, 1, -4, 1, 0, 1, 0]
    let laplacianKernel = CIVector(values: [
      0, 1, 0,
      1, -4, 1,
      0, 1, 0
    ], count: 9)

    convolutionFilter.setValue(grayscaleImage, forKey: kCIInputImageKey)
    convolutionFilter.setValue(laplacianKernel, forKey: "inputWeights")

    guard let outputImage = convolutionFilter.outputImage else {
      return [
        "sharpness": 0.0,
        "isBlurry": true
      ]
    }

    // Render to bitmap for variance calculation
    let extent = outputImage.extent
    let width = Int(extent.width)
    let height = Int(extent.height)

    // Sample a smaller region for performance (center 1/9 of image)
    let sampleWidth = width / 3
    let sampleHeight = height / 3
    let sampleX = width / 3
    let sampleY = height / 3
    let sampleRect = CGRect(x: sampleX, y: sampleY, width: sampleWidth, height: sampleHeight)

    var bitmap = [UInt8](repeating: 0, count: sampleWidth * sampleHeight)
    context.render(outputImage, toBitmap: &bitmap, rowBytes: sampleWidth, bounds: sampleRect, format: .L8, colorSpace: CGColorSpaceCreateDeviceGray())

    // Calculate variance
    let sharpness = calculateVariance(bitmap: bitmap)
    let isBlurry = sharpness < 100.0

    return [
      "sharpness": Float(sharpness),
      "isBlurry": isBlurry
    ]
  }

  private func calculateVariance(bitmap: [UInt8]) -> Double {
    guard !bitmap.isEmpty else { return 0.0 }

    // Calculate mean
    let sum = bitmap.reduce(0.0) { $0 + Double($1) }
    let mean = sum / Double(bitmap.count)

    // Calculate variance
    let variance = bitmap.reduce(0.0) { $0 + pow(Double($1) - mean, 2) }
    return variance / Double(bitmap.count)
  }
}
