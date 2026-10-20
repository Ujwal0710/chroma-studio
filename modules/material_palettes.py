"""Material-Aware Palettes: Material characteristics, undertone harmony, and recommendation ranking."""
from typing import Dict, Any, List, Tuple
from models.schemas import PaletteConcept

MATERIAL_PROFILES = {
    "Oak Wood": {
        "undertone": "warm honey amber",
        "harmonious_hues": ["Warm Linen", "Muted Sage", "Terracotta", "Architectural Greige"],
        "clashing_hues": ["Cool Purple", "Bright Magenta"],
        "design_advice": "Pairs naturally with warm whites, botanical greens, and soft terracotta."
    },
    "Walnut Wood": {
        "undertone": "deep chocolate espresso",
        "harmonious_hues": ["Alabaster White", "Warm Greige", "Deep Forest", "Oatmeal Linen"],
        "clashing_hues": ["Neon Yellow", "Orange-Red"],
        "design_advice": "Provides rich grounding contrast; pair with creamy neutrals or deep moody greens."
    },
    "Carrara Marble": {
        "undertone": "crisp white with cool graphite veins",
        "harmonious_hues": ["Architectural Charcoal", "Muted Slate", "Pure Chalk", "Brushed Brass"],
        "clashing_hues": ["Muddy Yellow", "Raw Umber"],
        "design_advice": "Complements cool neutrals, charcoal trims, and metallic brass accents."
    },
    "Cast Concrete": {
        "undertone": "neutral mineral gray",
        "harmonious_hues": ["Warm Ochre", "Raw Sienna", "Matte Black", "Desert Sand"],
        "clashing_hues": ["Pastel Pink", "Baby Blue"],
        "design_advice": "Balances best with warm woods, terracotta accents, or sleek industrial black metal."
    },
    "Natural Stone": {
        "undertone": "warm travertine limestone",
        "harmonious_hues": ["Warm Linen", "Olive Tint", "Sand Dune", "Burnt Umber"],
        "clashing_hues": ["Cold Blue-Gray"],
        "design_advice": "Organic and tactile; best complemented by earthy analogous tones and textured fabrics."
    },
    "Brushed Brass": {
        "undertone": "warm reflective metallic gold",
        "harmonious_hues": ["Architectural Teal", "Deep Charcoal", "Warm Alabaster", "Emerald"],
        "clashing_hues": ["Lime Green", "Bright Orange"],
        "design_advice": "Acts as jewelry for the room; elevates dark moody walls and soft alabaster surfaces."
    },
    "Black Matte Metal": {
        "undertone": "neutral structural black",
        "harmonious_hues": ["Light Limestone", "Warm Oak", "White Chalk", "Sage"],
        "clashing_hues": [],
        "design_advice": "Provides crisp architectural lines; coordinates with almost any cohesive palette."
    },
    "Natural Linen": {
        "undertone": "soft unbleached oatmeal",
        "harmonious_hues": ["Chalk Wash", "Muted Fog", "Eucalyptus Mist", "Soft Terracotta"],
        "clashing_hues": ["Electric Blue"],
        "design_advice": "Relaxed and breathable; perfect base for Scandinavian and Japandi color harmonies."
    },
    "Velvet": {
        "undertone": "rich saturated light-absorbing",
        "harmonious_hues": ["Deep Sapphire", "Plum", "Champagne", "Moody Charcoal"],
        "clashing_hues": ["Chalky Pastels"],
        "design_advice": "Adds opulence and depth; ideal for accent chairs, drapery, and focal walls."
    }
}

ALL_MATERIALS = list(MATERIAL_PROFILES.keys())


def evaluate_material_compatibility(materials: List[str], palette: PaletteConcept) -> Tuple[float, List[str]]:
    """
    Evaluate palette harmony against selected interior materials.
    Returns (compatibility_score_delta, list_of_insights).
    """
    if not materials:
        return 0.0, ["No specific materials selected for harmony calibration."]
        
    delta = 0.0
    insights = []
    
    palette_colors_lower = [c.name.lower() if c.name else "" for c in palette.all_colors()]
    
    for mat in materials:
        profile = MATERIAL_PROFILES.get(mat)
        if not profile:
            continue
            
        mat_matched = False
        for harm in profile["harmonious_hues"]:
            if any(harm.lower() in p_col for p_col in palette_colors_lower):
                delta += 3.0
                insights.append(f"✓ Strong synergy: {mat} ({profile['undertone']}) complements '{harm}'.")
                mat_matched = True
                break
                
        for clash in profile["clashing_hues"]:
            if any(clash.lower() in p_col for p_col in palette_colors_lower):
                delta -= 4.0
                insights.append(f"⚠ Caution: {mat} may clash with high-saturation '{clash}'.")
                
        if not mat_matched:
            insights.append(f"ℹ {mat}: {profile['design_advice']}")
            
    # Clip delta to reasonable bounds
    delta = max(-10.0, min(12.0, delta))
    return delta, insights
