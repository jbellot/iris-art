#import <Foundation/Foundation.h>
#import <VisionCamera/FrameProcessorPlugin.h>
#import <VisionCamera/FrameProcessorPluginRegistry.h>

@interface LightingAnalysisPlugin : FrameProcessorPlugin
@end

VISION_EXPORT_FRAME_PROCESSOR(LightingAnalysisPlugin, analyzeLighting)
