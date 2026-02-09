"""Style transfer model using ONNX Runtime with OpenCV fallback."""

import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class StyleTransferModel:
    """Wrapper for Fast Neural Style Transfer using ONNX Runtime.

    Supports CUDA acceleration with CPU fallback.
    Falls back to OpenCV artistic filter if ONNX model not found (dev mode).
    """

    def __init__(self):
        """Initialize model (lazy loaded on first use)."""
        self.session = None
        self.input_name = None
        self.output_name = None
        self.model_loaded = False
        self.dev_mode = False

    def load(self, model_path: str | Path):
        """Load ONNX model from path.

        Args:
            model_path: Path to ONNX model file

        Raises:
            RuntimeError: If model loading fails unexpectedly
        """
        model_path = Path(model_path)

        # Check if model exists
        if not model_path.exists():
            logger.warning(
                f"Style model not found at {model_path}. "
                "Using OpenCV stylization fallback (dev mode)."
            )
            self.dev_mode = True
            self.model_loaded = True
            return

        try:
            import onnxruntime as ort

            # Try CUDA first, fall back to CPU
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self.session = ort.InferenceSession(str(model_path), providers=providers)

            # Get input/output names
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name

            # Log provider
            provider_name = self.session.get_providers()[0]
            logger.info(f"Loaded style model with provider: {provider_name}")

            self.model_loaded = True
            self.dev_mode = False

        except Exception as e:
            logger.error(f"Failed to load style model: {e}")
            logger.warning("Falling back to OpenCV stylization (dev mode)")
            self.dev_mode = True
            self.model_loaded = True

    def apply(self, image: np.ndarray, output_size: tuple[int, int] = (1024, 1024)) -> np.ndarray:
        """Apply style transfer to an image.

        Args:
            image: Input image as numpy array (HWC, BGR, uint8)
            output_size: Desired output size as (width, height)

        Returns:
            Styled image as numpy array (HWC, BGR, uint8)

        Raises:
            RuntimeError: If model not loaded or inference fails
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Dev mode: use OpenCV stylization as simulation
        if self.dev_mode:
            return self._apply_opencv_fallback(image, output_size)

        # ONNX inference mode
        return self._apply_onnx(image, output_size)

    def _apply_opencv_fallback(self, image: np.ndarray, output_size: tuple[int, int]) -> np.ndarray:
        """Apply OpenCV stylization as dev-mode fallback.

        Args:
            image: Input image (HWC, BGR, uint8)
            output_size: Desired output size (width, height)

        Returns:
            Styled image (HWC, BGR, uint8)
        """
        # Resize to output size
        resized = cv2.resize(image, output_size, interpolation=cv2.INTER_LANCZOS4)

        # Apply stylization filter for painterly effect
        styled = cv2.stylization(resized, sigma_s=60, sigma_r=0.07)

        logger.debug(f"Applied OpenCV stylization fallback at {output_size}")
        return styled

    def _apply_onnx(self, image: np.ndarray, output_size: tuple[int, int]) -> np.ndarray:
        """Apply ONNX style transfer.

        Args:
            image: Input image (HWC, BGR, uint8)
            output_size: Desired output size (width, height)

        Returns:
            Styled image (HWC, BGR, uint8)

        Raises:
            RuntimeError: If ONNX inference fails
        """
        try:
            # Preprocess: resize to model input size (typically 512x512)
            model_input_size = (512, 512)
            resized = cv2.resize(image, model_input_size, interpolation=cv2.INTER_LINEAR)

            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

            # Normalize to [0, 1]
            normalized = rgb_image.astype(np.float32) / 255.0

            # Convert HWC to CHW
            chw_image = np.transpose(normalized, (2, 0, 1))

            # Add batch dimension
            batch_image = np.expand_dims(chw_image, axis=0)

            # Run inference
            outputs = self.session.run([self.output_name], {self.input_name: batch_image})
            output = outputs[0]

            # Postprocess: remove batch dim, CHW to HWC
            output = output[0]
            output = np.transpose(output, (1, 2, 0))

            # Denormalize and clip to [0, 255]
            output = np.clip(output * 255.0, 0, 255).astype(np.uint8)

            # Convert RGB back to BGR
            output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)

            # Resize to desired output size
            final = cv2.resize(output_bgr, output_size, interpolation=cv2.INTER_LANCZOS4)

            logger.debug(f"Applied ONNX style transfer at {output_size}")
            return final

        except Exception as e:
            logger.error(f"ONNX inference failed: {e}")
            raise RuntimeError(f"Style transfer inference failed: {e}")
