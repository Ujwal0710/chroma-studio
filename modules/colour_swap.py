"""Colour Swap Playground: Interactive single-colour modification with locked anchors."""
from typing import Tuple, Optional, Dict, Any
from models.schemas import PaletteConcept, ColorSwatch
from modules.colour_extraction import get_closest_interior_color_name
from modules.image_processing import rgb_to_cielab, calculate_cielab_delta_e


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    h = hex_code.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
    r, g, b = [x / 255.0 for x in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def determine_temperature(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    if r > b + 20:
        return "warm"
    elif b > r + 20:
        return "cool"
    return "neutral"


def swap_palette_color(
    base_palette: PaletteConcept,
    slot_name: str,  # 'primary_wall', 'secondary_wall', 'accent', 'trim'
    new_hex: str,
    custom_swatch_name: Optional[str] = None
) -> PaletteConcept:
    """
    Swap a single color swatch in a palette while preserving all locked colors.
    Returns a cloned, updated PaletteConcept.
    """
    new_rgb = hex_to_rgb(new_hex)
    new_name = custom_swatch_name or get_closest_interior_color_name(new_hex)
    new_lum = calculate_luminance(new_rgb)
    new_temp = determine_temperature(new_rgb)
    
    updated_dict = base_palette.model_dump()
    
    new_swatch = ColorSwatch(
        hex=new_hex.upper(),
        rgb=new_rgb,
        role=slot_name.replace("_", " ").title(),
        name=new_name,
        luminance=round(new_lum, 3),
        temperature=new_temp,
        percentage=updated_dict.get(slot_name, {}).get("percentage", 25.0)
    )
    
    updated_dict[slot_name] = new_swatch.model_dump()
    updated_dict["name"] = f"{base_palette.name} (Custom Variant)"
    updated_dict["id"] = f"{base_palette.id}_variant"
    
    # Recalculate heuristic score variation
    p_rgb = updated_dict["primary_wall"]["rgb"]
    a_rgb = updated_dict["accent"]["rgb"]
    delta_e = calculate_cielab_delta_e(rgb_to_cielab(tuple(p_rgb)), rgb_to_cielab(tuple(a_rgb)))
    
    score = min(98.0, max(50.0, 75.0 + (delta_e / 2.5)))
    updated_dict["heuristic_score"] = round(score, 1)
    
    return PaletteConcept(**updated_dict)
