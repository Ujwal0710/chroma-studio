"""Tests for colour extraction, K-Means clustering, RGB/HEX conversions, and color spaces."""
import numpy as np
from PIL import Image
from modules.image_processing import (
    rgb_to_hex,
    hex_to_rgb,
    calculate_perceptual_luminance,
    classify_color_characteristics
)
from modules.colour_extraction import extract_dominant_colors


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


def test_cielab_kmeans_exact_100_percent_sum():
    """Verify that CIELAB K-Means dominant color percentages sum to exactly 100.0%."""
    # Test on random RGB image
    rng = np.random.RandomState(42)
    random_pixels = rng.randint(20, 240, size=(120, 120, 3), dtype=np.uint8)
    img = Image.fromarray(random_pixels)

    for k in [3, 5, 7]:
        extracted = extract_dominant_colors(img, num_colors=k, filter_extremes=False)
        total_pct = sum(s.percentage for s in extracted.dominant_colors)
        assert round(total_pct, 1) == 100.0, f"Expected 100.0%, got {total_pct}% for k={k}"
        for s in extracted.dominant_colors:
            assert s.hex.startswith("#")
            assert len(s.hex) == 7
            for val in s.rgb:
                assert 0 <= val <= 255


def test_typology_not_detected_when_unspecified():
    """Verify that room typology does not silently default to Living Room."""
    from services.vision_provider import generate_local_rule_based_analysis
    img = Image.new("RGB", (100, 100), (220, 200, 180))
    extracted = extract_dominant_colors(img, num_colors=3)
    result = generate_local_rule_based_analysis(extracted, selected_room_type="Automatic Detection")
    assert "Not detected" in result.detected_room_type
    assert "Inferred default interior" not in result.detected_room_type


def test_dark_mode_and_no_sidebar_architecture():
    """Verify .streamlit/config.toml dark-only configuration and absence of st.sidebar in app.py."""
    import pathlib
    config_path = pathlib.Path(".streamlit/config.toml")
    assert config_path.exists(), ".streamlit/config.toml must exist"
    config_text = config_path.read_text(encoding="utf-8")
    assert 'base = "dark"' in config_text
    assert "#121411" in config_text

    app_text = pathlib.Path("app.py").read_text(encoding="utf-8")
    assert "with st.sidebar:" not in app_text, "st.sidebar must be removed from app.py"
    assert 'initial_sidebar_state="collapsed"' in app_text
    assert "st.tabs([" in app_text

