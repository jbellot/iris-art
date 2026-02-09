"""Reflection removal model wrapper using OpenCV inpainting (MVP)."""

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def remove_reflections(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Remove specular reflections from iris image.

    For MVP: Uses OpenCV inpainting on detected highlights.
    Future: Can be replaced with LapCAT transformer model.

    Args:
        image: Input image (H, W, 3)
        mask: Iris segmentation mask (H, W)

    Returns:
        Image with reflections removed (H, W, 3)
    """
    # Convert to grayscale to detect highlights
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect specular highlights within the mask region (bright pixels > 240)
    highlights = np.zeros_like(mask)
    highlights[(gray > 240) & (mask > 0)] = 255

    # Check if any highlights detected
    if np.sum(highlights) == 0:
        logger.debug("No highlights detected - returning original image")
        return image

    # Apply morphological operations to expand highlight regions slightly
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    inpaint_mask = cv2.dilate(highlights, kernel, iterations=1)

    # Apply inpainting with TELEA method
    result = cv2.inpaint(image, inpaint_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    logger.debug(f"Removed reflections from {np.sum(inpaint_mask > 0)} pixels")

    return result
