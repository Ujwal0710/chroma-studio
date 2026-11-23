"""Room colour visualization, multi-strategy wall recolouring, and comparison generation.

Features:
1. Zero-bleed mask-aware colour transformations (guarantees pixels outside mask remain untouched).
2. Multiple luminance preservation & colour space strategies:
   - 'cielab_perceptual': CIELAB Lightness Transfer (true target chroma + texture/shadow preservation).
   - 'adaptive_luminance': ITU-R BT.709 Luminance ratio with highlight/shadow compression.
   - 'architectural_glaze': Direct photometric overlay preserving subsurface grain.
3. Configurable shading depth (0.0 to 1.0) rather than forcing 100% luminance preservation.
4. Specular highlight and deep shadow protection.
5. Inner-feathering to eliminate jagged seams without spilling outside the mask.
6. Side-by-side, split-slider, and mask overlay visual comparison utilities.
"""
from typing import Tuple
import numpy as np
from PIL import Image, ImageDraw
import cv2

from modules.image_processing import (
    pil_to_numpy_rgb,
    numpy_rgb_to_pil
)


LUMINANCE_STRATEGIES = {
    "cielab_perceptual": "Perceptual CIELAB (Accurate tone values + natural texture)",
    "adaptive_luminance": "Adaptive Luminance Ratio (High-contrast shadow retention)",
    "architectural_glaze": "Direct Glaze / Tint (Subtle translucent finish)"
}

__all__ = [
    "LUMINANCE_STRATEGIES",
    "apply_luminance_preserving_recolour",
    "create_side_by_side_comparison",
    "create_split_slider_comparison",
    "create_mask_overlay_preview"
]


def apply_luminance_preserving_recolour(
    original_img: Image.Image,
    wall_mask: np.ndarray,
    target_rgb: Tuple[int, int, int],
    intensity: float = 0.85,
    feather_radius: int = 2,
    strategy: str = "cielab_perceptual",
    shading_retention: float = 0.75
) -> Image.Image:
    """
    Recolour the masked wall surfaces in the room while preserving natural shadows,
    ambient depth, surface texture, and optical lighting falloff.

    Parameters:
        original_img: PIL Image of the room.
        wall_mask: 2D uint8 numpy array [0..255].
        target_rgb: Target paint RGB tuple (e.g. (215, 180, 140)).
        intensity: Recolouring blend factor [0.0 to 1.0].
        feather_radius: Gaussian smoothing radius for anti-aliasing.
        strategy: 'cielab_perceptual' | 'adaptive_luminance' | 'architectural_glaze'.
        shading_retention: Degree of original wall texture/shadows preserved [0.0 to 1.0].

    Returns:
        Recoloured PIL Image with zero outside-mask bleed.
    """
    orig_arr = pil_to_numpy_rgb(original_img)
    height, width, _ = orig_arr.shape

    # If mask is empty, return exact copy
    if np.sum(wall_mask > 0) == 0:
        return original_img.copy()

    # Create strict binary mask
    binary_mask = (wall_mask > 0)

    # 1. Inner Feathering: Ensure non-zero alpha occurs ONLY inside binary_mask (strict zero bleed)
    if feather_radius > 0:
        # Distance transform to smoothly roll off inside boundary
        dist = cv2.distanceTransform(binary_mask.astype(np.uint8), cv2.DIST_L2, 3)
        # Normalize distance within feather radius
        alpha = np.clip(dist / float(feather_radius), 0.0, 1.0)
    else:
        alpha = binary_mask.astype(np.float32)

    # Modulate alpha by overall user intensity
    alpha = np.clip(alpha * intensity, 0.0, 1.0)
    # Strictly zero out outside mask
    alpha[~binary_mask] = 0.0

    t_r, t_g, t_b = float(target_rgb[0]), float(target_rgb[1]), float(target_rgb[2])

    # 2. Compute Recoloured Wall Array Based on Selected Strategy
    if strategy == "cielab_perceptual":
        # Strategy A: CIELAB Perceptual Lightness Transfer
        orig_lab = cv2.cvtColor(orig_arr, cv2.COLOR_RGB2LAB).astype(np.float32)
        target_patch = np.uint8([[[t_r, t_g, t_b]]])
        target_lab = cv2.cvtColor(target_patch, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]

        # L channel is [0..255] in OpenCV
        orig_l = orig_lab[:, :, 0]
        mean_wall_l = float(np.mean(orig_l[binary_mask])) if np.any(binary_mask) else 128.0
        mean_wall_l = max(mean_wall_l, 10.0)

        # L texture deviation (local shadows and highlights relative to mean wall luminance)
        l_delta = (orig_l - mean_wall_l) * shading_retention

        # Synthesized L channel combines target paint lightness with preserved texture delta
        synth_l = np.clip(target_lab[0] + l_delta, 5.0, 250.0)

        # Protect extreme specular highlights from turning into flat paint
        highlight_mask = (orig_l > 235.0)
        synth_l[highlight_mask] = orig_l[highlight_mask]

        # Synthesize LAB
        synth_lab = np.zeros_like(orig_lab)
        synth_lab[:, :, 0] = synth_l
        synth_lab[:, :, 1] = target_lab[1]
        synth_lab[:, :, 2] = target_lab[2]

        recoloured_rgb = cv2.cvtColor(np.clip(synth_lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)

    elif strategy == "architectural_glaze":
        # Strategy B: High-fidelity optical glaze / translucent wash via HSV chromatic transfer
        orig_hsv = cv2.cvtColor(orig_arr, cv2.COLOR_RGB2HSV).astype(np.float32)
        target_patch = np.uint8([[[t_r, t_g, t_b]]])
        target_hsv = cv2.cvtColor(target_patch, cv2.COLOR_RGB2HSV).astype(np.float32)[0, 0]

        tint_hsv = np.zeros_like(orig_hsv)
        tint_hsv[:, :, 0] = target_hsv[0]  # Target paint hue
        tint_hsv[:, :, 1] = target_hsv[1] * np.clip(intensity, 0.35, 1.0)  # Target paint saturation
        # Retain original surface value and texture modulation
        val_delta = (orig_hsv[:, :, 2] - 128.0) * shading_retention
        tint_hsv[:, :, 2] = np.clip(orig_hsv[:, :, 2] + val_delta * 0.15, 0.0, 255.0)

        recoloured_rgb = cv2.cvtColor(np.clip(tint_hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)

    else:
        # Strategy C: Adaptive Luminance Ratio (ITU-R BT.709)
        arr_f = orig_arr.astype(np.float32)
        lum_orig = 0.2126 * arr_f[:, :, 0] + 0.7152 * arr_f[:, :, 1] + 0.0722 * arr_f[:, :, 2]
        mean_wall_lum = float(np.mean(lum_orig[binary_mask])) if np.any(binary_mask) else 128.0
        mean_wall_lum = max(mean_wall_lum, 10.0)

        lum_ratio = lum_orig / mean_wall_lum
        # Shading retention governs how intensely the ratio shifts the paint
        scaled_ratio = np.power(np.clip(lum_ratio, 0.15, 3.0), np.clip(shading_retention, 0.2, 1.2))

        rec_r = np.clip(t_r * scaled_ratio, 0.0, 255.0)
        rec_g = np.clip(t_g * scaled_ratio, 0.0, 255.0)
        rec_b = np.clip(t_b * scaled_ratio, 0.0, 255.0)
        recoloured_rgb = np.stack([rec_r, rec_g, rec_b], axis=2)

    # 3. Soft Alpha Compositing strictly within the mask
    alpha_3d = np.repeat(alpha[:, :, np.newaxis], 3, axis=2)
    blended = alpha_3d * recoloured_rgb + (1.0 - alpha_3d) * orig_arr.astype(np.float32)

    # Strictly guarantee that pixels where binary_mask == False are IDENTICAL to original
    blended_uint8 = np.clip(blended, 0.0, 255.0).astype(np.uint8)
    blended_uint8[~binary_mask] = orig_arr[~binary_mask]

    return numpy_rgb_to_pil(blended_uint8)


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
    header_h = 56
    divider_w = 4

    total_w = w * 2 + divider_w
    total_h = h + header_h

    canvas = Image.new("RGB", (total_w, total_h), color=(245, 240, 232))
    draw = ImageDraw.Draw(canvas)

    canvas.paste(original_img, (0, header_h))
    canvas.paste(recoloured_img, (w + divider_w, header_h))

    # Divider bar
    draw.rectangle([w, 0, w + divider_w, total_h], fill=(227, 216, 203))

    label_left = "ORIGINAL PHOTOGRAPH"
    label_right = f"WALL RECOLOURED: {paint_name.upper()}" + (f" ({hex_code})" if hex_code else "")

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
    split_x = int(w * np.clip(split_ratio, 0.05, 0.95))

    canvas = original_img.copy()
    crop_box = (split_x, 0, w, h)
    right_part = recoloured_img.crop(crop_box)
    canvas.paste(right_part, (split_x, 0))

    draw = ImageDraw.Draw(canvas)
    line_w = 3
    draw.line([(split_x, 0), (split_x, h)], fill=(255, 255, 255), width=line_w)

    cy = h // 2
    r = 16
    draw.ellipse([(split_x - r, cy - r), (split_x + r, cy + r)], fill=(255, 252, 247), outline=(114, 86, 64), width=2)
    draw.text((split_x - 7, cy - 8), "◀▶", fill=(48, 39, 31))

    draw.rectangle([(15, 15), (115, 45)], fill=(48, 39, 31, 200))
    draw.text((25, 22), "ORIGINAL", fill=(255, 255, 255))

    lbl_text = f"PREVIEW: {paint_name}" if paint_name else "PREVIEW"
    draw.rectangle([(w - 180, 15), (w - 15, 45)], fill=(114, 86, 64, 200))
    draw.text((w - 170, 22), lbl_text[:20], fill=(255, 255, 255))

    return canvas


def create_mask_overlay_preview(
    original_img: Image.Image,
    wall_mask: np.ndarray,
    show_boundary_contour: bool = True
) -> Image.Image:
    """
    Generate visual verification overlay highlighting detected wall areas with a translucent terracotta tint
    and optional high-contrast architectural boundary lines.
    """
    arr = pil_to_numpy_rgb(original_img).astype(np.float32)
    mask_norm = (wall_mask.astype(np.float32) / 255.0)[:, :, np.newaxis]

    # Warm terracotta tint overlay (200, 100, 60)
    tint_layer = np.zeros_like(arr)
    tint_layer[:, :, 0] = 200.0
    tint_layer[:, :, 1] = 100.0
    tint_layer[:, :, 2] = 60.0

    alpha = mask_norm * 0.45
    blended = alpha * tint_layer + (1.0 - alpha) * arr

    if show_boundary_contour:
        contours, _ = cv2.findContours(wall_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour_layer = np.zeros(arr.shape[:2], dtype=np.uint8)
        cv2.drawContours(contour_layer, contours, -1, 255, thickness=2)
        # Draw gold boundary lines
        boundary_idx = contour_layer > 0
        blended[boundary_idx, 0] = 235.0
        blended[boundary_idx, 1] = 180.0
        blended[boundary_idx, 2] = 75.0

    blended = np.clip(blended, 0.0, 255.0).astype(np.uint8)
    return numpy_rgb_to_pil(blended)
