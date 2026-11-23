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
    colors: List[ColorSwatch] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.colors and hasattr(self, "primary_wall") and hasattr(self, "secondary_wall") and hasattr(self, "accent") and hasattr(self, "trim"):
            self.colors = [self.primary_wall, self.secondary_wall, self.accent, self.trim]

    def all_colors(self) -> List[ColorSwatch]:
        return self.colors if self.colors else [self.primary_wall, self.secondary_wall, self.accent, self.trim]


class ExtractedColorAnalysis(BaseModel):
    dominant_colors: List[ColorSwatch]
    overall_brightness: float  # 0.0 to 1.0
    overall_temperature_tendency: str  # 'warm', 'cool', 'neutral'
    mean_saturation: float
    neutral_count: int
    warm_count: int
    cool_count: int
    lighting_condition_estimate: str = "Neutral Balanced Lighting"
    analysis_disclaimer: str = (
        "Note: Inherent camera white balance, exposure, reflections, artificial lighting, "
        "and compression artifacts can shift observed colour measurements from physical paint pigments."
    )


class RoomAnalysisResult(BaseModel):
    detected_room_type: str
    detected_style: str
    visible_materials: List[str] = Field(default_factory=list)
    visible_furniture: List[str] = Field(default_factory=list)
    existing_wall_description: str
    flooring_description: str
    dominant_color_observations: List[str] = Field(default_factory=list)
    apparent_lighting: str
    lighting_temperature: str = "neutral"
    brightness_level: str = "medium"
    design_strengths: List[str] = Field(default_factory=list)
    design_challenges: List[str] = Field(default_factory=list)
    compatibility_constraints: List[str] = Field(default_factory=list)
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
    user_id: Optional[str] = "default_user"


class UserProfile(BaseModel):
    user_id: str
    display_name: str = "Architectural Designer"
    avatar_url: str = ""
    preferred_language: str = "English"
    theme: str = "light"  # 'light', 'dark', 'system'
    default_room_type: str = "Living Room"
    default_interior_style: str = "Modern"
    preferred_temp: str = "Balanced / Neutral"
    liked_colors: List[str] = Field(default_factory=lambda: ["Warm Linen", "Desert Sand", "Muted Sage"])
    disliked_colors: List[str] = Field(default_factory=list)
    preferred_atmospheres: List[str] = Field(default_factory=lambda: ["Calm & Relaxing", "Modern & Sophisticated"])
    default_vis_mode: str = "Side-by-Side Comparison"


class UserAccount(BaseModel):
    id: str
    email: str
    full_name: str
    role: str = "user"  # 'user', 'admin'
    created_at: str
    avatar_url: Optional[str] = ""
    profile: Optional[UserProfile] = None


class UserSubscription(BaseModel):
    user_id: str
    plan_id: str = "free"  # 'free', 'plus', 'pro'
    status: str = "active"  # 'active', 'cancelled', 'past_due', 'expired'
    billing_cycle: str = "monthly"  # 'monthly', 'annual'
    current_period_start: str
    current_period_end: str
    razorpay_subscription_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None


class UsageRecord(BaseModel):
    user_id: str
    month_key: str  # 'YYYY-MM'
    analyses_used: int = 0
    ai_previews_used: int = 0
    exports_count: int = 0


class TimelineVersion(BaseModel):
    id: str
    user_id: str
    project_id: str
    version_num: int
    label: str
    timestamp: str
    palette_data: Dict[str, Any]
    notes: str = ""
    thumbnail_data: Optional[str] = None  # Base64 thumbnail string


class ChromaMemoryProfile(BaseModel):
    user_id: str
    favorite_colors: List[str] = Field(default_factory=list)
    rejected_colors: List[str] = Field(default_factory=list)
    preferred_styles: List[str] = Field(default_factory=list)
    preferred_atmospheres: List[str] = Field(default_factory=list)
    interactions_count: int = 0


class ChromaDNA(BaseModel):
    user_id: str
    signature_name: str
    dominant_family: str
    contrast_level: str  # 'Subtle Low-Contrast', 'Balanced Architectural', 'Dramatic High-Contrast'
    temperature_bias: str  # 'Warm Terracotta Leaning', 'Crisp Cool Leaning', 'True Neutral Greige'
    material_affinity: List[str]
    preferred_styles: List[str]
    signature_swatches: List[ColorSwatch]


class PaintEstimateInput(BaseModel):
    room_length_meters: float = 5.0
    room_width_meters: float = 4.0
    wall_height_meters: float = 2.8
    num_doors: int = 1
    num_windows: int = 2
    coats: int = 2
    num_coats: Optional[int] = None  # alias for coats
    coverage_sqm_per_liter: float = 12.0  # Standard interior emulsion coverage
    cost_per_liter_inr: Optional[float] = 450.0  # Optional user-supplied rate
    total_wall_area_sqft: Optional[float] = None  # Optional direct sq ft input


class PaintEstimateResult(BaseModel):
    gross_wall_area_sqm: float
    deductions_sqm: float
    net_wall_area_sqm: float
    total_coated_area_sqm: float
    paint_liters_required: float
    recommended_cans_breakdown: Dict[str, int]
    estimated_cost_inr: Optional[float] = None
    estimator_disclaimer: str = (
        "Note: Rule-based architectural approximation. Real coverage varies by physical wall texture, "
        "primer quality, porosity, and application method. Always check manufacturer specifications before purchasing."
    )

    @property
    def total_litres_needed(self) -> float:
        return self.paint_liters_required

    @property
    def recommended_cans_one_litre(self) -> int:
        return self.recommended_cans_breakdown.get("1-Litre Cans", 0)

