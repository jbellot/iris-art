"""ControlNet preprocessing for iris edge and color extraction."""

import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ControlNetProcessor:
    """Extracts iris edges and color maps for ControlNet-guided generation.

    Uses OpenCV for edge detection and color analysis - no ML models needed.
    """

    def extract_iris_edges(self, image: Image.Image) -> Image.Image:
        """Extract edge map from iris image using Canny edge detection.

        Enhances iris radial patterns by strengthening detected edges
        around iris boundaries.

        Args:
            image: Input iris image (PIL Image)

        Returns:
            Edge map as PIL Image (white edges on black background)
        """
        # Convert PIL to OpenCV
        img_array = np.array(image)
        if img_array.shape[2] == 4:  # RGBA
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        else:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)

        # Enhance iris circular patterns using Hough Circle detection
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=100,
            param2=30,
            minRadius=30,
            maxRadius=200,
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            # Strengthen edges around detected circles
            for circle in circles[0, :]:
                center_x, center_y, radius = circle
                # Draw circle outline to strengthen boundary
                cv2.circle(edges, (center_x, center_y), radius, 255, 2)
                # Draw inner details
                cv2.circle(edges, (center_x, center_y), radius // 2, 255, 1)

        # Dilate edges slightly for better ControlNet guidance
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

        # Convert back to PIL
        edge_image = Image.fromarray(edges)

        logger.info("Extracted iris edge map with radial pattern enhancement")
        return edge_image

    def extract_color_map(self, image: Image.Image) -> Image.Image:
        """Extract dominant color palette from iris center.

        Uses k-means clustering to find dominant colors in the iris
        and creates an abstract color map.

        Args:
            image: Input iris image (PIL Image)

        Returns:
            Color map as PIL Image (abstract color composition)
        """
        # Convert PIL to OpenCV
        img_array = np.array(image)
        if img_array.shape[2] == 4:  # RGBA
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        else:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Extract center 50% of image (iris region)
        h, w = img_array.shape[:2]
        center_x, center_y = w // 2, h // 2
        crop_size = min(h, w) // 2
        iris_region = img_array[
            center_y - crop_size:center_y + crop_size,
            center_x - crop_size:center_x + crop_size
        ]

        # Reshape to pixel list
        pixels = iris_region.reshape((-1, 3))
        pixels = np.float32(pixels)

        # K-means clustering to find 5 dominant colors
        k = 5
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS
        )

        # Sort colors by frequency
        unique, counts = np.unique(labels, return_counts=True)
        sorted_indices = np.argsort(-counts)  # Sort descending
        dominant_colors = centers[sorted_indices]

        # Create abstract color map (radial gradient with dominant colors)
        color_map = self._create_color_composition(dominant_colors, (h, w))

        # Convert back to PIL
        color_map_rgb = cv2.cvtColor(color_map, cv2.COLOR_BGR2RGB)
        color_image = Image.fromarray(color_map_rgb)

        logger.info(f"Extracted {k} dominant iris colors for color map")
        return color_image

    def _create_color_composition(
        self, colors: np.ndarray, size: tuple[int, int]
    ) -> np.ndarray:
        """Create abstract color composition from dominant colors.

        Creates a radial gradient composition using the extracted colors.

        Args:
            colors: Array of dominant colors (BGR format)
            size: Output size (height, width)

        Returns:
            Color composition image (OpenCV BGR format)
        """
        h, w = size
        composition = np.zeros((h, w, 3), dtype=np.uint8)

        # Create radial zones for each color
        center_x, center_y = w // 2, h // 2
        max_radius = np.sqrt(center_x**2 + center_y**2)

        # Create coordinate grids
        y_coords, x_coords = np.ogrid[:h, :w]
        distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)

        # Assign colors based on radial distance
        num_colors = len(colors)
        for i in range(num_colors):
            start_radius = (i / num_colors) * max_radius
            end_radius = ((i + 1) / num_colors) * max_radius

            # Create mask for this color zone
            mask = (distances >= start_radius) & (distances < end_radius)

            # Apply color with gradient blending
            composition[mask] = colors[i].astype(np.uint8)

        # Apply Gaussian blur for smooth transitions
        composition = cv2.GaussianBlur(composition, (51, 51), 0)

        return composition
