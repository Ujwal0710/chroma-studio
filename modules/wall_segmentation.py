"""Wall segmentation pipeline using gradient edge detection, color homogeneity, and seed growing."""
from typing import Tuple, Optional, Dict, Any
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

from modules.image_processing import pil_to_numpy_rgb, rgb_to_cielab


def compute_gradient_magnitude(gray_arr: np.ndarray) -> np.ndarray:
    """Compute 2D spatial gradient magnitude using Sobel kernels."""
    # Sobel kernels
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    grad_x = ndimage.convolve(gray_arr.astype(np.float32), sobel_x)
    grad_y = ndimage.convolve(gray_arr.astype(np.float32), sobel_y)

    grad_mag = np.hypot(grad_x, grad_y)
    # Normalize to [0, 255]
    max_val = np.max(grad_mag)
    if max_val > 0:
        grad_mag = (grad_mag / max_val) * 255.0
    return grad_mag.astype(np.uint8)


def generate_wall_mask(
    img: Image.Image,
    sensitivity: float = 0.55,
    upper_bias: float = 0.70,
    edge_protection: float = 0.65,
    manual_seed: Optional[Tuple[int, int]] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate an intelligent wall mask preserving furniture, floorboards, windows, and decor.

    Parameters:
        img: Input PIL Image
        sensitivity: Tolerance for wall tonal variance (0.1 to 1.0)
        upper_bias: Vertical prior penalizing bottom flooring (0.0 to 1.0)
        edge_protection: Strength of edge and boundary barrier preservation (0.1 to 1.0)
        manual_seed: Optional (x, y) coordinate to anchor wall region growing

    Returns:
        Tuple of (mask_uint8, metadata_dict) where mask_uint8 is [0..255]
    """
    arr = pil_to_numpy_rgb(img)
    height, width, _ = arr.shape

    # Grayscale conversion (standard luminance weights)
    gray = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.uint8)

    # 1. Edge and Boundary Map
    grad = compute_gradient_magnitude(gray)
    edge_threshold = int(255 * (1.05 - edge_protection * 0.75))
    edges = grad > edge_threshold

    # 2. Vertical position prior (walls dominate upper 70% of interior photography)
    y_coords, _ = np.indices((height, width))
    vertical_factor = y_coords / float(height)

    # Floor exclusion threshold based on upper_bias
    floor_cutoff = 1.0 - (upper_bias * 0.35)  # e.g., cuts off lowest 20-30% if upper_bias is high
    floor_mask = vertical_factor > floor_cutoff

    # 3. Candidate Seed Points
    if manual_seed is not None and 0 <= manual_seed[0] < width and 0 <= manual_seed[1] < height:
        seed_x, seed_y = manual_seed
        seed_pixels = [(seed_y, seed_x)]
    else:
        # Automatic seed selection: upper-middle regions with low gradient and non-extreme luminance
        upper_height = int(height * 0.45)
        candidate_region = (~edges[:upper_height, :]) & (gray[:upper_height, :] > 35) & (gray[:upper_height, :] < 240)

        # Sample grid points in low-gradient upper region
        step = max(10, width // 20)
        seed_pixels = []
        for y in range(int(height * 0.10), upper_height, step):
            for x in range(int(width * 0.15), int(width * 0.85), step):
                if candidate_region[y, x]:
                    seed_pixels.append((y, x))

    if not seed_pixels:
        # Fallback to upper center pixel
        seed_pixels = [(int(height * 0.25), int(width * 0.5))]

    # 4. Color & Luminance Homogeneity Distance from seed tones
    seed_rgbs = [arr[sy, sx] for sy, sx in seed_pixels[:12]]
    avg_seed_rgb = np.mean(seed_rgbs, axis=0)

    # Distance in RGB space
    diff = np.sqrt(np.sum((arr.astype(np.float32) - avg_seed_rgb) ** 2, axis=2))
    max_dist = 60.0 + (sensitivity * 90.0)  # Sensitivity expands allowed color variance
    homogeneity_mask = diff <= max_dist

    # 5. Combine cues: low gradient + color homogeneity + floor suppression
    raw_wall = homogeneity_mask & (~edges) & (~floor_mask)

    # 6. Morphological cleanup (closing small holes, removing isolated noise)
    structure_open = np.ones((3, 3), dtype=bool)
    structure_close = np.ones((7, 7), dtype=bool)

    # Binary opening to discard thin edge noise
    cleaned = ndimage.binary_opening(raw_wall, structure=structure_open)
    # Binary closing to bridge subtle texture variations on wall paint
    cleaned = ndimage.binary_closing(cleaned, structure=structure_close)

    # Retain substantial connected components
    labeled, num_features = ndimage.label(cleaned)
    if num_features > 0:
        sizes = ndimage.sum(cleaned, labeled, range(1, num_features + 1))
        # Keep components with at least 0.5% of total image area
        min_size = (height * width) * 0.005
        keep_labels = [i + 1 for i, s in enumerate(sizes) if s >= min_size]
        final_mask_bool = np.isin(labeled, keep_labels)
    else:
        final_mask_bool = cleaned

    mask_uint8 = (final_mask_bool.astype(np.uint8)) * 255

    # Calculate coverage and confidence
    coverage_pct = round((np.sum(mask_uint8 > 0) / float(height * width)) * 100.0, 1)

    # Confidence heuristic: typical interior wall coverage is between 20% and 65%
    if 20.0 <= coverage_pct <= 65.0:
        confidence = "High (Clear continuous wall planes detected)"
    elif 10.0 <= coverage_pct < 20.0:
        confidence = "Moderate (Compact or partially visible wall region)"
    elif coverage_pct > 65.0:
        confidence = "Moderate (Broad coverage; ensure flooring/furniture boundaries are preserved)"
    else:
        confidence = "Low (Limited wall plane detected; consider adjusting sensitivity)"

    metadata = {
        "wall_coverage_percent": coverage_pct,
        "segmentation_confidence": confidence,
        "sensitivity": sensitivity,
        "edge_protection": edge_protection,
        "upper_bias": upper_bias,
        "seed_count": len(seed_pixels)
    }

    return mask_uint8, metadata
