"""Colour Harmony Explorer: Computational harmony relationships, wheel shifts, and CIELAB distance."""
import colorsys
from typing import Dict, Any, List, Tuple
from modules.image_processing import rgb_to_cielab, calculate_cielab_delta_e
from modules.colour_extraction import get_closest_interior_color_name
from models.schemas import ColorSwatch, PaletteConcept


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    h = hex_code.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return f"#{int(rgb[0]):02X}{int(rgb[1]):02X}{int(rgb[2]):02X}"


def shift_hue(rgb: Tuple[int, int, int], degree_shift: float, s_scale: float = 1.0, l_scale: float = 1.0) -> Tuple[int, int, int]:
    """Shift hue by degrees (0-360) in HLS color space."""
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    new_h = (h + (degree_shift / 360.0)) % 1.0
    new_s = max(0.05, min(1.0, s * s_scale))
    new_l = max(0.08, min(0.95, l * l_scale))
    nr, ng, nb = colorsys.hls_to_rgb(new_h, new_l, new_s)
    return (int(round(nr * 255)), int(round(ng * 255)), int(round(nb * 255)))


def explore_color_harmonies(seed_hex: str) -> Dict[str, Any]:
    """
    Generate comprehensive harmony relationships around a seed colour.
    Calculates exact CIELAB Delta-E metrics and architectural interior names.
    """
    seed_rgb = hex_to_rgb(seed_hex)
    seed_lab = rgb_to_cielab(seed_rgb)
    seed_name = get_closest_interior_color_name(seed_hex)
    
    # 1. Complementary (+180 deg)
    comp_rgb = shift_hue(seed_rgb, 180)
    comp_hex = rgb_to_hex(comp_rgb)
    comp_delta = calculate_cielab_delta_e(seed_lab, rgb_to_cielab(comp_rgb))
    
    # 2. Analogous (-30 and +30 deg)
    ana1_rgb = shift_hue(seed_rgb, -30)
    ana1_hex = rgb_to_hex(ana1_rgb)
    ana2_rgb = shift_hue(seed_rgb, 30)
    ana2_hex = rgb_to_hex(ana2_rgb)
    
    # 3. Triadic (+120 and +240 deg)
    tri1_rgb = shift_hue(seed_rgb, 120)
    tri1_hex = rgb_to_hex(tri1_rgb)
    tri2_rgb = shift_hue(seed_rgb, 240)
    tri2_hex = rgb_to_hex(tri2_rgb)
    
    # 4. Monochromatic variations (light tint and deep shade)
    tint_rgb = shift_hue(seed_rgb, 0, s_scale=0.75, l_scale=1.35)
    tint_hex = rgb_to_hex(tint_rgb)
    shade_rgb = shift_hue(seed_rgb, 0, s_scale=1.1, l_scale=0.65)
    shade_hex = rgb_to_hex(shade_rgb)
    
    # 5. Neutral Supporting Tone (desaturated complement / greige companion)
    neut_rgb = shift_hue(seed_rgb, 15, s_scale=0.25, l_scale=1.2)
    neut_hex = rgb_to_hex(neut_rgb)
    
    return {
        "seed": {
            "hex": seed_hex,
            "rgb": seed_rgb,
            "name": seed_name
        },
        "complementary": {
            "hex": comp_hex,
            "rgb": comp_rgb,
            "name": get_closest_interior_color_name(comp_hex),
            "delta_e": round(comp_delta, 1),
            "description": "Opposite on the 360° colour wheel for dynamic contrast."
        },
        "analogous": [
            {
                "hex": ana1_hex,
                "rgb": ana1_rgb,
                "name": get_closest_interior_color_name(ana1_hex),
                "delta_e": round(calculate_cielab_delta_e(seed_lab, rgb_to_cielab(ana1_rgb)), 1),
                "label": "-30° Neighbor"
            },
            {
                "hex": ana2_hex,
                "rgb": ana2_rgb,
                "name": get_closest_interior_color_name(ana2_hex),
                "delta_e": round(calculate_cielab_delta_e(seed_lab, rgb_to_cielab(ana2_rgb)), 1),
                "label": "+30° Neighbor"
            }
        ],
        "triadic": [
            {
                "hex": tri1_hex,
                "rgb": tri1_rgb,
                "name": get_closest_interior_color_name(tri1_hex),
                "delta_e": round(calculate_cielab_delta_e(seed_lab, rgb_to_cielab(tri1_rgb)), 1),
                "label": "+120° Triad"
            },
            {
                "hex": tri2_hex,
                "rgb": tri2_rgb,
                "name": get_closest_interior_color_name(tri2_hex),
                "delta_e": round(calculate_cielab_delta_e(seed_lab, rgb_to_cielab(tri2_rgb)), 1),
                "label": "+240° Triad"
            }
        ],
        "monochromatic": [
            {
                "hex": tint_hex,
                "rgb": tint_rgb,
                "name": get_closest_interior_color_name(tint_hex),
                "label": "Airy Tint (Light Wall)"
            },
            {
                "hex": shade_hex,
                "rgb": shade_rgb,
                "name": get_closest_interior_color_name(shade_hex),
                "label": "Deep Shade (Grounded Accent)"
            }
        ],
        "neutral_supporting": {
            "hex": neut_hex,
            "rgb": neut_rgb,
            "name": get_closest_interior_color_name(neut_hex),
            "label": "Architectural Foundation Greige"
        }
    }
