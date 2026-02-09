#import <Foundation/Foundation.h>
#import <VisionCamera/FrameProcessorPlugin.h>
#import <VisionCamera/FrameProcessorPluginRegistry.h>

@interface IrisDetectionPlugin : FrameProcessorPlugin
@end

VISION_EXPORT_FRAME_PROCESSOR(IrisDetectionPlugin, detectIris)
