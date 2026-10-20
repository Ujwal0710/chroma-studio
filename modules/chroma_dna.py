"""Chroma DNA: Deterministic personal design signature generator."""
from typing import Dict, Any, List
from models.schemas import ChromaDNA, ColorSwatch, UserProfile
from modules.chroma_memory import get_chroma_memory
from modules.storage import get_user_profile, DB_PATH


def generate_chroma_dna(user_id: str, db_path: str = DB_PATH) -> ChromaDNA:
    """
    Generate an inspectable personal design signature based on profile and interactions.
    Deterministic, rule-based algorithm.
    """
    profile = get_user_profile(user_id, db_path=db_path) or {}
    memory = get_chroma_memory(user_id, db_path=db_path)
    
    preferred_temp = profile.get("preferred_temp", "Balanced / Neutral")
    fav_styles = memory.get("preferred_styles", [])
    if not fav_styles:
        fav_styles = [profile.get("default_interior_style", "Modern")]
    
    liked_colors = profile.get("liked_colors", []) + memory.get("favorite_colors", [])
    liked_lower = [c.lower() for c in liked_colors]
    
    # 1. Temperature bias
    if "warm" in preferred_temp.lower() or any(w in liked_lower for w in ["terracotta", "sand", "linen", "clay", "amber"]):
        temp_bias = "Warm Terracotta & Sand Leaning"
        seed_hexes = [("#F5EBE1", "Warm Alabaster"), ("#D8C3B0", "Oatmeal Linen"), ("#B98468", "Raw Sienna"), ("#5B4130", "Burnt Umber")]
    elif "cool" in preferred_temp.lower() or any(c in liked_lower for c in ["sage", "slate", "blue", "teal", "eucalyptus"]):
        temp_bias = "Crisp Nordic Slate & Sage Leaning"
        seed_hexes = [("#E8ECE9", "Muted Fog"), ("#B8C7BC", "Eucalyptus Mist"), ("#566E64", "Architectural Sage"), ("#2C3E3A", "Deep Pine")]
    else:
        temp_bias = "True Neutral Architectural Greige"
        seed_hexes = [("#EFECE6", "Chalk Wash"), ("#D6CFCE", "Limestone Greige"), ("#8C827A", "Warm Taupe"), ("#34302C", "Espresso Bronze")]
    
    # 2. Contrast Level
    if "minimalist" in [s.lower() for s in fav_styles] or "scandinavian" in [s.lower() for s in fav_styles]:
        contrast_level = "Subtle Low-Contrast (Calming)"
    elif "industrial" in [s.lower() for s in fav_styles] or "contemporary" in [s.lower() for s in fav_styles]:
        contrast_level = "Dramatic High-Contrast (Bold Focal)"
    else:
        contrast_level = "Balanced Architectural (Harmonious)"
        
    # 3. Material affinities
    materials = ["Oak Wood", "Natural Linen"]
    if "Warm" in temp_bias:
        materials.append("Brushed Brass")
    elif "Nordic" in temp_bias:
        materials.append("Carrara Marble")
    else:
        materials.append("Cast Concrete")
        
    # 4. Construct signature swatches
    swatches = []
    roles = ["Foundational Plane", "Secondary Surface", "Key Focal Accent", "Structural Trim"]
    for i, (hex_code, name) in enumerate(seed_hexes):
        # Calculate approximate RGB
        h = hex_code.lstrip("#")
        rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        swatches.append(ColorSwatch(
            hex=hex_code,
            rgb=rgb,
            role=roles[i],
            name=name,
            temperature="warm" if "Warm" in temp_bias else ("cool" if "Nordic" in temp_bias else "neutral"),
            percentage=60.0 if i == 0 else (30.0 if i == 1 else (10.0 if i == 2 else 5.0))
        ))
        
    signature_name = f"{profile.get('display_name', 'Architectural')} Studio DNA"
    
    return ChromaDNA(
        user_id=user_id,
        signature_name=signature_name,
        dominant_family=temp_bias,
        contrast_level=contrast_level,
        temperature_bias=temp_bias,
        material_affinity=materials,
        preferred_styles=fav_styles[:3],
        signature_swatches=swatches
    )
