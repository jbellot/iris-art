"""Iris segmentation model wrapper with dev mode fallback."""

import logging
from typing import Tuple

import cv2
import numpy as np

from app.workers.models.model_cache import ModelCache

logger = logging.getLogger(__name__)


def segment_iris(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Segment iris from eye image.

    Args:
        image: Input image as numpy array (H, W, 3)

    Returns:
        Tuple of (segmented_image, binary_mask)

    Raises:
        ValueError: If iris not detected clearly (mask too small)
    """
    model = ModelCache.get_segmentation_model()

    if model is not None:
        # Use ONNX model for real segmentation
        mask = _segment_with_onnx(image, model)
    else:
        # Dev mode: create simulated circular mask
        logger.info("Using simulated segmentation (dev mode)")
        mask = _create_simulated_mask(image)

    # Validate mask coverage
    mask_area = np.sum(mask > 0)
    total_area = mask.shape[0] * mask.shape[1]
    coverage = mask_area / total_area

    if coverage < 0.05:  # Less than 5% coverage
        raise ValueError("Iris not detected clearly - mask coverage too small")

    # Apply mask to image
    segmented_image = cv2.bitwise_and(image, image, mask=mask)

    return segmented_image, mask


def _segment_with_onnx(image: np.ndarray, model) -> np.ndarray:
    """Run ONNX segmentation model.

    Args:
        image: Input image (H, W, 3)
        model: ONNX InferenceSession

    Returns:
        Binary mask (H, W) uint8
    """
    original_height, original_width = image.shape[:2]

    # Resize to model input size (512x512)
    resized = cv2.resize(image, (512, 512), interpolation=cv2.INTER_AREA)

    # Normalize to [0, 1]
    normalized = resized.astype(np.float32) / 255.0

    # Add batch dimension and transpose to NCHW format
    input_tensor = np.transpose(normalized, (2, 0, 1))
    input_tensor = np.expand_dims(input_tensor, axis=0)

    # Run inference
    input_name = model.get_inputs()[0].name
    output_name = model.get_outputs()[0].name
    outputs = model.run([output_name], {input_name: input_tensor})

    # Get mask and threshold at 0.5
    mask_output = outputs[0][0, 0]  # Remove batch and channel dims
    mask_binary = (mask_output > 0.5).astype(np.uint8) * 255

    # Resize mask back to original dimensions
    mask_resized = cv2.resize(mask_binary, (original_width, original_height), interpolation=cv2.INTER_NEAREST)

    return mask_resized


def _create_simulated_mask(image: np.ndarray) -> np.ndarray:
    """Create simulated circular iris mask for dev testing.

    Args:
        image: Input image (H, W, 3)

    Returns:
        Binary mask (H, W) uint8
    """
    height, width = image.shape[:2]

    # Create circular mask centered on image
    center_y, center_x = height // 2, width // 2
    radius = min(height, width) // 3  # About 1/3 of image size

    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.circle(mask, (center_x, center_y), radius, 255, -1)

    return mask
