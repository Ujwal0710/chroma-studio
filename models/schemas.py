"""Data schemas and Pydantic models for AI Interior Colour Palette Suggester."""
from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel, Field


class ColorSwatch(BaseModel):
    hex: str
    rgb: Tuple[int, int, int]
    role: str = "Color"
    name: Optional[str] = None
    percentage: Optional[float] = None
    temperature: Optional[str] = None  # 'warm', 'cool', 'neutral'
    saturation_category: Optional[str] = None  # 'muted', 'neutral', 'saturated'
    luminance: Optional[float] = None
    description: Optional[str] = None


class PaletteConcept(BaseModel):
    id: str
    name: str
    concept_category: str  # 'Warm and Inviting', 'Cool and Calming', 'Modern Neutral', 'Bold Accent'
    harmony_type: str  # 'Complementary', 'Analogous', 'Monochromatic', 'Neutral and Accent'
    description: str
    atmosphere: str
    primary_wall: ColorSwatch
    secondary_wall: ColorSwatch
    accent: ColorSwatch
    trim: ColorSwatch
    proportions: Dict[str, str] = Field(default_factory=lambda: {
        "Primary Wall": "60%",
        "Secondary Wall / Trim": "30%",
        "Accent Details": "10%"
    })
    design_rationale: str
    furniture_flooring_compatibility: str
    heuristic_score: float = 0.0
    score_breakdown: Dict[str, float] = Field(default_factory=dict)

    def all_colors(self) -> List[ColorSwatch]:
        return [self.primary_wall, self.secondary_wall, self.accent, self.trim]


class ExtractedColorAnalysis(BaseModel):
    dominant_colors: List[ColorSwatch]
    overall_brightness: float  # 0.0 to 1.0
    overall_temperature_tendency: str  # 'warm', 'cool', 'neutral'
    mean_saturation: float
    neutral_count: int
    warm_count: int
    cool_count: int
    lighting_condition_estimate: str
    analysis_disclaimer: str = (
        "Note: Inherent camera white balance, exposure, reflections, artificial lighting, "
        "and compression artifacts can shift observed colour measurements from physical paint pigments."
    )


class RoomAnalysisResult(BaseModel):
    detected_room_type: str
    detected_style: str
    visible_materials: List[str] = Field(default_factory=list)
    existing_wall_description: str
    flooring_description: str
    dominant_color_observations: List[str] = Field(default_factory=list)
    apparent_lighting: str
    lighting_temperature: str = "neutral"
    brightness_level: str = "medium"
    design_strengths: List[str] = Field(default_factory=list)
    design_challenges: List[str] = Field(default_factory=list)
    recommended_direction: str
    confidence_notes: str
    is_ai_inferred: bool = False
    provider_name: str = "Local Computer Vision Fallback"


class PreferenceSettings(BaseModel):
    room_type: str = "Automatic Detection"
    interior_style: str = "Automatic Detection"
    temperature_preference: str = "Balanced / Neutral"  # 'Warm', 'Cool', 'Balanced / Neutral'
    lightness_preference: str = "Light & Airy"  # 'Light & Airy', 'Mid-Tone Balanced', 'Deep & Moody'
    colorfulness_preference: str = "Balanced Color"  # 'Subtle & Neutral', 'Balanced Color', 'Vibrant & Saturated'
    desired_atmosphere: str = "Calm & Relaxing"  # 'Calm & Relaxing', 'Warm & Cozy', 'Modern & Sophisticated', 'Energetic & Uplifting', 'Luxurious & Dramatic'
    accent_intensity: str = "Moderate"  # 'Subtle', 'Moderate', 'Bold'
    preferred_colors: List[str] = Field(default_factory=list)
    colors_to_avoid: List[str] = Field(default_factory=list)
    furniture_flooring_constraints: str = "None specified"
    budget_category: str = "Mid-range"  # 'Budget-friendly', 'Mid-range', 'Premium / Designer'


class SavedPaletteRecord(BaseModel):
    id: str
    name: str
    timestamp: str
    room_type: str
    interior_style: str
    palette_data: Dict[str, Any]
    preferences_data: Dict[str, Any]
    notes: Optional[str] = ""
    preview_image_path: Optional[str] = None
