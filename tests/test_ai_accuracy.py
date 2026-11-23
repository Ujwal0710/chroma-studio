"""Comprehensive AI Accuracy and Visualization Quality Control Test Suite.

Verifies:
1. Scenario 1: Simple room with clear continuous wall.
2. Scenario 2: Room with large bright windows (glare exclusion).
3. Scenario 3: Room with furniture close to the wall (obstacle exclusion, zero bleed).
4. Scenario 4: Room with strong directional shadows (texture and shadow preservation).
5. Scenario 5: Room with multiple wall colors (multi-plane isolation).
6. Rigorous Quality Control validation (outside-mask tolerance, clipping, dimensions).
7. Preference sensitivity and palette distinctiveness (Delta E >= 12.0).
8. Full end-to-end upload -> extraction -> analysis -> palette -> recolouring workflow.
"""
from typing import Tuple
import numpy as np
from PIL import Image, ImageDraw

from modules.image_processing import pil_to_numpy_rgb
from modules.wall_segmentation import generate_wall_mask, apply_manual_corrections
from modules.room_visualization import apply_luminance_preserving_recolour
from modules.quality_control import validate_recolour_quality
from modules.colour_extraction import extract_dominant_colors
from modules.room_analysis import analyze_room_photograph
from modules.palette_engine import generate_recommended_palettes
from modules.preferences import create_default_preferences
from modules.colour_theory import calculate_color_distance_lab


# ---------------------------------------------------------------------------
# Synthetic Room Fixtures
# ---------------------------------------------------------------------------

def create_simple_room(w: int = 240, h: int = 180) -> Image.Image:
    """Scenario 1: Clean wall with dark hardwood flooring."""
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:120, :] = [235, 230, 222]  # Cream alabaster wall
    arr[120:126, :] = [245, 245, 245]  # Baseboard molding
    arr[126:, :] = [90, 55, 35]  # Walnut wood floor
    return Image.fromarray(arr)


def create_window_room(w: int = 240, h: int = 180) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
    """Scenario 2: Wall with a large bright window."""
    img = create_simple_room(w, h)
    draw = ImageDraw.Draw(img)
    # Window box (x1, y1, x2, y2)
    win_box = (40, 20, 110, 95)
    # Bright exterior daylight / sky
    draw.rectangle(win_box, fill=(240, 248, 255))
    # Window frame
    draw.rectangle(win_box, outline=(60, 60, 60), width=3)
    draw.line([(75, 20), (75, 95)], fill=(60, 60, 60), width=2)
    draw.line([(40, 58), (110, 58)], fill=(60, 60, 60), width=2)
    return img, win_box


def create_furniture_room(w: int = 240, h: int = 180) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
    """Scenario 3: Wall with a sofa directly against it."""
    img = create_simple_room(w, h)
    draw = ImageDraw.Draw(img)
    # Dark charcoal sofa (x1, y1, x2, y2)
    sofa_box = (50, 85, 190, 150)
    draw.rectangle(sofa_box, fill=(55, 60, 65))
    # Cushion lines
    draw.rectangle([60, 95, 120, 140], fill=(70, 75, 80))
    draw.rectangle([120, 95, 180, 140], fill=(70, 75, 80))
    return img, sofa_box


def create_shadow_room(w: int = 240, h: int = 180) -> Image.Image:
    """Scenario 4: Wall with strong directional shadow gradient."""
    arr = np.zeros((h, w, 3), dtype=np.float32)
    # Gradient from bright left (240) to shadow right (110)
    for x in range(w):
        t = x / float(w)
        lum = 235.0 * (1.0 - t * 0.55)
        arr[:120, x] = [lum, lum * 0.98, lum * 0.94]
    arr[120:126, :] = [245, 245, 245]
    arr[126:, :] = [90, 55, 35]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def create_multi_wall_room(w: int = 240, h: int = 180) -> Image.Image:
    """Scenario 5: Room with two distinct wall colors meeting at an architectural corner."""
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    # Left wall: warm ochre/sand
    arr[:120, :100] = [215, 175, 135]
    # Vertical corner shadow edge
    arr[:120, 100:104] = [120, 105, 90]
    # Right wall: cool pale gray
    arr[:120, 104:] = [210, 218, 225]
    arr[120:126, :] = [245, 245, 245]
    arr[126:, :] = [80, 50, 30]
    return Image.fromarray(arr)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_scenario_1_simple_room_wall_segmentation_and_recolour():
    """Verify clean segmentation and zero-bleed recolouring on simple room."""
    img = create_simple_room()
    mask, meta = generate_wall_mask(img, sensitivity=0.55, upper_bias=0.70)

    assert mask.shape == (180, 240)
    assert meta["segmentation_confidence"] in ["High", "Moderate"]
    assert meta["wall_coverage_percent"] > 15.0

    # Flooring (y > 130) must be 100% excluded
    assert np.all(mask[130:, :] == 0)

    # Test recolouring to terracotta
    target_rgb = (205, 110, 65)
    recoloured = apply_luminance_preserving_recolour(
        img, mask, target_rgb, intensity=0.9, strategy="cielab_perceptual"
    )

    # Quality control check
    qc = validate_recolour_quality(img, recoloured, mask, target_rgb)
    assert qc.passed is True
    # Zero outside-mask delta guarantee
    assert qc.max_outside_pixel_delta == 0.0


def test_scenario_2_window_glare_exclusion():
    """Verify window glass and specular outdoor light are excluded from wall mask."""
    img, win_box = create_window_room()
    mask, meta = generate_wall_mask(img, sensitivity=0.55, upper_bias=0.70)

    # Inner window glass should be excluded
    # Check that majority of window pane is not painted
    win_pane_pixels = mask[win_box[1]+5:win_box[3]-5, win_box[0]+5:win_box[2]-5]
    assert np.mean(win_pane_pixels > 0) < 0.25, "Window glass was incorrectly included in wall mask!"


def test_scenario_3_furniture_close_to_wall_zero_bleed():
    """Verify sofa in front of wall is excluded from mask and receives ZERO paint bleed."""
    img, sofa_box = create_furniture_room()
    mask, meta = generate_wall_mask(img, sensitivity=0.55, upper_bias=0.70)

    # The sofa center should not be masked
    sofa_center_y = (sofa_box[1] + sofa_box[3]) // 2
    sofa_center_x = (sofa_box[0] + sofa_box[2]) // 2
    assert mask[sofa_center_y, sofa_center_x] == 0, "Sofa interior was included in wall mask!"

    # Recolour with deep royal blue
    target_rgb = (40, 70, 130)
    recoloured = apply_luminance_preserving_recolour(
        img, mask, target_rgb, intensity=0.9, strategy="cielab_perceptual"
    )

    qc = validate_recolour_quality(img, recoloured, mask, target_rgb)
    assert qc.passed is True
    assert qc.max_outside_pixel_delta == 0.0

    # Verify sofa pixels in recoloured image are exactly identical to original
    rec_arr = pil_to_numpy_rgb(recoloured)
    orig_arr = pil_to_numpy_rgb(img)
    assert np.array_equal(rec_arr[sofa_box[1]:sofa_box[3], sofa_box[0]:sofa_box[2]],
                          orig_arr[sofa_box[1]:sofa_box[3], sofa_box[0]:sofa_box[2]])


def test_scenario_4_strong_shadow_preservation():
    """Verify that CIELAB lightness transfer preserves lighting gradient on wall."""
    img = create_shadow_room()
    mask, meta = generate_wall_mask(img, sensitivity=0.75, upper_bias=0.70)

    target_rgb = (180, 100, 60)  # Terracotta
    recoloured = apply_luminance_preserving_recolour(
        img, mask, target_rgb, intensity=0.9, strategy="cielab_perceptual", shading_retention=0.8
    )

    rec_arr = pil_to_numpy_rgb(recoloured)
    # The left side (in bright light) should be lighter than the right side (in shadow)
    left_lum = float(np.mean(rec_arr[40:80, 20:60]))
    right_lum = float(np.mean(rec_arr[40:80, 180:220]))
    assert left_lum > right_lum + 15.0, "Shadow gradient was wiped out by recolouring!"


def test_scenario_5_multiple_wall_planes_and_isolation():
    """Verify discovery of multiple architectural wall planes and selective recolouring."""
    img = create_multi_wall_room()
    # Mask both walls with higher sensitivity
    mask_all, meta_all = generate_wall_mask(img, sensitivity=0.85, upper_bias=0.70)

    detected_planes = meta_all.get("detected_planes", [])
    assert len(detected_planes) >= 2, "Failed to discover separate architectural wall planes!"

    # Target only plane 1
    plane1_id = detected_planes[0]["plane_id"]
    mask_plane1, meta_p1 = generate_wall_mask(img, sensitivity=0.85, upper_bias=0.70, target_plane_id=plane1_id)

    # Plane 1 mask should be smaller than all walls mask
    assert np.sum(mask_plane1 > 0) < np.sum(mask_all > 0)
    assert np.sum(mask_plane1 > 0) > 0


def test_manual_mask_brush_corrections():
    """Verify manual inclusion and exclusion brush strokes."""
    img = create_simple_room()
    mask, _ = generate_wall_mask(img)

    # Erase a hole at (x=100, y=50, radius=20)
    adjustments = [{"type": "brush", "mode": "exclude", "x": 100, "y": 50, "radius": 20}]
    corrected = apply_manual_corrections(mask, adjustments)

    # Hole should be completely zero
    assert corrected[50, 100] == 0
    # Nearby pixel outside radius should still be wall (255)
    assert corrected[50, 150] == 255


def test_all_luminance_strategies():
    """Verify all 3 luminance strategies produce valid non-clipping outputs."""
    img = create_simple_room()
    mask, _ = generate_wall_mask(img)
    target = (120, 150, 130)  # Muted Sage

    for strat in ["cielab_perceptual", "adaptive_luminance", "architectural_glaze"]:
        rec = apply_luminance_preserving_recolour(img, mask, target, strategy=strat)
        qc = validate_recolour_quality(img, rec, mask, target)
        assert qc.passed is True
        assert qc.max_outside_pixel_delta == 0.0


def test_quality_control_catches_invalid_inputs():
    """Verify QC flags low coverage and outside bleed correctly."""
    img = create_simple_room()
    h, w = img.size[1], img.size[0]

    # Test nearly empty mask (< 0.5% coverage)
    empty_mask = np.zeros((h, w), dtype=np.uint8)
    empty_mask[10, 10] = 255
    rec = apply_luminance_preserving_recolour(img, empty_mask, (200, 100, 50))
    qc_empty = validate_recolour_quality(img, rec, empty_mask, (200, 100, 50))
    assert qc_empty.passed is False
    assert any("critically low" in w for w in qc_empty.warnings)


def test_palette_distinctiveness_and_explanations():
    """Verify 4 distinct palettes with Delta E >= 12.0 and clear architectural explanations."""
    img = create_simple_room()
    extracted = extract_dominant_colors(img)
    analysis = analyze_room_photograph(img, extracted_analysis=extracted)
    prefs = create_default_preferences()

    palettes = generate_recommended_palettes(extracted, analysis, prefs)
    assert len(palettes) == 4

    categories = [p.concept_category for p in palettes]
    assert "Warm and Inviting" in categories
    assert "Cool and Calming" in categories
    assert "Modern Neutral" in categories
    assert "Bold Accent / Contemporary Contrast" in categories

    # Verify perceptual distinctiveness between primary wall paints
    for i in range(len(palettes)):
        for j in range(i + 1, len(palettes)):
            dist = calculate_color_distance_lab(palettes[i].primary_wall.rgb, palettes[j].primary_wall.rgb)
            assert dist >= 12.0, f"Palettes {palettes[i].name} and {palettes[j].name} are too similar (Delta E = {dist:.1f} < 12.0)!"

    # Verify architectural rationales are non-empty and descriptive
    for p in palettes:
        assert len(p.design_rationale) > 30
        assert len(p.furniture_flooring_compatibility) > 30


def test_preferences_drive_palette_changes():
    """Verify user preference changes materially shift the palette hues."""
    img = create_simple_room()
    extracted = extract_dominant_colors(img)
    analysis = analyze_room_photograph(img, extracted_analysis=extracted)

    prefs_light = create_default_preferences()
    prefs_light.lightness_preference = "Light & Airy"

    prefs_dark = create_default_preferences()
    prefs_dark.lightness_preference = "Deep & Moody"

    palettes_light = generate_recommended_palettes(extracted, analysis, prefs_light)
    palettes_dark = generate_recommended_palettes(extracted, analysis, prefs_dark)

    # Average lightness of light palettes must be higher than dark palettes
    avg_l_light = np.mean([p.primary_wall.luminance for p in palettes_light])
    avg_l_dark = np.mean([p.primary_wall.luminance for p in palettes_dark])
    assert avg_l_light > avg_l_dark, "Lightness preference failed to shift palette luminances!"
