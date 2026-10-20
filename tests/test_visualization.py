"""Tests for wall segmentation, recolouring pipeline, and outside-mask pixel preservation."""
import numpy as np
from PIL import Image

from modules.wall_segmentation import generate_wall_mask
from modules.room_visualization import (
    apply_luminance_preserving_recolour,
    create_side_by_side_comparison,
    create_split_slider_comparison,
    create_mask_overlay_preview,
    LUMINANCE_STRATEGIES
)


def test_wall_segmentation_pipeline():
    """Verify wall segmentation generates valid binary mask and coverage metadata."""
    # Synthetic room: top half is plain light wall, bottom half is dark wood floor
    h, w = 200, 200
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:120, :, :] = [230, 220, 210]  # Wall
    arr[120:, :, :] = [80, 50, 30]     # Floor

    img = Image.fromarray(arr)
    mask, meta = generate_wall_mask(img, sensitivity=0.6, upper_bias=0.7)

    assert mask.shape == (h, w)
    assert mask.dtype == np.uint8
    # Top region should have wall detected
    assert np.sum(mask[:100, :]) > 0
    # Bottom floor region should be suppressed
    assert np.sum(mask[150:, :]) == 0
    assert meta["wall_coverage_percent"] > 0.0


def test_recolour_changes_intended_pixels():
    """Requirement 8: Local wall recolouring changes the intended pixels."""
    h, w = 100, 100
    # Original gray wall image
    original_arr = np.full((h, w, 3), 180, dtype=np.uint8)
    original_img = Image.fromarray(original_arr)

    # Define a rectangular wall mask in the center
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[20:80, 20:80] = 255  # 60x60 square

    # Target paint color: Terracotta (205, 100, 50)
    target_rgb = (205, 100, 50)

    # Apply recolouring with feather_radius=0 to test exact pixel bounding
    recoloured = apply_luminance_preserving_recolour(
        original_img=original_img,
        wall_mask=mask,
        target_rgb=target_rgb,
        intensity=1.0,
        feather_radius=0
    )
    rec_arr = np.array(recoloured)

    # In center of mask, pixels MUST have changed significantly from original (180, 180, 180)
    center_pixel = rec_arr[50, 50]
    assert not np.array_equal(center_pixel, [180, 180, 180])
    # The red channel should be dominant (Terracotta)
    assert center_pixel[0] > center_pixel[1] > center_pixel[2]


def test_outside_mask_pixels_remain_unchanged():
    """Requirement 9: Pixels outside a test wall mask remain unchanged (zero tolerance without feathering)."""
    h, w = 100, 100
    original_arr = np.full((h, w, 3), 128, dtype=np.uint8)
    original_img = Image.fromarray(original_arr)

    # Wall mask occupying top half only
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[:50, :] = 255

    target_rgb = (220, 80, 80)  # Bright red

    # Recolour with feather_radius=0 for strict boundary check
    recoloured = apply_luminance_preserving_recolour(
        original_img=original_img,
        wall_mask=mask,
        target_rgb=target_rgb,
        intensity=1.0,
        feather_radius=0
    )
    rec_arr = np.array(recoloured)

    # Pixels in the bottom half (mask == 0) MUST be exactly 128 (0 tolerance)
    outside_region = rec_arr[50:, :]
    expected_outside = original_arr[50:, :]
    assert np.array_equal(outside_region, expected_outside), "Outside-mask pixels were inadvertently modified!"


def test_side_by_side_and_split_slider_generation():
    """Verify side-by-side and split slider composite generations."""
    w, h = 120, 90
    img1 = Image.new("RGB", (w, h), (200, 200, 200))
    img2 = Image.new("RGB", (w, h), (100, 100, 100))

    # Side-by-side
    sbs = create_side_by_side_comparison(img1, img2, paint_name="Warm Linen")
    assert sbs.width >= w * 2
    assert sbs.height > h

    # Split slider
    split = create_split_slider_comparison(img1, img2, split_ratio=0.5)
    assert split.size == (w, h)

    # Mask overlay
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[:40, :] = 255
    overlay = create_mask_overlay_preview(img1, mask)
    assert overlay.size == (w, h)


def test_luminance_strategies_definition_and_switching():
    """Verify LUMINANCE_STRATEGIES is exported, contains valid labels, and modifies recolouring."""
    assert isinstance(LUMINANCE_STRATEGIES, dict)
    expected_keys = {"cielab_perceptual", "adaptive_luminance", "architectural_glaze"}
    assert set(LUMINANCE_STRATEGIES.keys()) == expected_keys

    # Verify that each strategy modifies the image in a distinct manner
    img = Image.new("RGB", (80, 80), (220, 210, 200))
    mask = np.full((80, 80), 255, dtype=np.uint8)
    target = (180, 90, 60)

    res_cielab = np.array(apply_luminance_preserving_recolour(img, mask, target, strategy="cielab_perceptual"))
    res_adapt = np.array(apply_luminance_preserving_recolour(img, mask, target, strategy="adaptive_luminance"))
    res_glaze = np.array(apply_luminance_preserving_recolour(img, mask, target, strategy="architectural_glaze"))

    # All three must produce distinct pixel arrays
    assert not np.array_equal(res_cielab, res_adapt)
    assert not np.array_equal(res_cielab, res_glaze)
    assert not np.array_equal(res_adapt, res_glaze)
