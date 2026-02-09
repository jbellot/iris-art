package com.irisart.frameprocessors

import android.graphics.ImageFormat
import com.mrousavy.camera.frameprocessors.Frame
import com.mrousavy.camera.frameprocessors.FrameProcessorPlugin
import com.mrousavy.camera.frameprocessors.VisionCameraProxy
import java.nio.ByteBuffer
import kotlin.math.pow

class BlurDetectionPlugin(proxy: VisionCameraProxy, options: Map<String, Any>?) : FrameProcessorPlugin() {

  override fun callback(frame: Frame, arguments: Map<String, Any>?): Any {
    val image = frame.image

    // Get Y plane (luminance) from YUV image
    val yPlane = image.planes[0]
    val yBuffer = yPlane.buffer
    val yRowStride = yPlane.rowStride
    val yPixelStride = yPlane.pixelStride

    val width = image.width
    val height = image.height

    // Sample center region for blur detection (1/3 of image)
    val sampleWidth = width / 3
    val sampleHeight = height / 3
    val startX = width / 3
    val startY = height / 3

    // Apply Laplacian kernel to detect edges
    val laplacianValues = mutableListOf<Double>()

    for (y in startY until (startY + sampleHeight - 2) step 2) {
      for (x in startX until (startX + sampleWidth - 2) step 2) {
        // Get 3x3 neighborhood
        val values = Array(3) { IntArray(3) }
        for (dy in 0..2) {
          for (dx in 0..2) {
            val pixelY = y + dy
            val pixelX = x + dx
            val index = pixelY * yRowStride + pixelX * yPixelStride
            values[dy][dx] = yBuffer.get(index).toInt() and 0xFF
          }
        }

        // Apply Laplacian kernel: [0, 1, 0, 1, -4, 1, 0, 1, 0]
        val laplacian = (
          values[0][1] +
          values[1][0] +
          values[1][2] +
          values[2][1] -
          4 * values[1][1]
        ).toDouble()

        laplacianValues.add(laplacian)
      }
    }

    // Calculate variance of Laplacian
    val sharpness = if (laplacianValues.isNotEmpty()) {
      val mean = laplacianValues.average()
      val variance = laplacianValues.map { (it - mean).pow(2) }.average()
      variance
    } else {
      0.0
    }

    val isBlurry = sharpness < 100.0

    return mapOf(
      "sharpness" to sharpness.toFloat(),
      "isBlurry" to isBlurry
    )
  }
}
