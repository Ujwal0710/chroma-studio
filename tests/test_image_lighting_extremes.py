"""Tests verifying pipeline resilience across bright, dark, and cluttered room photos."""
import numpy as np
from PIL import Image
import io

from modules.image_validation import validate_image_bytes
from modules.colour_extraction import extract_dominant_colors
from modules.wall_segmentation import generate_wall_mask
from modules.palette_engine import generate_recommended_palettes
from modules.room_analysis import analyze_room_photograph
from modules.daylight_simulator import simulate_daylight_lighting
from modules.material_palettes import evaluate_material_compatibility


def create_jpeg_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_bright_room_photo():
    """Verify processing on a high-key, bright room image."""
    # High luminance pixels (mean > 210)
    rng = np.random.RandomState(101)
    arr = rng.randint(200, 255, size=(320, 480, 3), dtype=np.uint8)
    # Add a slightly warmer feature area
    arr[180:, 100:300, :] = [240, 220, 190]
    img = Image.fromarray(arr)
    raw_bytes = create_jpeg_bytes(img)

    # 1. Validation
    orig_pil, proc_pil, meta = validate_image_bytes(raw_bytes)
    assert meta["width"] == 480
    assert meta["height"] == 320

    # 2. Dominant color extraction
    extracted = extract_dominant_colors(proc_pil, num_colors=5)
    assert len(extracted.dominant_colors) == 5
    assert sum(s.percentage for s in extracted.dominant_colors) == 100.0
    assert extracted.overall_brightness > 0.65

    # 3. Room analysis
    analysis = analyze_room_photograph(proc_pil, extracted_analysis=extracted)
    assert analysis.brightness_level == "bright"
    assert "Not detected" in analysis.detected_room_type or analysis.detected_room_type

    # 4. Palette generation
    palettes = generate_recommended_palettes(extracted, analysis)
    assert len(palettes) >= 4
    for p in palettes:
        assert p.primary_wall.percentage == 60.0
        assert p.secondary_wall.percentage == 30.0
        assert p.accent.percentage == 10.0

    # 5. Wall segmentation
    mask, mask_meta = generate_wall_mask(proc_pil, sensitivity=0.55)
    assert mask.shape == (320, 480)
    assert mask_meta["wall_coverage_percent"] >= 0.0


def test_dark_room_photo():
    """Verify processing on a low-light, moody room image."""
    rng = np.random.RandomState(202)
    # Low luminance pixels (mean ~ 50)
    arr = rng.randint(15, 80, size=(320, 480, 3), dtype=np.uint8)
    # Add a dim warm accent light
    arr[60:120, 350:420, :] = [130, 95, 45]
    img = Image.fromarray(arr)
    raw_bytes = create_jpeg_bytes(img)

    orig_pil, proc_pil, meta = validate_image_bytes(raw_bytes)
    extracted = extract_dominant_colors(proc_pil, num_colors=5)
    assert len(extracted.dominant_colors) == 5
    assert sum(s.percentage for s in extracted.dominant_colors) == 100.0
    assert extracted.overall_brightness < 0.35

    analysis = analyze_room_photograph(proc_pil, extracted_analysis=extracted)
    assert analysis.brightness_level == "dim"

    palettes = generate_recommended_palettes(extracted, analysis)
    assert len(palettes) >= 4

    mask, mask_meta = generate_wall_mask(proc_pil, sensitivity=0.60)
    assert mask.shape == (320, 480)


def test_cluttered_textured_room_photo():
    """Verify processing on a high-entropy, cluttered room image with multiple materials."""
    rng = np.random.RandomState(303)
    # Multiple distinct texture patches
    arr = np.zeros((360, 480, 3), dtype=np.uint8)
    # Wall top
    arr[:180, :, :] = [215, 205, 190]
    # Flooring
    arr[260:, :, :] = [140, 90, 55]
    # Clutter / furniture blocks
    for _ in range(12):
        y = rng.randint(140, 260)
        x = rng.randint(40, 420)
        h, w = rng.randint(20, 60), rng.randint(30, 80)
        color = rng.randint(40, 220, size=3)
        arr[y:min(360, y+h), x:min(480, x+w), :] = color

    img = Image.fromarray(arr)
    raw_bytes = create_jpeg_bytes(img)

    orig_pil, proc_pil, meta = validate_image_bytes(raw_bytes)
    extracted = extract_dominant_colors(proc_pil, num_colors=7)
    assert len(extracted.dominant_colors) == 7
    assert sum(s.percentage for s in extracted.dominant_colors) == 100.0

    analysis = analyze_room_photograph(proc_pil, extracted_analysis=extracted)
    palettes = generate_recommended_palettes(extracted, analysis)
    assert len(palettes) >= 4

    # Test daylight simulator on room image
    sim_img = simulate_daylight_lighting(proc_pil, condition_name="Warm Morning Light")
    assert sim_img.size == proc_pil.size

    # Test material compatibility
    score_delta, notes = evaluate_material_compatibility(["Oak Wood", "Raw Concrete"], palettes[0])
    assert isinstance(score_delta, (int, float))
    assert len(notes) > 0
