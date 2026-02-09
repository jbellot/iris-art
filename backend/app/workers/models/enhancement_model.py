"""Image enhancement model wrapper with OpenCV fallback."""

import logging

import cv2
import numpy as np

from app.workers.models.model_cache import ModelCache

logger = logging.getLogger(__name__)


def enhance_iris(image: np.ndarray, scale: int = 4) -> np.ndarray:
    """Enhance iris image with super-resolution.

    Args:
        image: Input image (H, W, 3)
        scale: Upscaling factor (default: 4x)

    Returns:
        Enhanced image (H*scale, W*scale, 3)
    """
    # Apply CLAHE for contrast enhancement before upscaling
    image_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(image_lab)

    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel_enhanced = clahe.apply(l_channel)

    # Merge channels back
    image_enhanced = cv2.merge([l_channel_enhanced, a_channel, b_channel])
    image_enhanced = cv2.cvtColor(image_enhanced, cv2.COLOR_LAB2BGR)

    # Try to get Real-ESRGAN model
    model = ModelCache.get_enhancement_model()

    if model is not None:
        # Use Real-ESRGAN for super-resolution
        logger.info("Using Real-ESRGAN for enhancement")
        # Real-ESRGAN enhancement would go here
        # For now, fall through to OpenCV
        pass

    # Fallback: Use OpenCV with Lanczos interpolation
    logger.info(f"Using OpenCV Lanczos {scale}x upscaling (dev mode)")
    height, width = image_enhanced.shape[:2]
    new_height, new_width = height * scale, width * scale

    result = cv2.resize(
        image_enhanced,
        (new_width, new_height),
        interpolation=cv2.INTER_LANCZOS4
    )

    return result
