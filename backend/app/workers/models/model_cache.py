"""Singleton model cache for AI models with lazy loading."""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ModelCache:
    """Singleton cache for AI models loaded once at worker startup."""

    _segmentation_model = None
    _enhancement_model = None
    _reflection_model = None
    _style_models: dict = {}  # Cache style models by style name

    @classmethod
    def get_segmentation_model(cls):
        """Get or load ONNX segmentation model (lazy load).

        Returns:
            ONNX InferenceSession or None if model file not found
        """
        if cls._segmentation_model is None:
            try:
                import onnxruntime as ort

                model_path = Path(__file__).parent / "weights" / "unet_iris_segmentation.onnx"

                if not model_path.exists():
                    logger.warning(
                        f"Segmentation model not found at {model_path}. "
                        "Will use simulated segmentation (dev mode)."
                    )
                    return None

                # Try CUDA first, fall back to CPU
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                cls._segmentation_model = ort.InferenceSession(str(model_path), providers=providers)

                # Log which provider is being used
                provider_name = cls._segmentation_model.get_providers()[0]
                logger.info(f"Loaded segmentation model with provider: {provider_name}")

            except Exception as e:
                logger.error(f"Failed to load segmentation model: {e}")
                return None

        return cls._segmentation_model

    @classmethod
    def get_enhancement_model(cls):
        """Get or load Real-ESRGAN enhancement model (lazy load).

        Returns:
            RealESRGAN enhancer or None if model file not found
        """
        if cls._enhancement_model is None:
            try:
                model_path = Path(__file__).parent / "weights" / "RealESRGAN_x4plus.pth"

                if not model_path.exists():
                    logger.warning(
                        f"Enhancement model not found at {model_path}. "
                        "Will use OpenCV fallback (dev mode)."
                    )
                    return None

                # Real-ESRGAN setup would go here
                # For now, returning None to use OpenCV fallback
                logger.info("Enhancement model support pending - using OpenCV fallback")
                return None

            except Exception as e:
                logger.error(f"Failed to load enhancement model: {e}")
                return None

        return cls._enhancement_model

    @classmethod
    def get_reflection_model(cls):
        """Get or load reflection removal model (lazy load).

        For MVP: returns None to use OpenCV inpainting fallback.

        Returns:
            Reflection removal model or None
        """
        if cls._reflection_model is None:
            logger.info("Reflection removal using OpenCV inpainting (MVP approach)")
            # For MVP: return None to signal OpenCV fallback should be used
            return None

        return cls._reflection_model

    @classmethod
    def get_style_model(cls, style_name: str, model_path: str):
        """Get or load style transfer model (lazy load and cache by style name).

        Args:
            style_name: Unique style identifier (used as cache key)
            model_path: Path to ONNX model file

        Returns:
            StyleTransferModel instance
        """
        if style_name not in cls._style_models:
            try:
                from app.workers.models.style_transfer_model import StyleTransferModel

                model = StyleTransferModel()
                model.load(model_path)
                cls._style_models[style_name] = model

                logger.info(f"Loaded and cached style model: {style_name}")

            except Exception as e:
                logger.error(f"Failed to load style model {style_name}: {e}")
                raise

        return cls._style_models[style_name]

    @classmethod
    def clear_style_models(cls):
        """Clear all cached style models to free memory.

        Useful when switching to different model types (e.g., Stable Diffusion).
        """
        cls._style_models.clear()
        logger.info("Cleared all cached style models")
