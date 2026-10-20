"""Deterministic colour palette recommendation engine with heuristic ranking and duplicate removal."""
import uuid
import math
from typing import List, Dict, Tuple, Optional
from models.schemas import (
    PaletteConcept,
    ColorSwatch,
    ExtractedColorAnalysis,
    RoomAnalysisResult,
    PreferenceSettings
)
from modules.image_processing import (
    rgb_to_hex,
    rgb_to_hsv,
    hsv_to_rgb,
    rgb_to_cielab,
    calculate_perceptual_luminance,
    classify_color_characteristics
)
from modules.colour_extraction import match_color_name
from modules.colour_theory import (
    generate_monochromatic_harmony,
    generate_analogous_harmony,
    generate_complementary_harmony,
    generate_neutral_accent_harmony,
    calculate_color_distance_lab,
    calculate_palette_distance,
    calculate_contrast_ratio
)

# Reference palette seeds for preference-driven selections
PREFERENCE_COLOR_MAP = {
    "terracotta": (205, 125, 85),
    "warm beige / cream": (238, 228, 212),
    "sage green": (155, 172, 145),
    "olive green": (125, 138, 105),
    "navy blue": (45, 65, 88),
    "coastal blue": (145, 175, 192),
    "greige / warm gray": (210, 202, 190),
    "charcoal / slate": (75, 80, 88),
    "ochre / mustard": (215, 160, 75),
    "blush / soft rose": (228, 195, 185)
}


def build_swatch(
    rgb: Tuple[int, int, int],
    role: str,
    custom_name: Optional[str] = None,
    proportion_str: Optional[str] = None
) -> ColorSwatch:
    """Build a validated ColorSwatch instance with automatic trait classification."""
    r, g, b = max(0, min(255, rgb[0])), max(0, min(255, rgb[1])), max(0, min(255, rgb[2]))
    hex_code = rgb_to_hex(r, g, b)
    name = custom_name or match_color_name(r, g, b)
    traits = classify_color_characteristics(r, g, b)
    lum = round(calculate_perceptual_luminance(r, g, b), 3)

    return ColorSwatch(
        hex=hex_code,
        rgb=(r, g, b),
        role=role,
        name=name,
        temperature=traits["temperature"],
        saturation_category=traits["saturation"],
        luminance=lum,
        description=f"{traits['lightness'].capitalize()} {traits['temperature']} tone ({name})"
    )


def adjust_for_preferences(
    rgb: Tuple[int, int, int],
    preferences: PreferenceSettings
) -> Tuple[int, int, int]:
    """Apply lightness, colorfulness, and temperature adjustments to an RGB tone."""
    h, s, v = rgb_to_hsv(rgb[0], rgb[1], rgb[2])

    # Lightness adjustment
    if preferences.lightness_preference == "Light & Airy":
        v = min(0.96, max(0.72, v + 0.12))
        s = max(0.04, s * 0.85)
    elif preferences.lightness_preference == "Deep & Moody":
        v = max(0.20, min(0.48, v * 0.65))
        s = min(0.65, max(0.18, s * 1.15))
    else:  # Mid-Tone Balanced
        v = min(0.85, max(0.48, v))

    # Colorfulness adjustment
    if preferences.colorfulness_preference == "Subtle & Neutral":
        s = max(0.03, min(0.18, s * 0.6))
    elif preferences.colorfulness_preference == "Vibrant & Saturated":
        s = min(0.75, max(0.35, s * 1.35 + 0.1))

    # Temperature adjustment
    if preferences.temperature_preference == "Warm":
        if 160 <= h <= 280:  # cool hue
            h = (h + 60) % 360  # nudge toward teal/yellow
        s = min(0.65, s * 1.05)
    elif preferences.temperature_preference == "Cool":
        if h <= 80 or h >= 330:  # warm hue
            h = (h + 120) % 360  # nudge toward sage or cool blue

    return hsv_to_rgb(h, s, v)


def score_palette_heuristic(
    palette: PaletteConcept,
    preferences: PreferenceSettings,
    extracted: ExtractedColorAnalysis
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate transparent heuristic ranking score (0 to 100) based on:
    - Temperature alignment
    - Lightness alignment
    - Colorfulness alignment
    - Contrast ratio with trim
    - Compatibility with dominant room colors
    - Respect of preferred and avoided colors
    """
    score = 50.0  # Base neutral baseline
    breakdown: Dict[str, float] = {}

    primary_rgb = palette.primary_wall.rgb
    accent_rgb = palette.accent.rgb
    trim_rgb = palette.trim.rgb

    # 1. Temperature score (up to +15)
    pref_temp = preferences.temperature_preference.lower()
    wall_temp = palette.primary_wall.temperature
    if "warm" in pref_temp:
        temp_score = 15.0 if wall_temp == "warm" else (8.0 if wall_temp == "neutral" else 2.0)
    elif "cool" in pref_temp:
        temp_score = 15.0 if wall_temp == "cool" else (8.0 if wall_temp == "neutral" else 2.0)
    else:
        temp_score = 12.0  # Balanced preference
    breakdown["Temperature Alignment"] = round(temp_score, 1)
    score += temp_score

    # 2. Lightness alignment (up to +12)
    lum = palette.primary_wall.luminance or 0.5
    if preferences.lightness_preference == "Light & Airy":
        light_score = 12.0 if lum >= 0.60 else (6.0 if lum >= 0.40 else 2.0)
    elif preferences.lightness_preference == "Deep & Moody":
        light_score = 12.0 if lum <= 0.35 else (6.0 if lum <= 0.50 else 2.0)
    else:
        light_score = 10.0 if 0.35 <= lum <= 0.65 else 5.0
    breakdown["Lightness Calibration"] = round(light_score, 1)
    score += light_score

    # 3. Architectural Contrast (up to +10)
    contrast = calculate_contrast_ratio(primary_rgb, trim_rgb)
    contrast_score = 10.0 if contrast >= 2.0 else 5.0
    breakdown["Trim Contrast Ratio"] = round(contrast_score, 1)
    score += contrast_score

    # 4. Room Dominant Harmony (up to +10)
    # Check if accent or trim coordinates with existing dominant room tones
    min_dist_to_room = min(
        calculate_color_distance_lab(palette.primary_wall.rgb, d.rgb)
        for d in extracted.dominant_colors[:4]
    ) if extracted.dominant_colors else 20.0
    # Good harmony is moderate distance (not an exact identical clashing duplicate, but coordinated)
    harm_score = 10.0 if 12.0 <= min_dist_to_room <= 45.0 else 6.0
    breakdown["Existing Space Harmony"] = round(harm_score, 1)
    score += harm_score

    # 5. Preferred / Avoided color penalties (±10)
    pref_score = 0.0
    # Check avoided colors
    for avoided in preferences.colors_to_avoid:
        avoid_key = avoided.lower().strip()
        for c in palette.all_colors():
            if avoid_key in c.name.lower() or avoid_key in (c.temperature or ""):
                pref_score -= 8.0
                break

    # Check preferred colors
    for pref in preferences.preferred_colors:
        pref_key = pref.lower().strip()
        for c in palette.all_colors():
            if pref_key in c.name.lower():
                pref_score += 6.0
                break

    breakdown["User Preference Constraints"] = round(pref_score, 1)
    score += pref_score

    # Clamp total score between 55.0 and 98.0
    final_score = round(max(55.0, min(98.5, score)), 1)
    return final_score, breakdown


def generate_recommended_palettes(
    extracted: ExtractedColorAnalysis,
    room_analysis: Optional[RoomAnalysisResult] = None,
    preferences: Optional[PreferenceSettings] = None
) -> List[PaletteConcept]:
    """
    Deterministic generation of 4 distinct interior design palettes:
    1. Warm and Inviting
    2. Cool and Calming
    3. Modern Neutral
    4. Bold Accent / Contemporary Contrast
    """
    if preferences is None:
        from modules.preferences import create_default_preferences
        r_type = room_analysis.detected_room_type if room_analysis else "Automatic Detection"
        r_style = room_analysis.detected_style if room_analysis else "Automatic Detection"
        preferences = create_default_preferences(room_type=r_type, interior_style=r_style)

    if room_analysis is None:
        from services.vision_provider import generate_local_rule_based_analysis
        room_analysis = generate_local_rule_based_analysis(extracted)

    palettes: List[PaletteConcept] = []
    dom_colors = extracted.dominant_colors


    # Select seed tones from extracted image colors
    # Warmest dominant
    warm_candidates = [c for c in dom_colors if c.temperature == "warm"]
    seed_warm = warm_candidates[0].rgb if warm_candidates else (210, 160, 120)

    # Coolest dominant
    cool_candidates = [c for c in dom_colors if c.temperature == "cool"]
    seed_cool = cool_candidates[0].rgb if cool_candidates else (145, 175, 185)

    # Most prominent neutral
    neutral_candidates = [c for c in dom_colors if c.saturation_category == "neutral"]
    seed_neutral = neutral_candidates[0].rgb if neutral_candidates else (215, 210, 200)

    # Prominent accent candidate
    sat_candidates = [c for c in dom_colors if c.saturation_category == "saturated"]
    seed_accent = sat_candidates[0].rgb if sat_candidates else (185, 95, 65)

    # Override seeds if user explicitly selected preferred color
    if preferences.preferred_colors:
        first_pref = preferences.preferred_colors[0].lower().strip()
        for key, ref_rgb in PREFERENCE_COLOR_MAP.items():
            if key in first_pref or first_pref in key:
                seed_neutral = ref_rgb
                break

    # --- CONCEPT 1: Warm and Inviting ---
    c1_seed = adjust_for_preferences(seed_warm, preferences)
    c1_raw = generate_analogous_harmony(c1_seed, angle=25.0)
    sw_prim = build_swatch(c1_raw["primary_wall"], "Primary Wall (60%)")
    sw_sec = build_swatch(c1_raw["secondary_wall"], "Secondary / Feature Wall (30%)")
    sw_acc = build_swatch(c1_raw["accent"], "Accent Details & Decor (10%)")
    sw_trim = build_swatch(c1_raw["trim"], "Trim & Ceiling")

    p1 = PaletteConcept(
        id=f"palette-{uuid.uuid4().hex[:8]}",
        name="Warm Amber & Linen Sanctuary",
        concept_category="Warm and Inviting",
        harmony_type="Analogous Harmony",
        description=(
            f"An inviting, sun-drenched palette anchored by {sw_prim.name} on main walls, "
            f"supported by {sw_sec.name} for gentle depth and {sw_acc.name} as a grounding focal point."
        ),
        atmosphere="Warm, welcoming, cozy, and grounding",
        primary_wall=sw_prim,
        secondary_wall=sw_sec,
        accent=sw_acc,
        trim=sw_trim,
        proportions={"Primary Wall": "60%", "Secondary Wall / Trim": "30%", "Accent Accents": "10%"},
        design_rationale=(
            f"Balances the ambient {room_analysis.apparent_lighting} by infusing welcoming warmth "
            f"while maintaining high Light Reflectance Value on living planes."
        ),
        furniture_flooring_compatibility=(
            f"Harmonizes naturally with {room_analysis.flooring_description} and enhances natural wood and soft textiles."
        )
    )
    score1, b1 = score_palette_heuristic(p1, preferences, extracted)
    p1.heuristic_score = score1
    p1.score_breakdown = b1
    palettes.append(p1)

    # --- CONCEPT 2: Cool and Calming ---
    c2_seed = adjust_for_preferences(seed_cool, preferences)
    c2_raw = generate_monochromatic_harmony(c2_seed)
    sw_prim2 = build_swatch(c2_raw["primary_wall"], "Primary Wall (60%)")
    sw_sec2 = build_swatch(c2_raw["secondary_wall"], "Secondary / Feature Wall (30%)")
    sw_acc2 = build_swatch(c2_raw["accent"], "Accent Details & Decor (10%)")
    sw_trim2 = build_swatch(c2_raw["trim"], "Trim & Ceiling")

    p2 = PaletteConcept(
        id=f"palette-{uuid.uuid4().hex[:8]}",
        name="Nordic Mist & Mineral Serenity",
        concept_category="Cool and Calming",
        harmony_type="Monochromatic Harmony",
        description=(
            f"A serene, restorative palette pairing tranquil {sw_prim2.name} with {sw_sec2.name} "
            f"and sophisticated {sw_acc2.name} accents."
        ),
        atmosphere="Calm, restorative, spacious, and fresh",
        primary_wall=sw_prim2,
        secondary_wall=sw_sec2,
        accent=sw_acc2,
        trim=sw_trim2,
        proportions={"Primary Wall": "60%", "Secondary Wall / Trim": "30%", "Accent Accents": "10%"},
        design_rationale=(
            f"Expands spatial perception and calms visual clutter under {room_analysis.apparent_lighting}. "
            f"Ideal for rooms designed for concentration or tranquil rest."
        ),
        furniture_flooring_compatibility=(
            "Provides an elegant architectural backdrop that lets warm leather and medium timber grains stand out with crisp contrast."
        )
    )
    score2, b2 = score_palette_heuristic(p2, preferences, extracted)
    p2.heuristic_score = score2
    p2.score_breakdown = b2
    palettes.append(p2)

    # --- CONCEPT 3: Modern Neutral ---
    c3_seed = adjust_for_preferences(seed_neutral, preferences)
    c3_acc = (
        adjust_for_preferences(seed_accent, preferences)
        if preferences.accent_intensity == "Bold"
        else (110, 120, 115)  # muted slate / sage
    )
    c3_raw = generate_neutral_accent_harmony(c3_seed, c3_acc)
    sw_prim3 = build_swatch(c3_raw["primary_wall"], "Primary Wall (60%)")
    sw_sec3 = build_swatch(c3_raw["secondary_wall"], "Secondary / Feature Wall (30%)")
    sw_acc3 = build_swatch(c3_raw["accent"], "Accent Details & Decor (10%)")
    sw_trim3 = build_swatch(c3_raw["trim"], "Trim & Ceiling")

    p3 = PaletteConcept(
        id=f"palette-{uuid.uuid4().hex[:8]}",
        name="Architectural Greige & Travertine",
        concept_category="Modern Neutral",
        harmony_type="Neutral and Accent",
        description=(
            f"A timeless, high-end gallery aesthetic centering on {sw_prim3.name} walls with "
            f"tonal depth from {sw_sec3.name} and a curated statement in {sw_acc3.name}."
        ),
        atmosphere="Sophisticated, understated, timeless, and curated",
        primary_wall=sw_prim3,
        secondary_wall=sw_sec3,
        accent=sw_acc3,
        trim=sw_trim3,
        proportions={"Primary Wall": "60%", "Secondary Wall / Trim": "30%", "Accent Accents": "10%"},
        design_rationale=(
            "Provides an adaptable, designer-grade canvas that flatters both natural daylight and evening artificial lighting."
        ),
        furniture_flooring_compatibility=(
            f"Seamlessly coordinates with existing millwork and {room_analysis.flooring_description} without undertone clashes."
        )
    )
    score3, b3 = score_palette_heuristic(p3, preferences, extracted)
    p3.heuristic_score = score3
    p3.score_breakdown = b3
    palettes.append(p3)

    # --- CONCEPT 4: Bold Accent / Contemporary Contrast ---
    c4_seed = adjust_for_preferences(seed_warm if preferences.temperature_preference != "Cool" else seed_cool, preferences)
    c4_raw = generate_complementary_harmony(c4_seed)
    sw_prim4 = build_swatch(c4_raw["primary_wall"], "Primary Wall (60%)")
    sw_sec4 = build_swatch(c4_raw["secondary_wall"], "Secondary / Feature Wall (30%)")
    sw_acc4 = build_swatch(c4_raw["accent"], "Statement Accent (10%)")
    sw_trim4 = build_swatch(c4_raw["trim"], "Trim & Ceiling")

    p4 = PaletteConcept(
        id=f"palette-{uuid.uuid4().hex[:8]}",
        name="Dramatic Contrast & Spiced Terracotta",
        concept_category="Bold Accent / Contemporary Contrast",
        harmony_type="Complementary Contrast",
        description=(
            f"A confident, visually engaging composition featuring {sw_prim4.name} with "
            f"high-impact complementary energy from {sw_acc4.name}."
        ),
        atmosphere="Dynamic, luxurious, artistic, and memorable",
        primary_wall=sw_prim4,
        secondary_wall=sw_sec4,
        accent=sw_acc4,
        trim=sw_trim4,
        proportions={"Primary Wall": "60%", "Secondary Wall / Trim": "30%", "Accent Statement": "10%"},
        design_rationale=(
            "Creates visual focal points and architectural depth, defining distinct zones within the interior layout."
        ),
        furniture_flooring_compatibility=(
            "Brings lively counterpoint to neutral upholstery while echoing tone highlights in metallic or stone finishes."
        )
    )
    score4, b4 = score_palette_heuristic(p4, preferences, extracted)
    p4.heuristic_score = score4
    p4.score_breakdown = b4
    palettes.append(p4)

    # Duplicate check: ensure no two palettes are perceptual near-duplicates (Delta E < 6.0)
    unique_palettes: List[PaletteConcept] = []
    for p in palettes:
        p_colors = [c.rgb for c in p.all_colors()]
        is_dup = False
        for u in unique_palettes:
            u_colors = [c.rgb for c in u.all_colors()]
            dist = calculate_palette_distance(p_colors, u_colors)
            if dist < 6.5:
                is_dup = True
                break
        if not is_dup:
            unique_palettes.append(p)
        else:
            # Shift hue slightly to disambiguate
            h_p, s_p, v_p = rgb_to_hsv(p.primary_wall.rgb[0], p.primary_wall.rgb[1], p.primary_wall.rgb[2])
            shifted_rgb = hsv_to_rgb((h_p + 40.0) % 360.0, s_p, v_p)
            p.primary_wall = build_swatch(shifted_rgb, p.primary_wall.role)
            unique_palettes.append(p)

    # Sort palettes by heuristic score descending
    unique_palettes.sort(key=lambda x: x.heuristic_score, reverse=True)
    return unique_palettes
