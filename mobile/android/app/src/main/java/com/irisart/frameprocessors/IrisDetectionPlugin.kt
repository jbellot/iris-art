package com.irisart.frameprocessors

import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.face.FaceDetection
import com.google.mlkit.vision.face.FaceDetectorOptions
import com.mrousavy.camera.core.types.Orientation
import com.mrousavy.camera.frameprocessors.Frame
import com.mrousavy.camera.frameprocessors.FrameProcessorPlugin
import com.mrousavy.camera.frameprocessors.VisionCameraProxy

class IrisDetectionPlugin(proxy: VisionCameraProxy, options: Map<String, Any>?) : FrameProcessorPlugin() {

  private val faceDetector = FaceDetection.getClient(
    FaceDetectorOptions.Builder()
      .setLandmarkMode(FaceDetectorOptions.LANDMARK_MODE_ALL)
      .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_FAST)
      .build()
  )

  override fun callback(frame: Frame, arguments: Map<String, Any>?): Any {
    val mediaImage = frame.image
    val rotationDegrees = when (frame.orientation) {
      Orientation.PORTRAIT -> 0
      Orientation.LANDSCAPE_RIGHT -> 90
      Orientation.PORTRAIT_UPSIDE_DOWN -> 180
      Orientation.LANDSCAPE_LEFT -> 270
    }
    val inputImage = InputImage.fromMediaImage(mediaImage, rotationDegrees)

    var result = mapOf(
      "detected" to false,
      "centerX" to 0.0f,
      "centerY" to 0.0f,
      "radius" to 0.0f,
      "distance" to 0.0f
    )

    try {
      // Synchronous processing for frame processor
      val task = faceDetector.process(inputImage)
      while (!task.isComplete) {
        Thread.sleep(1) // Wait for completion (blocking is OK in frame processor)
      }

      if (task.isSuccessful) {
        val faces = task.result
        if (faces.isNotEmpty()) {
          val face = faces[0]
          val leftEye = face.getLandmark(com.google.mlkit.vision.face.FaceLandmark.LEFT_EYE)
          val rightEye = face.getLandmark(com.google.mlkit.vision.face.FaceLandmark.RIGHT_EYE)

          if (leftEye != null && rightEye != null) {
            // Calculate iris center as midpoint between eyes
            val irisCenterX = (leftEye.position.x + rightEye.position.x) / 2.0f
            val irisCenterY = (leftEye.position.y + rightEye.position.y) / 2.0f

            // Normalize to 0-1 range
            val frameWidth = frame.width.toFloat()
            val frameHeight = frame.height.toFloat()
            val normalizedX = irisCenterX / frameWidth
            val normalizedY = irisCenterY / frameHeight

            // Calculate iris radius from eye distance
            val eyeDistance = kotlin.math.sqrt(
              (rightEye.position.x - leftEye.position.x).let { it * it } +
              (rightEye.position.y - leftEye.position.y).let { it * it }
            )
            val normalizedRadius = eyeDistance / frameWidth / 4.0f

            // Estimate distance based on face bounding box size
            val faceBounds = face.boundingBox
            val faceWidth = faceBounds.width().toFloat() / frameWidth

            val distance = when {
              faceWidth < 0.25f -> (faceWidth / 0.25f) * 0.5f
              faceWidth > 0.55f -> 0.5f + ((faceWidth - 0.55f) / 0.45f) * 0.5f
              else -> 0.5f
            }

            result = mapOf(
              "detected" to true,
              "centerX" to normalizedX,
              "centerY" to normalizedY,
              "radius" to normalizedRadius,
              "distance" to distance
            )
          }
        }
      }
    } catch (e: Exception) {
      // Return default result on error
    }

    return result
  }
}
