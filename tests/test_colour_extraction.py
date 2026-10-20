"""Tests for colour extraction, K-Means clustering, RGB/HEX conversions, and color spaces."""
import numpy as np
from PIL import Image
from modules.image_processing import (
    rgb_to_hex,
    hex_to_rgb,
    calculate_perceptual_luminance,
    rgb_to_hsv,
    hsv_to_rgb,
    rgb_to_cielab,
    classify_color_characteristics
)
from modules.colour_extraction import extract_dominant_colors, match_color_name


def test_hex_and_rgb_conversions():
    """Requirement 4: HEX and RGB conversions are correct."""
    test_cases = [
        ((255, 255, 255), "#FFFFFF"),
        ((0, 0, 0), "#000000"),
        ((114, 86, 64), "#725640"),
        ((185, 132, 104), "#B98468"),
        ((245, 240, 232), "#F5F0E8"),
        ((48, 39, 31), "#30271F")
    ]
    for rgb, expected_hex in test_cases:
        assert rgb_to_hex(rgb[0], rgb[1], rgb[2]) == expected_hex
        assert hex_to_rgb(expected_hex) == rgb


def test_color_characteristics_classification():
    """Test classification of warm/cool/neutral and saturation."""
    # Warm tone (Terracotta / Red-Orange)
    c_warm = classify_color_characteristics(205, 125, 85)
    assert c_warm["temperature"] == "warm"

    # Cool tone (Slate Blue)
    c_cool = classify_color_characteristics(70, 95, 120)
    assert c_cool["temperature"] == "cool"

    # Neutral tone (Greige / White)
    c_neutral = classify_color_characteristics(220, 218, 215)
    assert c_neutral["saturation"] == "neutral"


def test_perceptual_luminance():
    """Verify perceptual luminance calculations."""
    # White should be 1.0, black should be 0.0
    assert abs(calculate_perceptual_luminance(255, 255, 255) - 1.0) < 0.01
    assert abs(calculate_perceptual_luminance(0, 0, 0) - 0.0) < 0.01
    # Green is perceptually brighter than blue
    lum_green = calculate_perceptual_luminance(0, 255, 0)
    lum_blue = calculate_perceptual_luminance(0, 0, 255)
    assert lum_green > lum_blue


def test_dominant_colors_extraction_from_known_image():
    """Requirement 3: Dominant colours are extracted from a known test image."""
    # Create synthetic test room image:
    # 60% Alabaster Wall (240, 235, 225)
    # 30% Warm Hardwood (160, 110, 70)
    # 10% Accent Sage (120, 140, 110)
    width, height = 300, 300
    arr = np.zeros((height, width, 3), dtype=np.uint8)

    # 60% height wall
    h_wall = int(height * 0.60)
    arr[:h_wall, :, :] = [240, 235, 225]

    # 30% height floor
    h_floor = int(height * 0.90)
    arr[h_wall:h_floor, :, :] = [160, 110, 70]

    # 10% accent
    arr[h_floor:, :, :] = [120, 140, 110]

    test_img = Image.fromarray(arr)
    extracted = extract_dominant_colors(test_img, num_colors=3, filter_extremes=False)

    assert len(extracted.dominant_colors) == 3
    # Check that highest percentage cluster corresponds to the wall color
    top_swatch = extracted.dominant_colors[0]
    assert top_swatch.percentage > 45.0
    # Top swatch RGB should be very close to [240, 235, 225]
    assert abs(top_swatch.rgb[0] - 240) < 15
    assert abs(top_swatch.rgb[1] - 235) < 15
    assert abs(top_swatch.rgb[2] - 225) < 15

    # Check overall lighting and temperature
    assert extracted.overall_brightness > 0.40
    assert extracted.neutral_count >= 1 or extracted.warm_count >= 1
    assert "white balance" in extracted.analysis_disclaimer.lower()
