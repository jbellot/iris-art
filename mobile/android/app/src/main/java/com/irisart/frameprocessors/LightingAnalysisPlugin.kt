package com.irisart.frameprocessors

import com.mrousavy.camera.frameprocessors.Frame
import com.mrousavy.camera.frameprocessors.FrameProcessorPlugin
import com.mrousavy.camera.frameprocessors.VisionCameraProxy
import kotlin.random.Random

class LightingAnalysisPlugin(proxy: VisionCameraProxy, options: Map<String, Any>?) : FrameProcessorPlugin() {

  override fun callback(frame: Frame, arguments: Map<String, Any>?): Any {
    val image = frame.image

    // Get Y plane (luminance) from YUV image
    val yPlane = image.planes[0]
    val yBuffer = yPlane.buffer
    val yRowStride = yPlane.rowStride
    val yPixelStride = yPlane.pixelStride

    val width = image.width
    val height = image.height

    // Sample 30 pixels from center region
    val centerX = width / 2
    val centerY = height / 2
    val sampleRadius = 50

    var brightnessSum = 0.0
    var sampleCount = 0

    repeat(30) {
      val x = centerX + Random.nextInt(-sampleRadius, sampleRadius + 1)
      val y = centerY + Random.nextInt(-sampleRadius, sampleRadius + 1)

      if (x in 0 until width && y in 0 until height) {
        val index = y * yRowStride + x * yPixelStride
        val luminance = (yBuffer.get(index).toInt() and 0xFF) / 255.0
        brightnessSum += luminance
        sampleCount++
      }
    }

    val avgBrightness = if (sampleCount > 0) {
      brightnessSum / sampleCount
    } else {
      0.0
    }

    val status = when {
      avgBrightness < 0.25 -> "too_dark"
      avgBrightness > 0.85 -> "too_bright"
      else -> "good"
    }

    return mapOf(
      "brightness" to avgBrightness.toFloat(),
      "status" to status
    )
  }
}
