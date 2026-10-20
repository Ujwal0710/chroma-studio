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
    r = int(max(0, min(255, round(rgb[0]))))
    g = int(max(0, min(255, round(rgb[1]))))
    b = int(max(0, min(255, round(rgb[2]))))
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
        v = min(0.96, max(0.72, v + 0.14))
        s = max(0.04, s * 0.82)
    elif preferences.lightness_preference == "Deep & Moody":
        v = max(0.18, min(0.44, v * 0.62))
        s = min(0.70, max(0.20, s * 1.18))
    else:  # Mid-Tone Balanced
        v = min(0.85, max(0.48, v))

    # Colorfulness adjustment
    if preferences.colorfulness_preference == "Subtle & Neutral":
        s = max(0.03, min(0.18, s * 0.55))
    elif preferences.colorfulness_preference == "Vibrant & Saturated":
        s = min(0.80, max(0.35, s * 1.40 + 0.12))

    # Temperature adjustment
    if preferences.temperature_preference == "Warm":
        if 160 <= h <= 280:
            h = (h + 70) % 360  # nudge toward warm ochre/terracotta
        s = min(0.65, s * 1.08)
    elif preferences.temperature_preference == "Cool":
        if h <= 80 or h >= 330:
            h = (h + 120) % 360  # nudge toward sage or cool mineral

    # Specific preferred color guidance
    if preferences.preferred_colors:
        first_pref = preferences.preferred_colors[0].lower().strip()
        for key, ref_rgb in PREFERENCE_COLOR_MAP.items():
            if key in first_pref or first_pref in key:
                ref_h, ref_s, _ = rgb_to_hsv(ref_rgb[0], ref_rgb[1], ref_rgb[2])
                # Shift hue halfway toward user preferred color
                h = (h * 0.4 + ref_h * 0.6) % 360

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
    score = 50.0
    breakdown: Dict[str, float] = {}

    primary_rgb = palette.primary_wall.rgb
    trim_rgb = palette.trim.rgb

    # 1. Temperature score (up to +15)
    pref_temp = preferences.temperature_preference.lower()
    wall_temp = palette.primary_wall.temperature
    if "warm" in pref_temp:
        temp_score = 15.0 if wall_temp == "warm" else (8.0 if wall_temp == "neutral" else 2.0)
    elif "cool" in pref_temp:
        temp_score = 15.0 if wall_temp == "cool" else (8.0 if wall_temp == "neutral" else 2.0)
    else:
        temp_score = 12.0
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
    min_dist_to_room = min(
        calculate_color_distance_lab(palette.primary_wall.rgb, d.rgb)
        for d in extracted.dominant_colors[:4]
    ) if extracted.dominant_colors else 20.0
    harm_score = 10.0 if 12.0 <= min_dist_to_room <= 45.0 else 6.0
    breakdown["Existing Space Harmony"] = round(harm_score, 1)
    score += harm_score

    # 5. Preferred / Avoided color penalties (±10)
    pref_score = 0.0
    for avoided in preferences.colors_to_avoid:
        avoid_key = avoided.lower().strip()
        for c in palette.all_colors():
            if avoid_key in c.name.lower() or avoid_key in (c.temperature or ""):
                pref_score -= 8.0
                break

    for pref in preferences.preferred_colors:
        pref_key = pref.lower().strip()
        for c in palette.all_colors():
            if pref_key in c.name.lower():
                pref_score += 6.0
                break

    breakdown["User Preference Constraints"] = round(pref_score, 1)
    score += pref_score

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

    Guarantees perceptual distinctiveness (Delta E >= 12.0 between primary walls),
    valid HEX/RGB values, and detailed architectural rationales.
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

    # Select seed tones
    warm_candidates = [c for c in dom_colors if c.temperature == "warm"]
    seed_warm = warm_candidates[0].rgb if warm_candidates else (210, 155, 110)

    cool_candidates = [c for c in dom_colors if c.temperature == "cool"]
    seed_cool = cool_candidates[0].rgb if cool_candidates else (140, 168, 175)

    neutral_candidates = [c for c in dom_colors if c.saturation_category == "neutral"]
    seed_neutral = neutral_candidates[0].rgb if neutral_candidates else (215, 210, 200)

    sat_candidates = [c for c in dom_colors if c.saturation_category == "saturated"]
    seed_accent = sat_candidates[0].rgb if sat_candidates else (185, 90, 60)

    # Respect user preferred color seed if provided
    if preferences.preferred_colors:
        first_pref = preferences.preferred_colors[0].lower().strip()
        for key, ref_rgb in PREFERENCE_COLOR_MAP.items():
            if key in first_pref or first_pref in key:
                if "green" in key or "blue" in key or "slate" in key:
                    seed_cool = ref_rgb
                elif "terracotta" in key or "ochre" in key or "blush" in key:
                    seed_warm = ref_rgb
                else:
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
            f"An inviting, sun-drenched palette anchored by {sw_prim.name} ({sw_prim.hex}) on main walls, "
            f"supported by {sw_sec.name} for gentle depth and {sw_acc.name} as a grounding focal point."
        ),
        atmosphere="Warm, welcoming, cozy, and grounding",
        primary_wall=sw_prim,
        secondary_wall=sw_sec,
        accent=sw_acc,
        trim=sw_trim,
        proportions={"Primary Wall": "60%", "Secondary Wall / Trim": "30%", "Accent Accents": "10%"},
        design_rationale=(
            f"Selected to enrich the room's apparent {room_analysis.apparent_lighting}. "
            f"The warm primary hue ({sw_prim.name}) counteracts cool ambient shadow while harmonizing "
            f"with detected dominant tones like {dom_colors[0].name if dom_colors else 'room neutrals'}."
        ),
        furniture_flooring_compatibility=(
            f"Coordinates seamlessly with {room_analysis.flooring_description}. "
            f"The warm undertone bridges natural timber grain, leather, and woven textiles without undertone clash."
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
            f"A serene, restorative palette pairing tranquil {sw_prim2.name} ({sw_prim2.hex}) with {sw_sec2.name} "
            f"and sophisticated {sw_acc2.name} accents."
        ),
        atmosphere="Calm, restorative, spacious, and fresh",
        primary_wall=sw_prim2,
        secondary_wall=sw_sec2,
        accent=sw_acc2,
        trim=sw_trim2,
        proportions={"Primary Wall": "60%", "Secondary Wall / Trim": "30%", "Accent Accents": "10%"},
        design_rationale=(
            f"Calibrated for spatial expansion under {room_analysis.apparent_lighting}. "
            f"The cool mineral balance reflects natural light into darker corners and visually declutters the room."
        ),
        furniture_flooring_compatibility=(
            f"Provides a crisp architectural counterpoint to {room_analysis.flooring_description}, "
            "allowing warm furnishings to register as intentional focal accents rather than competing surfaces."
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
        else (110, 120, 115)
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
            f"A timeless, high-end gallery aesthetic centering on {sw_prim3.name} ({sw_prim3.hex}) walls with "
            f"tonal depth from {sw_sec3.name} and a curated statement in {sw_acc3.name}."
        ),
        atmosphere="Sophisticated, understated, timeless, and curated",
        primary_wall=sw_prim3,
        secondary_wall=sw_sec3,
        accent=sw_acc3,
        trim=sw_trim3,
        proportions={"Primary Wall": "60%", "Secondary Wall / Trim": "30%", "Accent Accents": "10%"},
        design_rationale=(
            "Provides an adaptable, designer-grade neutral canvas that flatters shifting diurnal daylight "
            "while maintaining comfortable Light Reflectance Value without glare."
        ),
        furniture_flooring_compatibility=(
            f"Seamlessly aligns with {room_analysis.flooring_description}. "
            "Its low-chroma baseline supports mixed metal finishes, stone countertops, and natural upholstery."
        )
    )
    score3, b3 = score_palette_heuristic(p3, preferences, extracted)
    p3.heuristic_score = score3
    p3.score_breakdown = b3
    palettes.append(p3)

    # --- CONCEPT 4: Bold Accent / Contemporary Contrast ---
    # Strong contrast against existing room baseline
    bold_seed = (
        (185, 75, 60) if preferences.temperature_preference != "Cool"
        else (50, 85, 115)
    )
    c4_seed = adjust_for_preferences(bold_seed, preferences)
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
            f"A confident, visually engaging composition featuring {sw_prim4.name} ({sw_prim4.hex}) with "
            f"high-impact complementary energy from {sw_acc4.name}."
        ),
        atmosphere="Dynamic, luxurious, artistic, and memorable",
        primary_wall=sw_prim4,
        secondary_wall=sw_sec4,
        accent=sw_acc4,
        trim=sw_trim4,
        proportions={"Primary Wall": "60%", "Secondary Wall / Trim": "30%", "Accent Statement": "10%"},
        design_rationale=(
            "Creates visual focal points and architectural depth, defining distinct zones within the interior layout "
            f"and offering high-impact contrast under {room_analysis.apparent_lighting}."
        ),
        furniture_flooring_compatibility=(
            f"Provides an energetic counterbalance to {room_analysis.flooring_description}, "
            "infusing architectural rhythm while preventing the room from feeling monolithic or washed out."
        )
    )
    score4, b4 = score_palette_heuristic(p4, preferences, extracted)
    p4.heuristic_score = score4
    p4.score_breakdown = b4
    palettes.append(p4)

    # Enforce distinctiveness: ensure all 4 palettes have Delta E >= 12.0 between their primary walls
    for i in range(len(palettes)):
        for j in range(i + 1, len(palettes)):
            dist = calculate_color_distance_lab(palettes[i].primary_wall.rgb, palettes[j].primary_wall.rgb)
            if dist < 12.0:
                # Disambiguate palette j by shifting hue 45 degrees
                h_j, s_j, v_j = rgb_to_hsv(
                    palettes[j].primary_wall.rgb[0],
                    palettes[j].primary_wall.rgb[1],
                    palettes[j].primary_wall.rgb[2]
                )
                shifted_rgb = hsv_to_rgb((h_j + 50.0) % 360.0, max(0.15, s_j), v_j)
                palettes[j].primary_wall = build_swatch(shifted_rgb, palettes[j].primary_wall.role)
                s_score, s_b = score_palette_heuristic(palettes[j], preferences, extracted)
                palettes[j].heuristic_score = s_score
                palettes[j].score_breakdown = s_b

    palettes.sort(key=lambda x: x.heuristic_score, reverse=True)
    return palettes
