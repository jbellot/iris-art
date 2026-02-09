"""Server-side watermark application for free exports."""

import logging
import math

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def apply_watermark(image: Image.Image, is_paid: bool) -> Image.Image:
    """Apply semi-transparent watermark to image.

    Free exports get a tiled diagonal "IrisVue" watermark that is difficult
    to remove by cropping. Paid exports are returned unmodified.

    Args:
        image: Input image (PIL Image)
        is_paid: Whether user paid for watermark-free export

    Returns:
        Image with watermark applied (or original if paid)
    """
    if is_paid:
        logger.info("Paid export - no watermark applied")
        return image

    logger.info("Free export - applying watermark")

    # Create a copy to avoid modifying original
    watermarked = image.copy()
    width, height = watermarked.size

    # Create transparent overlay for watermark
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Calculate font size (proportional to image size)
    font_size = max(width // 8, 60)

    # Try to load a nice font, fall back to default if unavailable
    try:
        # Try DejaVu Sans (common on Linux)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        try:
            # Try Arial (common on Windows)
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            # Fall back to default font
            logger.warning("TrueType fonts not available, using default font")
            font = ImageFont.load_default()

    # Watermark text
    watermark_text = "IrisVue"

    # Get text bounding box
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate diagonal spacing for tiled pattern
    # Rotate 45 degrees, so diagonal length is sqrt(2) * dimension
    diagonal = math.sqrt(width**2 + height**2)
    num_repeats = int(diagonal / (text_width * 1.5)) + 2

    # Create rotated overlay for diagonal watermark
    rotated_overlay = Image.new("RGBA", (int(diagonal * 2), int(diagonal * 2)), (0, 0, 0, 0))
    rotated_draw = ImageDraw.Draw(rotated_overlay)

    # Draw tiled watermark pattern
    semi_transparent_white = (255, 255, 255, 80)  # RGBA with alpha=80/255

    y_spacing = text_height * 3
    x_spacing = text_width * 2

    for i in range(-2, num_repeats + 2):
        for j in range(-2, num_repeats + 2):
            x = int(diagonal) + (i * x_spacing)
            y = int(diagonal / 2) + (j * y_spacing)

            rotated_draw.text(
                (x, y),
                watermark_text,
                fill=semi_transparent_white,
                font=font,
            )

    # Rotate overlay 45 degrees
    rotated_overlay = rotated_overlay.rotate(45, expand=False)

    # Crop rotated overlay to original image size (centered)
    crop_x = (rotated_overlay.width - width) // 2
    crop_y = (rotated_overlay.height - height) // 2
    rotated_overlay = rotated_overlay.crop((crop_x, crop_y, crop_x + width, crop_y + height))

    # Add "Free Preview" text in bottom-right corner
    small_font_size = max(width // 40, 20)
    try:
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", small_font_size)
    except Exception:
        small_font = font  # Use same font if small font not available

    preview_text = "Free Preview"
    preview_bbox = draw.textbbox((0, 0), preview_text, font=small_font)
    preview_width = preview_bbox[2] - preview_bbox[0]
    preview_height = preview_bbox[3] - preview_bbox[1]

    # Position in bottom-right with padding
    padding = 20
    preview_x = width - preview_width - padding
    preview_y = height - preview_height - padding

    preview_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    preview_draw = ImageDraw.Draw(preview_overlay)
    preview_draw.text(
        (preview_x, preview_y),
        preview_text,
        fill=semi_transparent_white,
        font=small_font,
    )

    # Composite watermarks onto image
    if watermarked.mode != "RGBA":
        watermarked = watermarked.convert("RGBA")

    watermarked = Image.alpha_composite(watermarked, rotated_overlay)
    watermarked = Image.alpha_composite(watermarked, preview_overlay)

    # Convert back to RGB if original was RGB
    if image.mode == "RGB":
        watermarked = watermarked.convert("RGB")

    logger.info("Watermark applied successfully")
    return watermarked
