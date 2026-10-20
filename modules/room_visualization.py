"""Room colour visualization, luminance-preserving wall recolouring, and comparison generation."""
import math
from typing import Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from scipy import ndimage

from modules.image_processing import (
    pil_to_numpy_rgb,
    numpy_rgb_to_pil,
    rgb_to_cielab,
    calculate_perceptual_luminance
)
from modules.wall_segmentation import generate_wall_mask


def apply_luminance_preserving_recolour(
    original_img: Image.Image,
    wall_mask: np.ndarray,
    target_rgb: Tuple[int, int, int],
    intensity: float = 0.85,
    feather_radius: int = 3
) -> Image.Image:
    """
    Recolour the masked wall surfaces in the room while preserving natural shadows,
    ambient depth, surface texture, and optical lighting falloff.

    Parameters:
        original_img: PIL Image of the room
        wall_mask: 2D uint8 numpy array [0..255]
        target_rgb: Target paint RGB tuple (e.g. (215, 180, 140))
        intensity: Recolouring blend factor [0.0 to 1.0]
        feather_radius: Gaussian blur sigma on mask boundary to eliminate harsh jagged seams

    Returns:
        Recoloured PIL Image
    """
    arr = pil_to_numpy_rgb(original_img).astype(np.float32)
    height, width, _ = arr.shape

    # 1. Soft feather the mask edges using gaussian filter
    if feather_radius > 0:
        mask_float = ndimage.gaussian_filter(wall_mask.astype(np.float32) / 255.0, sigma=feather_radius)
    else:
        mask_float = wall_mask.astype(np.float32) / 255.0

    mask_float = np.clip(mask_float * intensity, 0.0, 1.0)
    # Expand to 3-channel
    alpha_3d = np.repeat(mask_float[:, :, np.newaxis], 3, axis=2)

    # If mask is empty, return original
    if np.sum(wall_mask) == 0:
        return original_img.copy()

    # 2. Extract original image luminance channel (ITU-R BT.709)
    # Y = 0.2126 R + 0.7152 G + 0.0722 B
    lum_orig = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]

    # Calculate average luminance of the existing wall region
    wall_indices = wall_mask > 50
    if np.any(wall_indices):
        avg_wall_lum = float(np.mean(lum_orig[wall_indices]))
    else:
        avg_wall_lum = float(np.mean(lum_orig))
    avg_wall_lum = max(avg_wall_lum, 10.0)

    # Target paint characteristics
    t_r, t_g, t_b = float(target_rgb[0]), float(target_rgb[1]), float(target_rgb[2])
    target_lum = 0.2126 * t_r + 0.7152 * t_g + 0.0722 * t_b
    target_lum = max(target_lum, 10.0)

    # 3. Luminance-scaled target RGB plane
    # Scale factor represents local shadows / highlights relative to average wall luminance
    lum_ratio = lum_orig / avg_wall_lum
    # Gentle compression so deep shadows don't saturate into pure black
    lum_scale = np.power(np.clip(lum_ratio, 0.15, 3.0), 0.85)

    # Synthesized painted wall channels
    recoloured_r = np.clip(t_r * lum_scale, 0.0, 255.0)
    recoloured_g = np.clip(t_g * lum_scale, 0.0, 255.0)
    recoloured_b = np.clip(t_b * lum_scale, 0.0, 255.0)

    recoloured_wall = np.stack([recoloured_r, recoloured_g, recoloured_b], axis=2)

    # 4. Soft Alpha Compositing
    # Result = Alpha * Recoloured + (1 - Alpha) * Original
    blended = alpha_3d * recoloured_wall + (1.0 - alpha_3d) * arr
    blended = np.clip(blended, 0.0, 255.0).astype(np.uint8)

    return numpy_rgb_to_pil(blended)


def create_side_by_side_comparison(
    original_img: Image.Image,
    recoloured_img: Image.Image,
    paint_name: str = "Selected Wall Hue",
    hex_code: str = ""
) -> Image.Image:
    """
    Generate a polished side-by-side comparison image with design-system typography and labels.
    """
    w, h = original_img.size
    # Header bar height
    header_h = 56
    divider_w = 4

    total_w = w * 2 + divider_w
    total_h = h + header_h

    # Create canvas with warm background
    canvas = Image.new("RGB", (total_w, total_h), color=(245, 240, 232))
    draw = ImageDraw.Draw(canvas)

    # Paste images
    canvas.paste(original_img, (0, header_h))
    canvas.paste(recoloured_img, (w + divider_w, header_h))

    # Divider bar
    draw.rectangle([w, 0, w + divider_w, total_h], fill=(227, 216, 203))

    # Header labels
    label_left = "ORIGINAL PHOTOGRAPH"
    label_right = f"WALL RECOLOURED: {paint_name.upper()}" + (f" ({hex_code})" if hex_code else "")

    # Draw title text
    draw.text((20, 18), label_left, fill=(48, 39, 31))
    draw.text((w + divider_w + 20, 18), label_right, fill=(114, 86, 64))

    return canvas


def create_split_slider_comparison(
    original_img: Image.Image,
    recoloured_img: Image.Image,
    split_ratio: float = 0.50,
    paint_name: str = ""
) -> Image.Image:
    """
    Generate a split before/after image at split_ratio (0.0 to 1.0) with an architectural divider line.
    """
    w, h = original_img.size
    split_x = int(w * split_ratio)

    canvas = original_img.copy()
    # Crop right portion of recoloured image and paste
    crop_box = (split_x, 0, w, h)
    right_part = recoloured_img.crop(crop_box)
    canvas.paste(right_part, (split_x, 0))

    # Draw divider line and handle
    draw = ImageDraw.Draw(canvas)
    line_w = 3
    draw.line([(split_x, 0), (split_x, h)], fill=(255, 255, 255), width=line_w)

    # Circular handle in center
    cy = h // 2
    r = 16
    draw.ellipse([(split_x - r, cy - r), (split_x + r, cy + r)], fill=(255, 252, 247), outline=(114, 86, 64), width=2)
    draw.text((split_x - 7, cy - 8), "◀▶", fill=(48, 39, 31))

    # Labels
    draw.rectangle([(15, 15), (115, 45)], fill=(48, 39, 31, 200))
    draw.text((25, 22), "ORIGINAL", fill=(255, 255, 255))

    lbl_text = f"PREVIEW: {paint_name}" if paint_name else "PREVIEW"
    draw.rectangle([(w - 180, 15), (w - 15, 45)], fill=(114, 86, 64, 200))
    draw.text((w - 170, 22), lbl_text[:20], fill=(255, 255, 255))

    return canvas


def create_mask_overlay_preview(
    original_img: Image.Image,
    wall_mask: np.ndarray
) -> Image.Image:
    """
    Generate visual verification overlay highlighting detected wall areas with a translucent terracotta tint.
    """
    arr = pil_to_numpy_rgb(original_img).astype(np.float32)
    mask_norm = (wall_mask.astype(np.float32) / 255.0)[:, :, np.newaxis]

    # Warm terracotta tint overlay (200, 100, 60)
    tint_layer = np.zeros_like(arr)
    tint_layer[:, :, 0] = 200.0
    tint_layer[:, :, 1] = 100.0
    tint_layer[:, :, 2] = 60.0

    # Blend with 45% opacity on masked pixels
    alpha = mask_norm * 0.45
    blended = alpha * tint_layer + (1.0 - alpha) * arr
    blended = np.clip(blended, 0.0, 255.0).astype(np.uint8)

    return numpy_rgb_to_pil(blended)
