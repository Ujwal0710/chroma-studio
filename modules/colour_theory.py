"""Colour theory, harmony calculations, and perceptual colour distances."""
import math
from typing import Tuple, List, Dict
from modules.image_processing import (
    rgb_to_hsv,
    hsv_to_rgb,
    rgb_to_cielab,
    calculate_perceptual_luminance
)


def calculate_color_distance_lab(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """
    Calculate Euclidean Delta-E distance in CIE L*a*b* colour space.
    Perceptual difference: < 2.3 is JND (Just Noticeable Difference), > 10 is distinctly different.
    """
    l1, a1, b1 = rgb_to_cielab(rgb1[0], rgb1[1], rgb1[2])
    l2, a2, b2 = rgb_to_cielab(rgb2[0], rgb2[1], rgb2[2])
    return math.sqrt((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2)


def calculate_ciede2000(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float], k_L: float = 1.0, k_C: float = 1.0, k_H: float = 1.0) -> float:
    """
    Calculate standard CIEDE2000 color difference between two CIE L*a*b* colors.
    Implements Sharma et al. (2005) formulation.
    """
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_bar = (C1 + C2) / 2.0

    G = 0.5 * (1.0 - math.sqrt((C_bar**7) / (C_bar**7 + 25.0**7)))
    a1_prime = (1.0 + G) * a1
    a2_prime = (1.0 + G) * a2

    C1_prime = math.sqrt(a1_prime**2 + b1**2)
    C2_prime = math.sqrt(a2_prime**2 + b2**2)
    C_bar_prime = (C1_prime + C2_prime) / 2.0

    h1_prime = math.degrees(math.atan2(b1, a1_prime)) % 360.0
    h2_prime = math.degrees(math.atan2(b2, a2_prime)) % 360.0

    if C1_prime == 0 or C2_prime == 0:
        h_bar_prime = h1_prime + h2_prime
    elif abs(h1_prime - h2_prime) <= 180.0:
        h_bar_prime = (h1_prime + h2_prime) / 2.0
    elif (h1_prime + h2_prime) < 360.0:
        h_bar_prime = (h1_prime + h2_prime + 360.0) / 2.0
    else:
        h_bar_prime = (h1_prime + h2_prime - 360.0) / 2.0

    T = (1.0 - 0.17 * math.cos(math.radians(h_bar_prime - 30.0)) +
         0.24 * math.cos(math.radians(2.0 * h_bar_prime)) +
         0.32 * math.cos(math.radians(3.0 * h_bar_prime + 6.0)) -
         0.20 * math.cos(math.radians(4.0 * h_bar_prime - 63.0)))

    delta_h_prime = 0.0
    if C1_prime != 0 and C2_prime != 0:
        if abs(h2_prime - h1_prime) <= 180.0:
            delta_h_prime = h2_prime - h1_prime
        elif h2_prime <= h1_prime:
            delta_h_prime = h2_prime - h1_prime + 360.0
        else:
            delta_h_prime = h2_prime - h1_prime - 360.0

    delta_L_prime = L2 - L1
    delta_C_prime = C2_prime - C1_prime
    delta_H_prime = 2.0 * math.sqrt(C1_prime * C2_prime) * math.sin(math.radians(delta_h_prime / 2.0))

    L_bar = (L1 + L2) / 2.0
    S_L = 1.0 + (0.015 * (L_bar - 50.0)**2) / math.sqrt(20.0 + (L_bar - 50.0)**2)
    S_C = 1.0 + 0.045 * C_bar_prime
    S_H = 1.0 + 0.015 * C_bar_prime * T

    delta_theta = 30.0 * math.exp(-(((h_bar_prime - 275.0) / 25.0)**2))
    R_C = 2.0 * math.sqrt((C_bar_prime**7) / (C_bar_prime**7 + 25.0**7))
    R_T = -math.sin(math.radians(2.0 * delta_theta)) * R_C

    delta_E = math.sqrt(
        (delta_L_prime / (k_L * S_L))**2 +
        (delta_C_prime / (k_C * S_C))**2 +
        (delta_H_prime / (k_H * S_H))**2 +
        R_T * (delta_C_prime / (k_C * S_C)) * (delta_H_prime / (k_H * S_H))
    )
    return delta_E


def calculate_palette_distance(palette_a_colors: List[Tuple[int, int, int]], palette_b_colors: List[Tuple[int, int, int]]) -> float:
    """
    Calculate average minimum perceptual distance between two palettes to detect duplicates.
    """
    if not palette_a_colors or not palette_b_colors:
        return 0.0

    distances = []
    for c_a in palette_a_colors:
        min_d = min(calculate_color_distance_lab(c_a, c_b) for c_b in palette_b_colors)
        distances.append(min_d)

    return float(sum(distances) / len(distances))


def calculate_contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """
    Calculate WCAG standard relative luminance contrast ratio (range: 1.0 to 21.0).
    """
    lum1 = calculate_perceptual_luminance(rgb1[0], rgb1[1], rgb1[2])
    lum2 = calculate_perceptual_luminance(rgb2[0], rgb2[1], rgb2[2])
    l_max = max(lum1, lum2)
    l_min = min(lum1, lum2)
    return round((l_max + 0.05) / (l_min + 0.05), 2)


def generate_monochromatic_harmony(base_rgb: Tuple[int, int, int]) -> Dict[str, Tuple[int, int, int]]:
    """
    Generate monochromatic harmony:
    - Primary wall: base hue, light-to-mid value, gentle saturation
    - Secondary wall / support: lighter tint
    - Accent: deeper shade or richer saturation of same hue
    - Trim / Ceiling: crisp very light tint (LRV > 80%)
    """
    h, s, v = rgb_to_hsv(base_rgb[0], base_rgb[1], base_rgb[2])

    # Primary wall: balanced architectural wall tone
    w_s = min(0.35, max(0.08, s * 0.7))
    w_v = min(0.92, max(0.55, v))
    primary_wall = hsv_to_rgb(h, w_s, w_v)

    # Secondary wall: softer, lighter tint
    sec_s = max(0.04, w_s * 0.5)
    sec_v = min(0.96, w_v + 0.15)
    secondary_wall = hsv_to_rgb(h, sec_s, sec_v)

    # Accent: deeper shade
    acc_s = min(0.65, max(0.25, s * 1.3))
    acc_v = max(0.25, min(0.55, v * 0.65))
    accent = hsv_to_rgb(h, acc_s, acc_v)

    # Trim: crisp architectural white with subtle hue whisper
    trim_s = 0.03
    trim_v = 0.98
    trim = hsv_to_rgb(h, trim_s, trim_v)

    return {
        "primary_wall": primary_wall,
        "secondary_wall": secondary_wall,
        "accent": accent,
        "trim": trim
    }


def generate_analogous_harmony(base_rgb: Tuple[int, int, int], angle: float = 30.0) -> Dict[str, Tuple[int, int, int]]:
    """
    Generate analogous harmony (neighboring hues on colour wheel):
    - Primary wall: base hue adjusted for interior walls
    - Secondary wall: hue - angle (e.g. -30 deg)
    - Accent: hue + angle (e.g. +30 deg) with refined saturation
    - Trim: neutral ivory/alabaster tint
    """
    h, s, v = rgb_to_hsv(base_rgb[0], base_rgb[1], base_rgb[2])

    # Primary wall
    w_s = min(0.32, max(0.10, s * 0.65))
    w_v = min(0.90, max(0.60, v))
    primary_wall = hsv_to_rgb(h, w_s, w_v)

    # Secondary: hue shifted -angle
    h_sec = (h - angle) % 360.0
    sec_s = min(0.28, max(0.08, s * 0.55))
    sec_v = min(0.94, max(0.65, v * 0.95))
    secondary_wall = hsv_to_rgb(h_sec, sec_s, sec_v)

    # Accent: hue shifted +angle
    h_acc = (h + angle) % 360.0
    acc_s = min(0.65, max(0.35, s * 1.25))
    acc_v = max(0.35, min(0.65, v * 0.8))
    accent = hsv_to_rgb(h_acc, acc_s, acc_v)

    # Trim
    trim = hsv_to_rgb(h, 0.03, 0.98)

    return {
        "primary_wall": primary_wall,
        "secondary_wall": secondary_wall,
        "accent": accent,
        "trim": trim
    }


def generate_complementary_harmony(base_rgb: Tuple[int, int, int]) -> Dict[str, Tuple[int, int, int]]:
    """
    Generate complementary harmony:
    - Primary wall: sophisticated muted base
    - Secondary wall: coordinating light tone
    - Accent: exact complement (hue + 180 deg) in a rich, grounded accent
    - Trim: crisp matching trim
    """
    h, s, v = rgb_to_hsv(base_rgb[0], base_rgb[1], base_rgb[2])

    w_s = min(0.30, max(0.08, s * 0.6))
    w_v = min(0.92, max(0.55, v))
    primary_wall = hsv_to_rgb(h, w_s, w_v)

    # Secondary wall
    sec_s = max(0.04, w_s * 0.6)
    sec_v = min(0.95, w_v + 0.12)
    secondary_wall = hsv_to_rgb(h, sec_s, sec_v)

    # Complementary accent (hue + 180)
    h_comp = (h + 180.0) % 360.0
    acc_s = min(0.60, max(0.30, s * 1.1 + 0.15))
    acc_v = max(0.35, min(0.65, v * 0.75))
    accent = hsv_to_rgb(h_comp, acc_s, acc_v)

    # Trim
    trim = hsv_to_rgb((h + 30) % 360.0, 0.02, 0.98)

    return {
        "primary_wall": primary_wall,
        "secondary_wall": secondary_wall,
        "accent": accent,
        "trim": trim
    }


def generate_neutral_accent_harmony(
    neutral_rgb: Tuple[int, int, int],
    accent_rgb: Tuple[int, int, int]
) -> Dict[str, Tuple[int, int, int]]:
    """
    Generate neutral-and-accent harmony:
    - Primary wall: elegant, calming neutral
    - Secondary wall: slightly warmer or cooler tone of the neutral
    - Accent: statement pop derived from extracted room features or desired atmosphere
    - Trim: bright architectural white
    """
    h_n, s_n, v_n = rgb_to_hsv(neutral_rgb[0], neutral_rgb[1], neutral_rgb[2])
    h_a, s_a, v_a = rgb_to_hsv(accent_rgb[0], accent_rgb[1], accent_rgb[2])

    primary_wall = hsv_to_rgb(h_n, min(0.18, max(0.04, s_n)), min(0.94, max(0.68, v_n)))
    secondary_wall = hsv_to_rgb(h_n, min(0.14, max(0.03, s_n * 0.7)), min(0.96, v_n + 0.08))
    accent = hsv_to_rgb(h_a, min(0.70, max(0.30, s_a * 1.15)), max(0.30, min(0.70, v_a * 0.85)))
    trim = (252, 250, 246)

    return {
        "primary_wall": primary_wall,
        "secondary_wall": secondary_wall,
        "accent": accent,
        "trim": trim
    }
