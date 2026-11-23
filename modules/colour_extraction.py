"""Dominant colour extraction using K-Means clustering and perceptual classification."""
import math
from typing import List, Any
import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import MiniBatchKMeans

from models.schemas import ColorSwatch, ExtractedColorAnalysis
from modules.image_processing import (
    pil_to_numpy_rgb,
    rgb_to_hex,
    rgb_to_hsv,
    rgb_to_cielab,
    cielab_to_rgb,
    calculate_perceptual_luminance,
    classify_color_characteristics,
    analyze_image_lighting_and_atmosphere
)

# Reference dictionary of interior design color names
DESIGN_COLOR_NAMES = [
    # Neutrals / Whites / Creams
    ((250, 248, 245), "Alabaster White"),
    ((245, 240, 230), "Warm Linen"),
    ((238, 232, 220), "Creamy Travertine"),
    ((225, 218, 205), "Pale Oat"),
    ((210, 200, 185), "Soft Greige"),
    ((190, 180, 168), "Warm Taupe"),
    ((160, 150, 140), "Muted Putty"),
    ((120, 110, 100), "Earthy Umber"),
    ((75, 68, 62), "Deep Espresso"),
    ((40, 36, 32), "Charcoal Black"),
    ((240, 242, 245), "Chalk Cool White"),
    ((215, 220, 225), "Morning Mist Gray"),
    ((170, 175, 180), "Slate Gray"),
    ((100, 105, 112), "Architectural Charcoal"),

    # Warm Earth Tones / Terracottas / Woods
    ((205, 133, 90), "Sunbaked Terracotta"),
    ((180, 105, 65), "Rich Clay"),
    ((195, 145, 95), "Sandstone Ochre"),
    ((165, 115, 75), "Warm Walnut"),
    ((140, 85, 50), "Caramel Leather"),
    ((215, 165, 120), "Desert Sand"),
    ((230, 185, 150), "Soft Peach Linen"),
    ((145, 70, 45), "Rustic Sienna"),
    ((110, 55, 35), "Roasted Chestnut"),

    # Greens / Botanicals / Olives
    ((155, 170, 145), "Muted Sage"),
    ((120, 138, 110), "Earthy Olive"),
    ((85, 105, 80), "Forest Moss"),
    ((185, 198, 180), "Eucalyptus Gray"),
    ((60, 78, 60), "Deep Pine"),
    ((175, 180, 155), "Dried Herb"),
    ((135, 145, 125), "Celadon Stone"),

    # Blues / Coastal / Mineral
    ((150, 175, 190), "Coastal Mist Blue"),
    ((110, 140, 160), "Weathered Denim"),
    ((70, 95, 115), "Nordic Slate Blue"),
    ((45, 65, 85), "Midnight Navy"),
    ((185, 205, 215), "Pale Sky Linen"),
    ((80, 110, 120), "Teal Mineral"),

    # Accents / Yellows / Warm Highlights
    ((225, 180, 90), "Antique Brass"),
    ((200, 150, 60), "Burnished Gold"),
    ((180, 75, 65), "Spiced Paprika"),
    ((150, 60, 75), "Muted Wine / Burgundy")
]


def match_color_name(r: int, g: int, b: int) -> str:
    """Find the closest descriptive interior design color name using Lab Euclidean distance."""
    l1, a1, b1 = rgb_to_cielab(r, g, b)
    min_dist = float("inf")
    best_name = "Custom Tone"

    for (ref_r, ref_g, ref_b), name in DESIGN_COLOR_NAMES:
        l2, a2, b2 = rgb_to_cielab(ref_r, ref_g, ref_b)
        dist = math.sqrt((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2)
        if dist < min_dist:
            min_dist = dist
            best_name = name

    return best_name


def get_closest_interior_color_name(color_input: Any) -> str:
    """Convenience helper to match color name from hex string or RGB tuple."""
    if isinstance(color_input, str):
        h = color_input.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    elif isinstance(color_input, (tuple, list)):
        r, g, b = int(color_input[0]), int(color_input[1]), int(color_input[2])
    else:
        return "Interior Tone"
    return match_color_name(r, g, b)



def extract_dominant_colors(
    img: Image.Image,
    num_colors: int = 7,
    filter_extremes: bool = True,
    sample_size: int = 15000
) -> ExtractedColorAnalysis:
    """
    Extract representative dominant colors and their proportions using K-Means clustering.
    Filters extreme blown-out highlights (#FFFFFF) and noisy pitch black (#000000).
    """
    arr = pil_to_numpy_rgb(img)
    h, w, c = arr.shape
    pixels = arr.reshape(-1, 3).astype(np.float32)

    # Filter out extreme blown-out specular highlights or absolute black noise
    if filter_extremes:
        luminances = 0.2126 * pixels[:, 0] + 0.7152 * pixels[:, 1] + 0.0722 * pixels[:, 2]
        # Keep pixels between luminance 8 and 248 to avoid sensor clip noise
        valid_mask = (luminances >= 8.0) & (luminances <= 248.0)
        if np.sum(valid_mask) > (sample_size // 2):
            pixels = pixels[valid_mask]

    total_pixels = len(pixels)

    # Subsample if large for fast deterministic K-Means
    if total_pixels > sample_size:
        np.random.seed(42)
        indices = np.random.choice(total_pixels, size=sample_size, replace=False)
        sample_pixels = pixels[indices]
    else:
        sample_pixels = pixels

    # Convert sample pixels to CIE L*a*b* space for perceptually uniform clustering
    sample_rgb_norm = np.ascontiguousarray((sample_pixels / 255.0).reshape(1, -1, 3), dtype=np.float32)
    sample_lab = cv2.cvtColor(sample_rgb_norm, cv2.COLOR_RGB2Lab).reshape(-1, 3)

    # Run MiniBatchKMeans in CIELAB space with fixed seed
    kmeans = MiniBatchKMeans(
        n_clusters=num_colors,
        random_state=42,
        batch_size=2048,
        n_init=3
    )
    labels = kmeans.fit_predict(sample_lab)
    centers_lab = kmeans.cluster_centers_

    # Calculate cluster frequencies
    counts = np.bincount(labels, minlength=num_colors)
    proportions = counts / len(sample_pixels)

    # Sort clusters by proportion descending
    sorted_order = np.argsort(proportions)[::-1]

    # Calculate exact percentages summing to 100.0%
    raw_props = [float(proportions[idx]) * 100.0 for idx in sorted_order]
    rounded_props = [round(p, 1) for p in raw_props]
    diff = round(100.0 - sum(rounded_props), 1)
    if diff != 0 and len(rounded_props) > 0:
        rounded_props[0] = round(rounded_props[0] + diff, 1)

    swatches: List[ColorSwatch] = []
    neutral_count = 0
    warm_count = 0
    cool_count = 0
    saturations: List[float] = []

    for rank, (idx, prop) in enumerate(zip(sorted_order, rounded_props)):
        lab_c = centers_lab[idx]
        r, g, b = cielab_to_rgb(float(lab_c[0]), float(lab_c[1]), float(lab_c[2]))

        hex_code = rgb_to_hex(r, g, b)

        # Characteristics
        traits = classify_color_characteristics(r, g, b)
        temp = traits["temperature"]
        sat_cat = traits["saturation"]
        h, s, v = rgb_to_hsv(r, g, b)
        saturations.append(s)

        if temp == "warm":
            warm_count += 1
        elif temp == "cool":
            cool_count += 1
        else:
            neutral_count += 1

        color_name = match_color_name(r, g, b)
        lum = round(calculate_perceptual_luminance(r, g, b), 3)

        role = f"Dominant #{rank + 1} ({prop}%)"
        description = f"{traits['lightness'].capitalize()} {temp} tone, {sat_cat} saturation."

        swatches.append(ColorSwatch(
            hex=hex_code,
            rgb=(r, g, b),
            role=role,
            name=color_name,
            percentage=prop,
            temperature=temp,
            saturation_category=sat_cat,
            luminance=lum,
            description=description
        ))

    # Image-wide lighting and atmosphere
    lighting_info = analyze_image_lighting_and_atmosphere(img)
    mean_sat = round(float(np.mean(saturations)), 3) if saturations else 0.2

    return ExtractedColorAnalysis(
        dominant_colors=swatches,
        overall_brightness=lighting_info["mean_luminance"],
        overall_temperature_tendency=lighting_info["temperature_tendency"],
        mean_saturation=mean_sat,
        neutral_count=neutral_count,
        warm_count=warm_count,
        cool_count=cool_count,
        lighting_condition_estimate=f"{lighting_info['brightness_description']} with {lighting_info['temperature_description']}."
    )
