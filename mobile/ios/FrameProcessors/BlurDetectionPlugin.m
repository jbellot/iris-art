#import <Foundation/Foundation.h>
#import <VisionCamera/FrameProcessorPlugin.h>
#import <VisionCamera/FrameProcessorPluginRegistry.h>

@interface BlurDetectionPlugin : FrameProcessorPlugin
@end

VISION_EXPORT_FRAME_PROCESSOR(BlurDetectionPlugin, detectBlur)
