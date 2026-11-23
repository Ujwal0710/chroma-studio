"""Live Colour Scanner: Multi-space optical color scanning, reticle sampling, and palette extraction."""
from typing import Dict, Any, List, Tuple
import numpy as np
from PIL import Image
import cv2

from modules.image_processing import (
    rgb_to_hex,
    rgb_to_hsv,
    rgb_to_cielab,
    calculate_perceptual_luminance,
    classify_color_characteristics
)
from modules.colour_extraction import match_color_name


class ScannedColorDetail:
    """Complete color specification with multi-space coordinates and naming."""
    def __init__(
        self,
        name: str,
        hex_code: str,
        rgb: Tuple[int, int, int],
        hsv: Tuple[float, float, float],
        lab: Tuple[float, float, float],
        temperature: str,
        luminance: float,
        percentage: float = 0.0,
        notes: str = ""
    ):
        self.name = name
        self.hex = hex_code.upper()
        self.rgb = rgb
        self.hsv = (round(hsv[0], 1), round(hsv[1], 3), round(hsv[2], 3))
        self.lab = (round(lab[0], 2), round(lab[1], 2), round(lab[2], 2))
        self.temperature = temperature
        self.luminance = round(luminance, 3)
        self.percentage = round(percentage, 1)
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "hex": self.hex,
            "rgb": list(self.rgb),
            "hsv": list(self.hsv),
            "lab": list(self.lab),
            "temperature": self.temperature,
            "luminance": self.luminance,
            "percentage": self.percentage,
            "notes": self.notes
        }


def scan_color_at_reticle(
    image: Image.Image,
    reticle_norm_x: float = 0.5,
    reticle_norm_y: float = 0.5,
    sample_radius: int = 5
) -> ScannedColorDetail:
    """
    Sample an optical color reading directly beneath a viewfinder crosshair/reticle.
    Uses localized neighborhood averaging to mitigate camera noise and sensor flicker.
    """
    w, h = image.size
    cx = int(np.clip(reticle_norm_x * w, sample_radius, w - sample_radius - 1))
    cy = int(np.clip(reticle_norm_y * h, sample_radius, h - sample_radius - 1))

    arr = np.array(image.convert("RGB"))
    patch = arr[cy - sample_radius:cy + sample_radius + 1, cx - sample_radius:cx + sample_radius + 1]

    mean_rgb = np.mean(patch, axis=(0, 1))
    r, g, b = int(round(mean_rgb[0])), int(round(mean_rgb[1])), int(round(mean_rgb[2]))
    hex_code = rgb_to_hex(r, g, b)
    name = match_color_name(r, g, b)
    hsv = rgb_to_hsv(r, g, b)
    lab = rgb_to_cielab((r, g, b))
    lum = calculate_perceptual_luminance(r, g, b)
    traits = classify_color_characteristics(r, g, b)

    return ScannedColorDetail(
        name=name,
        hex_code=hex_code,
        rgb=(r, g, b),
        hsv=hsv,
        lab=lab,
        temperature=traits["temperature"],
        luminance=lum,
        percentage=100.0,
        notes=f"Reticle sample at ({cx}px, {cy}px) with {sample_radius}px neighborhood averaging."
    )


def scan_frame_dominant_palette(
    image: Image.Image,
    k_clusters: int = 5,
    filter_extremes: bool = True
) -> List[ScannedColorDetail]:
    """
    Perform real-time cluster extraction from live camera frame to produce a cohesive scanned palette.
    Downscales frame for instant computation (<40ms).
    """
    small = image.resize((240, 180), Image.Resampling.NEAREST)
    arr = np.array(small.convert("RGB"), dtype=np.float32)
    pixels = arr.reshape(-1, 3)

    if filter_extremes:
        # Filter extreme blown-out specular highlights and deep crushed shadows
        lum = 0.2126 * pixels[:, 0] + 0.7152 * pixels[:, 1] + 0.0722 * pixels[:, 2]
        valid_mask = (lum > 22.0) & (lum < 242.0)
        if np.sum(valid_mask) > 100:
            pixels = pixels[valid_mask]

    # Fast MiniBatch-like OpenCV K-means
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    flags = cv2.KMEANS_PP_CENTERS
    _, labels, centers = cv2.kmeans(
        pixels.astype(np.float32),
        k_clusters,
        None,
        criteria,
        3,
        flags
    )

    counts = np.bincount(labels.flatten())
    total = float(len(labels))

    # Sort clusters by area percentage descending
    order = np.argsort(counts)[::-1]
    results: List[ScannedColorDetail] = []

    for idx in order:
        c = centers[idx]
        pct = (counts[idx] / total) * 100.0
        r, g, b = int(round(c[0])), int(round(c[1])), int(round(c[2]))
        hex_code = rgb_to_hex(r, g, b)
        name = match_color_name(r, g, b)
        hsv = rgb_to_hsv(r, g, b)
        lab = rgb_to_cielab((r, g, b))
        lum = calculate_perceptual_luminance(r, g, b)
        traits = classify_color_characteristics(r, g, b)

        results.append(ScannedColorDetail(
            name=name,
            hex_code=hex_code,
            rgb=(r, g, b),
            hsv=hsv,
            lab=lab,
            temperature=traits["temperature"],
            luminance=lum,
            percentage=pct,
            notes=f"Cluster dominant share: {round(pct, 1)}%"
        ))

    return results


def draw_reticle_crosshair(
    image: Image.Image,
    reticle_norm_x: float = 0.5,
    reticle_norm_y: float = 0.5,
    active_color_hex: str = "#242424"
) -> Image.Image:
    """Render a clean architectural crosshair and color ring at the reticle position."""
    w, h = image.size
    cx = int(reticle_norm_x * w)
    cy = int(reticle_norm_y * h)

    out_bgr = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)

    # Reticle styling
    crosshair_len = 22
    ring_radius = 16
    cv2.circle(out_bgr, (cx, cy), ring_radius, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.circle(out_bgr, (cx, cy), ring_radius - 2, (30, 30, 30), 1, cv2.LINE_AA)

    # Crosshairs (outer lines leaving center open)
    cv2.line(out_bgr, (cx - crosshair_len, cy), (cx - ring_radius - 4, cy), (255, 255, 255), 2)
    cv2.line(out_bgr, (cx + ring_radius + 4, cy), (cx + crosshair_len, cy), (255, 255, 255), 2)
    cv2.line(out_bgr, (cx, cy - crosshair_len), (cx, cy - ring_radius - 4), (255, 255, 255), 2)
    cv2.line(out_bgr, (cx, cy + ring_radius + 4), (cx, cy + crosshair_len), (255, 255, 255), 2)

    return Image.fromarray(cv2.cvtColor(out_bgr, cv2.COLOR_BGR2RGB))
