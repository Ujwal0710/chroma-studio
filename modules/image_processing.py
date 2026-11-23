"""Image processing, colour space conversions, and optical characteristics."""
import math
from typing import Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image


def pil_to_numpy_rgb(img: Image.Image) -> np.ndarray:
    """Convert PIL RGB image to uint8 NumPy array in RGB channel order."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img, dtype=np.uint8)


def numpy_rgb_to_pil(arr: np.ndarray) -> Image.Image:
    """Convert uint8 NumPy RGB array to PIL Image."""
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB integers [0, 255] to formatted uppercase HEX string."""
    r = max(0, min(255, int(round(r))))
    g = max(0, min(255, int(round(g))))
    b = max(0, min(255, int(round(b))))
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert HEX string to RGB tuple."""
    hex_code = hex_code.strip().lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join([c * 2 for c in hex_code])
    if len(hex_code) != 6:
        raise ValueError(f"Invalid HEX code: {hex_code}")
    return int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)


def calculate_perceptual_luminance(r: int, g: int, b: int) -> float:
    """
    Calculate relative perceptual luminance using ITU-R BT.709 standard.
    Returns float in range [0.0, 1.0].
    """
    # Linearize sRGB components
    def linearize(c: float) -> float:
        c_norm = c / 255.0
        return c_norm / 12.92 if c_norm <= 0.04045 else ((c_norm + 0.055) / 1.055) ** 2.4

    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    Convert RGB [0..255] to HSV (H: [0..360), S: [0..1], V: [0..1]).
    """
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    c_max = max(r_norm, g_norm, b_norm)
    c_min = min(r_norm, g_norm, b_norm)
    diff = c_max - c_min

    # Hue calculation
    if diff == 0:
        h = 0.0
    elif c_max == r_norm:
        h = (60.0 * ((g_norm - b_norm) / diff) + 360.0) % 360.0
    elif c_max == g_norm:
        h = (60.0 * ((b_norm - r_norm) / diff) + 120.0) % 360.0
    else:
        h = (60.0 * ((r_norm - g_norm) / diff) + 240.0) % 360.0

    # Saturation
    s = 0.0 if c_max == 0 else diff / c_max
    v = c_max
    return round(h, 1), round(s, 3), round(v, 3)


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """Convert HSV (H: [0..360), S: [0..1], V: [0..1]) to RGB [0..255]."""
    h = h % 360.0
    c = v * s
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = v - c

    if 0 <= h < 60:
        r_p, g_p, b_p = c, x, 0.0
    elif 60 <= h < 120:
        r_p, g_p, b_p = x, c, 0.0
    elif 120 <= h < 180:
        r_p, g_p, b_p = 0.0, c, x
    elif 180 <= h < 240:
        r_p, g_p, b_p = 0.0, x, c
    elif 240 <= h < 300:
        r_p, g_p, b_p = x, 0.0, c
    else:
        r_p, g_p, b_p = c, 0.0, x

    r = int(round((r_p + m) * 255.0))
    g = int(round((g_p + m) * 255.0))
    b = int(round((b_p + m) * 255.0))
    return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))


def rgb_to_cielab(r: Any, g: Optional[int] = None, b: Optional[int] = None) -> Tuple[float, float, float]:
    """Convert sRGB [0..255] to CIE L*a*b* under D65 illuminant. Accepts (r, g, b) or single tuple/list."""
    if g is None and b is None and isinstance(r, (tuple, list)):
        r, g, b = int(r[0]), int(r[1]), int(r[2])
    else:
        r, g, b = int(r), int(g), int(b)

    # Convert sRGB to linear RGB
    def to_linear(v: float) -> float:
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r_lin = to_linear(r)
    g_lin = to_linear(g)
    b_lin = to_linear(b)

    # sRGB to XYZ (D65)
    x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
    y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
    z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041

    # D65 reference white
    xn, yn, zn = 0.95047, 1.00000, 1.08883

    def f(t: float) -> float:
        delta = 6.0 / 29.0
        return t ** (1.0 / 3.0) if t > delta ** 3 else (t / (3.0 * delta ** 2)) + (4.0 / 29.0)

    fx = f(x / xn)
    fy = f(y / yn)
    fz = f(z / zn)

    l_star = 116.0 * fy - 16.0
    a_star = 500.0 * (fx - fy)
    b_star = 200.0 * (fy - fz)

    return round(l_star, 2), round(a_star, 2), round(b_star, 2)


def cielab_to_rgb(l_star: float, a_star: float, b_star: float) -> Tuple[int, int, int]:
    """Convert CIE L*a*b* under D65 illuminant back to sRGB [0..255]."""
    fy = (float(l_star) + 16.0) / 116.0
    fx = float(a_star) / 500.0 + fy
    fz = fy - float(b_star) / 200.0

    delta = 6.0 / 29.0
    xn, yn, zn = 0.95047, 1.00000, 1.08883

    def finv(t: float) -> float:
        return t ** 3 if t > delta else 3.0 * (delta ** 2) * (t - 4.0 / 29.0)

    x = xn * finv(fx)
    y = yn * finv(fy)
    z = zn * finv(fz)

    # XYZ to linear sRGB
    r_lin = x * 3.2404542 - y * 1.5371385 - z * 0.4985314
    g_lin = -x * 0.9692660 + y * 1.8760108 + z * 0.0415560
    b_lin = x * 0.0556434 - y * 0.2040259 + z * 1.0572252

    def to_srgb(c: float) -> float:
        c = max(0.0, min(1.0, c))
        return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1.0 / 2.4)) - 0.055

    r = int(round(to_srgb(r_lin) * 255.0))
    g = int(round(to_srgb(g_lin) * 255.0))
    b = int(round(to_srgb(b_lin) * 255.0))
    return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))


def calculate_cielab_delta_e(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """Calculate Euclidean Delta-E distance between two CIE L*a*b* coordinates."""
    return math.sqrt((lab1[0] - lab2[0]) ** 2 + (lab1[1] - lab2[1]) ** 2 + (lab1[2] - lab2[2]) ** 2)



def classify_color_characteristics(r: int, g: int, b: int) -> Dict[str, str]:
    """
    Classify a color into:
    - temperature: 'warm', 'cool', 'neutral'
    - saturation: 'neutral', 'muted', 'saturated'
    - lightness: 'dark', 'mid-tone', 'light'
    """
    h, s, v = rgb_to_hsv(r, g, b)
    _, a_star, b_star = rgb_to_cielab(r, g, b)
    lum = calculate_perceptual_luminance(r, g, b)

    # Saturation category
    if s < 0.12 or (abs(a_star) < 7 and abs(b_star) < 7):
        saturation_category = "neutral"
    elif s < 0.45:
        saturation_category = "muted"
    else:
        saturation_category = "saturated"

    # Temperature category
    if saturation_category == "neutral":
        # Check subtle shift in b* or red/blue balance
        if b_star > 4 or (r > b + 10):
            temperature = "warm"
        elif b_star < -4 or (b > r + 10):
            temperature = "cool"
        else:
            temperature = "neutral"
    else:
        # Hue ranges:
        # Warm: 0 to 80 (Red to Yellow-Orange), 330 to 360 (Red-Pink)
        # Cool: 160 to 280 (Cyan, Blue, Violet)
        # Moderate/Transitional: 80 to 160 (Yellow-Green, Green), 280 to 330 (Magenta/Purple)
        if (h <= 85 or h >= 330):
            temperature = "warm"
        elif (160 <= h <= 280):
            temperature = "cool"
        elif (85 < h < 160):
            # Greens: Warm olive vs Cool mint/emerald
            temperature = "warm" if b_star > 5 else "cool"
        else:
            temperature = "cool" if b > r else "warm"

    # Lightness category
    if lum > 0.65 or v > 0.85:
        lightness_category = "light"
    elif lum < 0.20 or v < 0.30:
        lightness_category = "dark"
    else:
        lightness_category = "mid-tone"

    return {
        "temperature": temperature,
        "saturation": saturation_category,
        "lightness": lightness_category
    }


def analyze_image_lighting_and_atmosphere(img: Image.Image) -> Dict[str, Any]:
    """
    Evaluate overall brightness, apparent color temperature tendency,
    and lighting distribution across the room photograph.
    """
    arr = pil_to_numpy_rgb(img)
    # Downsample for quick statistical estimation
    if arr.shape[0] > 400 or arr.shape[1] > 400:
        arr_small = arr[::4, ::4, :]
    else:
        arr_small = arr

    r_ch = arr_small[:, :, 0].astype(np.float32)
    g_ch = arr_small[:, :, 1].astype(np.float32)
    b_ch = arr_small[:, :, 2].astype(np.float32)

    # Luminance matrix
    lum_matrix = (0.2126 * r_ch + 0.7152 * g_ch + 0.0722 * b_ch) / 255.0
    mean_lum = float(np.mean(lum_matrix))
    median_lum = float(np.median(lum_matrix))

    # Temperature metric: Red vs Blue dominance
    r_mean = float(np.mean(r_ch))
    b_mean = float(np.mean(b_ch))
    rb_diff = r_mean - b_mean

    if rb_diff > 12.0:
        temp_tendency = "warm"
        temp_desc = "Warm ambient lighting (incandescent or warm natural sunlight)"
    elif rb_diff < -8.0:
        temp_tendency = "cool"
        temp_desc = "Cool ambient lighting (overcast daylight or cool LED lighting)"
    else:
        temp_tendency = "neutral"
        temp_desc = "Neutral or balanced daylight illumination"

    # Brightness category
    if mean_lum > 0.60:
        brightness_desc = "Bright and well-illuminated room with ample light exposure"
        brightness_level = "bright"
    elif mean_lum < 0.32:
        brightness_desc = "Dimly lit or moody interior space with subdued illumination"
        brightness_level = "dim"
    else:
        brightness_desc = "Moderate, balanced ambient room lighting"
        brightness_level = "medium"

    return {
        "mean_luminance": round(mean_lum, 3),
        "median_luminance": round(median_lum, 3),
        "temperature_tendency": temp_tendency,
        "temperature_description": temp_desc,
        "brightness_level": brightness_level,
        "brightness_description": brightness_desc,
        "r_mean": round(r_mean, 1),
        "b_mean": round(b_mean, 1)
    }
