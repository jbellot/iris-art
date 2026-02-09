import Foundation
import Vision
import VisionCamera

@objc(IrisDetectionPlugin)
public class IrisDetectionPlugin: FrameProcessorPlugin {
  public override init(proxy: VisionCameraProxyHolder, options: [AnyHashable: Any]! = [:]) {
    super.init(proxy: proxy, options: options)
  }

  public override func callback(_ frame: Frame, withArguments arguments: [AnyHashable: Any]?) -> Any? {
    let image = frame.image
    let imageBuffer = CMSampleBufferGetImageBuffer(image)

    guard let pixelBuffer = imageBuffer else {
      return [
        "detected": false,
        "centerX": 0.0,
        "centerY": 0.0,
        "radius": 0.0,
        "distance": 0.0
      ]
    }

    // Create Vision request for face landmarks
    let faceDetectionRequest = VNDetectFaceLandmarksRequest()
    faceDetectionRequest.revision = VNDetectFaceLandmarksRequestRevision3

    let requestHandler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer, orientation: .up, options: [:])

    do {
      try requestHandler.perform([faceDetectionRequest])

      guard let observations = faceDetectionRequest.results,
            let face = observations.first,
            let landmarks = face.landmarks,
            let leftEye = landmarks.leftEye,
            let rightEye = landmarks.rightEye else {
        return [
          "detected": false,
          "centerX": 0.0,
          "centerY": 0.0,
          "radius": 0.0,
          "distance": 0.0
        ]
      }

      // Get normalized eye points
      let leftEyePoints = leftEye.normalizedPoints
      let rightEyePoints = rightEye.normalizedPoints

      // Calculate eye centers
      let leftEyeCenter = calculateCenter(points: leftEyePoints)
      let rightEyeCenter = calculateCenter(points: rightEyePoints)

      // Calculate iris center as midpoint between eyes
      let irisCenterX = (leftEyeCenter.x + rightEyeCenter.x) / 2.0
      let irisCenterY = (leftEyeCenter.y + rightEyeCenter.y) / 2.0

      // Calculate iris radius from eye region bounds
      let leftEyeBounds = calculateBounds(points: leftEyePoints)
      let rightEyeBounds = calculateBounds(points: rightEyePoints)
      let avgEyeWidth = (leftEyeBounds.width + rightEyeBounds.width) / 2.0
      let irisRadius = avgEyeWidth / 2.0

      // Estimate distance based on face size
      // Larger face = closer, smaller face = farther
      // face.boundingBox.width is normalized (0-1)
      // Typical values: 0.15 = far, 0.4 = ideal, 0.7+ = too close
      let faceWidth = face.boundingBox.width
      let distance: Float
      if faceWidth < 0.25 {
        distance = Float(faceWidth / 0.25) * 0.5 // Map 0-0.25 to 0-0.5
      } else if faceWidth > 0.55 {
        distance = 0.5 + Float((faceWidth - 0.55) / 0.45) * 0.5 // Map 0.55-1.0 to 0.5-1.0
      } else {
        distance = 0.5 // Ideal range
      }

      return [
        "detected": true,
        "centerX": Float(irisCenterX),
        "centerY": Float(irisCenterY),
        "radius": Float(irisRadius),
        "distance": distance
      ]

    } catch {
      return [
        "detected": false,
        "centerX": 0.0,
        "centerY": 0.0,
        "radius": 0.0,
        "distance": 0.0
      ]
    }
  }

  private func calculateCenter(points: [CGPoint]) -> CGPoint {
    let sum = points.reduce(CGPoint.zero) { CGPoint(x: $0.x + $1.x, y: $0.y + $1.y) }
    let count = CGFloat(points.count)
    return CGPoint(x: sum.x / count, y: sum.y / count)
  }

  private func calculateBounds(points: [CGPoint]) -> CGRect {
    guard !points.isEmpty else { return .zero }

    var minX = points[0].x
    var maxX = points[0].x
    var minY = points[0].y
    var maxY = points[0].y

    for point in points {
      minX = min(minX, point.x)
      maxX = max(maxX, point.x)
      minY = min(minY, point.y)
      maxY = max(maxY, point.y)
    }

    return CGRect(x: minX, y: minY, width: maxX - minX, height: maxY - minY)
  }
}
