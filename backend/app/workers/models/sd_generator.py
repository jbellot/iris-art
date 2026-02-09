"""Stable Diffusion SDXL Turbo wrapper for AI art generation."""

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class SDXLTurboGenerator:
    """SDXL Turbo image-to-image generator with ControlNet support.

    Generates unique artistic compositions from iris images using
    Stable Diffusion XL Turbo model with optional ControlNet guidance.

    Dev-mode fallback: Uses OpenCV artistic filters when torch/CUDA unavailable.
    """

    def __init__(self):
        """Initialize generator (models loaded lazily)."""
        self.pipeline = None
        self.controlnet = None
        self.device = None
        self.dev_mode = False

    def load(self):
        """Load SDXL Turbo pipeline with xformers memory optimization.

        Falls back to dev-mode OpenCV if torch/CUDA unavailable.
        """
        try:
            import torch
            from diffusers import AutoPipelineForImage2Image

            # Check CUDA availability
            if not torch.cuda.is_available():
                logger.warning(
                    "CUDA not available. Using OpenCV simulation (dev mode)."
                )
                self.dev_mode = True
                return

            self.device = "cuda"

            # Load SDXL Turbo pipeline
            logger.info("Loading SDXL Turbo pipeline...")
            self.pipeline = AutoPipelineForImage2Image.from_pretrained(
                "stabilityai/sdxl-turbo",
                torch_dtype=torch.float16,
                variant="fp16",
            )
            self.pipeline.to(self.device)

            # Enable xformers for memory efficiency
            try:
                self.pipeline.enable_xformers_memory_efficient_attention()
                logger.info("xformers memory efficient attention enabled")
            except Exception as e:
                logger.warning(f"xformers not available: {e}")

            logger.info("SDXL Turbo pipeline loaded successfully")

        except ImportError:
            logger.warning(
                "torch or diffusers not available. Using OpenCV simulation (dev mode)."
            )
            self.dev_mode = True
        except Exception as e:
            logger.error(f"Failed to load SDXL Turbo: {e}")
            logger.warning("Falling back to OpenCV simulation (dev mode)")
            self.dev_mode = True

    def generate(
        self,
        iris_image: Image.Image,
        prompt: str,
        control_image: Optional[Image.Image] = None,
        num_steps: int = 4,
        strength: float = 0.8,
    ) -> Image.Image:
        """Generate artistic composition from iris image.

        Args:
            iris_image: Source iris image (PIL Image)
            prompt: Text prompt describing desired art style
            control_image: Optional ControlNet edge map for guidance
            num_steps: Number of inference steps (default: 4 for Turbo)
            strength: Transformation strength 0-1 (default: 0.8)

        Returns:
            Generated artistic image at 1024x1024 (PIL Image)
        """
        if self.dev_mode or self.pipeline is None:
            return self._generate_dev_mode(iris_image, prompt)

        try:
            import torch

            # Resize iris image to 1024x1024 for SDXL
            iris_image = iris_image.resize((1024, 1024), Image.LANCZOS)

            # Generate with SDXL Turbo
            # Note: SDXL Turbo doesn't use guidance_scale (set to 0.0)
            result = self.pipeline(
                prompt=prompt,
                image=iris_image,
                num_inference_steps=num_steps,
                strength=strength,
                guidance_scale=0.0,  # Turbo doesn't need guidance
            ).images[0]

            # Clear GPU cache after generation
            torch.cuda.empty_cache()

            return result

        except Exception as e:
            logger.error(f"SDXL generation failed: {e}")
            logger.warning("Falling back to dev-mode generation")
            return self._generate_dev_mode(iris_image, prompt)

    def _generate_dev_mode(self, iris_image: Image.Image, prompt: str) -> Image.Image:
        """Dev-mode fallback using OpenCV artistic filters.

        Creates a visually distinct artistic image by combining:
        - Edge-preserving filtering
        - Color quantization
        - Style-based color overlay

        Args:
            iris_image: Source iris image (PIL Image)
            prompt: Text prompt (used to select color overlay)

        Returns:
            Stylized image at 1024x1024 (PIL Image)
        """
        logger.info("SDXL Turbo not available, using OpenCV simulation (dev mode)")

        # Convert PIL to OpenCV
        img_array = np.array(iris_image)
        if img_array.shape[2] == 4:  # RGBA
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        else:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Resize to 1024x1024
        img_array = cv2.resize(img_array, (1024, 1024), interpolation=cv2.INTER_LANCZOS4)

        # Apply edge-preserving filter for artistic effect
        filtered = cv2.edgePreservingFilter(img_array, flags=1, sigma_s=60, sigma_r=0.4)

        # Apply stylization for painterly effect
        stylized = cv2.stylization(filtered, sigma_s=60, sigma_r=0.07)

        # Color quantization for more artistic look (reduce colors to 16)
        quantized = self._color_quantize(stylized, k=16)

        # Apply color overlay based on prompt keywords
        result = self._apply_style_overlay(quantized, prompt)

        # Convert back to PIL
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        return Image.fromarray(result_rgb)

    def _color_quantize(self, image: np.ndarray, k: int = 16) -> np.ndarray:
        """Reduce color palette using k-means clustering.

        Args:
            image: Input image (OpenCV BGR format)
            k: Number of colors to reduce to

        Returns:
            Quantized image
        """
        # Reshape to pixel list
        pixels = image.reshape((-1, 3))
        pixels = np.float32(pixels)

        # K-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS
        )

        # Map pixels to cluster centers
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()]
        quantized = quantized.reshape(image.shape)

        return quantized

    def _apply_style_overlay(self, image: np.ndarray, prompt: str) -> np.ndarray:
        """Apply color overlay based on prompt keywords.

        Args:
            image: Input image (OpenCV BGR format)
            prompt: Text prompt

        Returns:
            Image with style-specific color overlay
        """
        prompt_lower = prompt.lower()

        # Define style overlays (BGR format)
        overlays = {
            "cosmic": ([139, 69, 19], 0.15),      # Deep blue/purple
            "sunset": ([30, 105, 255], 0.20),     # Orange/gold
            "ocean": ([180, 130, 20], 0.18),      # Blue/teal
            "fire": ([0, 69, 255], 0.22),         # Red/orange
            "forest": ([50, 150, 50], 0.15),      # Green
            "abstract": ([200, 100, 200], 0.12),  # Purple
            "watercolor": ([220, 220, 255], 0.10),# Soft pink
            "oil": ([80, 100, 120], 0.18),        # Warm brown
            "neon": ([255, 0, 255], 0.25),        # Bright magenta
            "minimal": ([200, 200, 200], 0.08),   # Subtle gray
        }

        # Find matching style keyword
        selected_color = ([100, 100, 150], 0.12)  # Default: subtle blue
        for keyword, (color, alpha) in overlays.items():
            if keyword in prompt_lower:
                selected_color = (color, alpha)
                break

        # Create color overlay
        overlay = np.full_like(image, selected_color[0], dtype=np.uint8)

        # Blend with original
        result = cv2.addWeighted(image, 1.0 - selected_color[1], overlay, selected_color[1], 0)

        return result

    def unload(self):
        """Unload model to free GPU memory."""
        if self.pipeline is not None:
            try:
                import torch
                del self.pipeline
                self.pipeline = None
                torch.cuda.empty_cache()
                logger.info("Unloaded SDXL Turbo pipeline")
            except Exception as e:
                logger.warning(f"Error unloading SDXL pipeline: {e}")
