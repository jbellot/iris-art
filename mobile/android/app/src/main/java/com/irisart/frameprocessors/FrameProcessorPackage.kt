package com.irisart.frameprocessors

import com.mrousavy.camera.frameprocessors.FrameProcessorPlugin
import com.mrousavy.camera.frameprocessors.FrameProcessorPluginRegistry

class FrameProcessorPackage {
  companion object {
    init {
      FrameProcessorPluginRegistry.addFrameProcessorPlugin("detectIris") { proxy, options ->
        IrisDetectionPlugin(proxy, options)
      }
      FrameProcessorPluginRegistry.addFrameProcessorPlugin("detectBlur") { proxy, options ->
        BlurDetectionPlugin(proxy, options)
      }
      FrameProcessorPluginRegistry.addFrameProcessorPlugin("analyzeLighting") { proxy, options ->
        LightingAnalysisPlugin(proxy, options)
      }
    }
  }
}
