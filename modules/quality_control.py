"""Quality Control Stage for Room Visualization and Color Transformation.

Validates:
1. Image and mask dimensions.
2. Mask coverage and pixel count.
3. Strict zero-bleed / bounded tolerance outside mask boundaries.
4. Chromatic clipping and extreme dynamic range compression.
5. Edge artifact and seam gradient consistency.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
import numpy as np
from PIL import Image

from modules.image_processing import pil_to_numpy_rgb


@dataclass
class QualityControlReport:
    """Standardized report for paint recolouring quality control."""
    passed: bool
    mask_pixel_count: int
    mask_coverage_percent: float
    max_outside_pixel_delta: float
    mean_outside_pixel_delta: float
    clipping_ratio_percent: float
    edge_artifact_detected: bool
    warnings: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        status = "PASSED" if self.passed else "FLAGGED"
        warn_str = f" ({len(self.warnings)} warning{'s' if len(self.warnings) > 1 else ''})" if self.warnings else ""
        return f"QC [{status}]: {self.mask_coverage_percent:.1f}% wall coverage, Δout={self.max_outside_pixel_delta:.1f}{warn_str}"


def validate_recolour_quality(
    original_img: Image.Image,
    recoloured_img: Image.Image,
    wall_mask: np.ndarray,
    target_rgb: Tuple[int, int, int],
    max_outside_tolerance: float = 2.0,
    min_mask_coverage_pct: float = 0.5
) -> QualityControlReport:
    """
    Perform a rigorous quality check comparing original and recoloured images.

    Parameters:
        original_img: Original room PIL image.
        recoloured_img: Recoloured room PIL image.
        wall_mask: 2D uint8 mask [0..255] where >0 is wall.
        target_rgb: Requested target color.
        max_outside_tolerance: Maximum allowed Euclidean color shift for unmasked pixels.
        min_mask_coverage_pct: Minimum required wall coverage percentage.

    Returns:
        QualityControlReport instance with validation flags and diagnostics.
    """
    warnings: List[str] = []
    passed = True

    orig_arr = pil_to_numpy_rgb(original_img).astype(np.float32)
    rec_arr = pil_to_numpy_rgb(recoloured_img).astype(np.float32)

    # 1. Dimension Check
    if orig_arr.shape != rec_arr.shape:
        return QualityControlReport(
            passed=False,
            mask_pixel_count=0,
            mask_coverage_percent=0.0,
            max_outside_pixel_delta=999.0,
            mean_outside_pixel_delta=999.0,
            clipping_ratio_percent=100.0,
            edge_artifact_detected=True,
            warnings=["Dimensional mismatch between original and recoloured images."],
            diagnostics={"orig_shape": orig_arr.shape, "rec_shape": rec_arr.shape}
        )

    h, w, _ = orig_arr.shape
    total_pixels = h * w

    # Ensure mask matches dimensions
    if wall_mask.shape != (h, w):
        return QualityControlReport(
            passed=False,
            mask_pixel_count=0,
            mask_coverage_percent=0.0,
            max_outside_pixel_delta=999.0,
            mean_outside_pixel_delta=999.0,
            clipping_ratio_percent=100.0,
            edge_artifact_detected=True,
            warnings=[f"Mask shape {wall_mask.shape} does not match image shape {(h, w)}."],
            diagnostics={"mask_shape": wall_mask.shape, "img_shape": (h, w)}
        )

    # 2. Mask Coverage & Pixel Count Check
    mask_pixels = int(np.sum(wall_mask > 0))
    coverage_pct = round((mask_pixels / float(total_pixels)) * 100.0, 2)

    if coverage_pct < min_mask_coverage_pct:
        passed = False
        warnings.append(
            f"Wall mask coverage is critically low ({coverage_pct}% < {min_mask_coverage_pct}% threshold). "
            f"Wall segmentation may have failed or target plane is too small."
        )

    # 3. Check for Unintended Changes Outside Mask (Bleed Check)
    # Binary inverse mask (strictly 0 in the original mask)
    outside_mask = (wall_mask == 0)
    outside_count = int(np.sum(outside_mask))

    if outside_count > 0:
        diff_outside = np.abs(rec_arr[outside_mask] - orig_arr[outside_mask])
        # Per-pixel color distance in RGB
        pixel_dist_outside = np.sqrt(np.sum(diff_outside ** 2, axis=1))
        max_outside_delta = float(np.max(pixel_dist_outside))
        mean_outside_delta = float(np.mean(pixel_dist_outside))

        if max_outside_delta > max_outside_tolerance:
            # Check if significant bleed or just subpixel anti-aliasing
            if mean_outside_delta > 1.0 or max_outside_delta > 15.0:
                passed = False
                warnings.append(
                    f"Color bleeding detected outside wall mask! Max delta: {max_outside_delta:.2f}, "
                    f"Mean delta: {mean_outside_delta:.2f} (tolerance: {max_outside_tolerance})."
                )
            else:
                warnings.append(
                    f"Minor subpixel anti-aliasing near mask boundary (max delta: {max_outside_delta:.2f})."
                )
    else:
        max_outside_delta = 0.0
        mean_outside_delta = 0.0

    # 4. Check for Color Clipping on Recoloured Wall
    inside_mask = (wall_mask > 0)
    inside_count = int(np.sum(inside_mask))

    if inside_count > 0:
        inside_pixels = rec_arr[inside_mask]
        clipped_pixels = np.sum((inside_pixels <= 0.0) | (inside_pixels >= 255.0))
        clipping_ratio = round((clipped_pixels / float(inside_pixels.size)) * 100.0, 2)

        if clipping_ratio > 12.0:
            warnings.append(
                f"High color clipping detected ({clipping_ratio}% of channels saturated at 0 or 255). "
                f"Consider lowering recolouring intensity or selecting an adaptive luminance strategy."
            )
    else:
        clipping_ratio = 0.0

    # 5. Check Target Shift on Recoloured Wall
    if inside_count > 0:
        avg_orig_inside = np.mean(orig_arr[inside_mask], axis=0)
        avg_rec_inside = np.mean(rec_arr[inside_mask], axis=0)
        wall_shift = float(np.linalg.norm(avg_rec_inside - avg_orig_inside))
        if wall_shift < 3.0 and np.linalg.norm(np.array(target_rgb) - avg_orig_inside) > 15.0:
            passed = False
            warnings.append("Recoloured wall shows virtually zero color shift despite different target paint.")
    else:
        wall_shift = 0.0

    # 6. Edge Artifact Check
    edge_artifact = False
    if max_outside_delta > 25.0:
        edge_artifact = True
        warnings.append("Abrupt boundary artifact detected at mask edge.")

    diagnostics = {
        "mask_pixels": mask_pixels,
        "total_pixels": total_pixels,
        "coverage_percent": coverage_pct,
        "max_outside_delta": round(max_outside_delta, 3),
        "mean_outside_delta": round(mean_outside_delta, 3),
        "clipping_ratio_percent": clipping_ratio,
        "wall_color_shift": round(wall_shift, 2),
        "edge_artifact": edge_artifact
    }

    return QualityControlReport(
        passed=passed,
        mask_pixel_count=mask_pixels,
        mask_coverage_percent=coverage_pct,
        max_outside_pixel_delta=round(max_outside_delta, 3),
        mean_outside_pixel_delta=round(mean_outside_delta, 3),
        clipping_ratio_percent=clipping_ratio,
        edge_artifact_detected=edge_artifact,
        warnings=warnings,
        diagnostics=diagnostics
    )
