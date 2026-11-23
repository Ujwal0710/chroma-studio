"""Tests for palette recommendation engine, preferences responsiveness, and duplicate elimination."""
from PIL import Image
import numpy as np

from models.schemas import PreferenceSettings, ExtractedColorAnalysis, RoomAnalysisResult
from modules.colour_extraction import extract_dominant_colors
from modules.palette_engine import generate_recommended_palettes
from modules.colour_theory import calculate_palette_distance


def get_mock_extracted() -> ExtractedColorAnalysis:
    """Create deterministic extracted colors for testing."""
    arr = np.zeros((200, 200, 3), dtype=np.uint8)
    arr[:120, :, :] = [235, 225, 210]  # Light warm greige
    arr[120:170, :, :] = [140, 95, 60]  # Medium wood
    arr[170:, :, :] = [90, 115, 95]     # Sage
    img = Image.fromarray(arr)
    return extract_dominant_colors(img, num_colors=4, filter_extremes=False)


def get_mock_room_analysis() -> RoomAnalysisResult:
    """Create deterministic room analysis result."""
    return RoomAnalysisResult(
        detected_room_type="Living Room",
        detected_style="Modern Scandinavian",
        visible_materials=["Oak flooring", "Linen upholstery"],
        existing_wall_description="Warm greige wall baseline",
        flooring_description="Warm oak timber",
        dominant_color_observations=["Greige", "Oak", "Sage"],
        apparent_lighting="Moderate natural daylight",
        lighting_temperature="neutral",
        brightness_level="medium",
        design_strengths=["Balanced light"],
        design_challenges=["Low contrast"],
        recommended_direction="Elevate with harmonious warm and cool contrasts",
        confidence_notes="Deterministic test analysis",
        is_ai_inferred=False
    )


def test_palette_generation_contains_required_fields():
    """Requirement 5: Palette generation returns the required colour fields."""
    extracted = get_mock_extracted()
    room_analysis = get_mock_room_analysis()
    prefs = PreferenceSettings()

    palettes = generate_recommended_palettes(extracted, room_analysis, prefs)

    assert len(palettes) >= 4
    for p in palettes:
        assert p.id
        assert p.name
        assert p.concept_category in [
            "Warm and Inviting",
            "Cool and Calming",
            "Modern Neutral",
            "Bold Accent / Contemporary Contrast"
        ]
        assert p.harmony_type
        assert p.description
        assert p.atmosphere
        assert p.design_rationale
        assert p.furniture_flooring_compatibility

        # Required 4 colors
        assert p.primary_wall.hex.startswith("#")
        assert len(p.primary_wall.rgb) == 3
        assert p.primary_wall.role

        assert p.secondary_wall.hex.startswith("#")
        assert len(p.secondary_wall.rgb) == 3

        assert p.accent.hex.startswith("#")
        assert len(p.accent.rgb) == 3

        assert p.trim.hex.startswith("#")
        assert len(p.trim.rgb) == 3

        # Proportions
        assert "Primary Wall" in p.proportions
        assert p.heuristic_score > 0.0


def test_palettes_respond_to_user_preferences():
    """Requirement 6: Palette options respond to user preferences."""
    extracted = get_mock_extracted()
    room_analysis = get_mock_room_analysis()

    # Preference 1: Warm & Airy
    pref_warm_light = PreferenceSettings(
        temperature_preference="Warm",
        lightness_preference="Light & Airy"
    )
    palettes_warm = generate_recommended_palettes(extracted, room_analysis, pref_warm_light)

    # Preference 2: Cool & Moody
    pref_cool_dark = PreferenceSettings(
        temperature_preference="Cool",
        lightness_preference="Deep & Moody"
    )
    palettes_cool = generate_recommended_palettes(extracted, room_analysis, pref_cool_dark)

    # Compare primary walls of the top-ranked palettes
    p_warm_top = palettes_warm[0]
    p_cool_top = palettes_cool[0]

    # Verify that warm preference yields higher red/blue ratio than cool preference
    warm_rb_ratio = p_warm_top.primary_wall.rgb[0] / max(1, p_warm_top.primary_wall.rgb[2])
    cool_rb_ratio = p_cool_top.primary_wall.rgb[0] / max(1, p_cool_top.primary_wall.rgb[2])
    assert warm_rb_ratio > cool_rb_ratio

    # Verify lightness effect: Light & Airy should have higher luminance than Deep & Moody
    assert p_warm_top.primary_wall.luminance > p_cool_top.primary_wall.luminance


def test_duplicate_palette_elimination():
    """Requirement 7: Duplicate palette detection works."""
    extracted = get_mock_extracted()
    room_analysis = get_mock_room_analysis()
    prefs = PreferenceSettings()

    palettes = generate_recommended_palettes(extracted, room_analysis, prefs)

    # Calculate pairwise distances between all palettes
    for i in range(len(palettes)):
        for j in range(i + 1, len(palettes)):
            p_i_colors = [c.rgb for c in palettes[i].all_colors()]
            p_j_colors = [c.rgb for c in palettes[j].all_colors()]
            dist = calculate_palette_distance(p_i_colors, p_j_colors)
            # Distance should exceed minimum duplicate threshold (Delta E >= 6.0)
            assert dist >= 6.0, f"Palettes {palettes[i].name} and {palettes[j].name} are too similar (dist={dist})"
