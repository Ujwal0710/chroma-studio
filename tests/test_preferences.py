"""Tests for user preference controls, avoid colors penalty, and accent intensities."""
from models.schemas import PreferenceSettings
from modules.palette_engine import generate_recommended_palettes
from tests.test_palette_engine import get_mock_extracted, get_mock_room_analysis


def test_avoid_color_penalizes_score():
    """Verify that specifying a color to avoid lowers the score of offending palettes."""
    extracted = get_mock_extracted()
    room_analysis = get_mock_room_analysis()

    # Base preferences
    pref_normal = PreferenceSettings()
    palettes_normal = generate_recommended_palettes(extracted, room_analysis, pref_normal)

    # Preferences avoiding 'Terracotta'
    pref_avoid_terracotta = PreferenceSettings(colors_to_avoid=["Terracotta", "Warm"])
    palettes_avoid = generate_recommended_palettes(extracted, room_analysis, pref_avoid_terracotta)

    # The Bold Accent / Terracotta concept score should be lower under avoid settings
    p_norm_bold = next(p for p in palettes_normal if "Bold Accent" in p.concept_category)
    p_avoid_bold = next(p for p in palettes_avoid if "Bold Accent" in p.concept_category)

    assert p_avoid_bold.heuristic_score < p_norm_bold.heuristic_score


def test_accent_intensity_affects_accent_saturation():
    """Verify that Accent Intensity control ('Subtle' vs 'Bold') modifies accent vibrancy."""
    extracted = get_mock_extracted()
    room_analysis = get_mock_room_analysis()

    pref_subtle = PreferenceSettings(accent_intensity="Subtle")
    palettes_subtle = generate_recommended_palettes(extracted, room_analysis, pref_subtle)

    pref_bold = PreferenceSettings(accent_intensity="Bold")
    palettes_bold = generate_recommended_palettes(extracted, room_analysis, pref_bold)

    p_sub = next(p for p in palettes_subtle if "Modern Neutral" in p.concept_category)
    p_bld = next(p for p in palettes_bold if "Modern Neutral" in p.concept_category)

    # Bold accent should have greater saturation or luminance contrast
    assert p_bld.accent.rgb != p_sub.accent.rgb
