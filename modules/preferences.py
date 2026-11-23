"""Preference options, presets, and validation logic."""
from models.schemas import PreferenceSettings


ATMOSPHERE_OPTIONS = [
    "Calm & Relaxing",
    "Warm & Cozy",
    "Modern & Sophisticated",
    "Energetic & Uplifting",
    "Luxurious & Dramatic"
]

TEMPERATURE_OPTIONS = [
    "Balanced / Neutral",
    "Warm",
    "Cool"
]

LIGHTNESS_OPTIONS = [
    "Light & Airy",
    "Mid-Tone Balanced",
    "Deep & Moody"
]

COLORFULNESS_OPTIONS = [
    "Balanced Color",
    "Subtle & Neutral",
    "Vibrant & Saturated"
]

ACCENT_INTENSITY_OPTIONS = [
    "Moderate",
    "Subtle",
    "Bold"
]

BUDGET_OPTIONS = [
    "Mid-range",
    "Budget-friendly",
    "Premium / Designer"
]

COMMON_ACCENT_HUES = [
    "Sage Green",
    "Earthy Olive",
    "Terracotta",
    "Desert Sand",
    "Coastal Mist Blue",
    "Nordic Slate Blue",
    "Antique Brass / Gold",
    "Warm Greige",
    "Charcoal Slate",
    "Deep Pine",
    "Muted Wine / Burgundy"
]


def create_default_preferences(
    room_type: str = "Automatic Detection",
    interior_style: str = "Automatic Detection"
) -> PreferenceSettings:
    """Create default initial preference configuration."""
    return PreferenceSettings(
        room_type=room_type,
        interior_style=interior_style,
        temperature_preference="Balanced / Neutral",
        lightness_preference="Light & Airy",
        colorfulness_preference="Balanced Color",
        desired_atmosphere="Calm & Relaxing",
        accent_intensity="Moderate",
        preferred_colors=[],
        colors_to_avoid=[],
        furniture_flooring_constraints="None specified",
        budget_category="Mid-range"
    )
