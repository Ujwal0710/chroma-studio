"""Daylight Simulator: Physically inspired natural lighting conditions preview."""
from PIL import Image
import numpy as np

LIGHTING_CONDITIONS = {
    "Warm Morning Light": {
        "kelvin": "3200K",
        "description": "Soft golden morning sun with high-key ambient warming.",
        "rgb_multiplier": (1.12, 1.04, 0.90),
        "contrast_factor": 1.05,
        "gamma": 0.98
    },
    "Neutral Daylight": {
        "kelvin": "5500K",
        "description": "Crisp balanced midday architectural illumination.",
        "rgb_multiplier": (1.00, 1.00, 1.00),
        "contrast_factor": 1.00,
        "gamma": 1.00
    },
    "Cool Overcast Daylight": {
        "kelvin": "6800K",
        "description": "Soft, diffuse north light with subtle cool cyan undertones.",
        "rgb_multiplier": (0.92, 0.98, 1.10),
        "contrast_factor": 0.95,
        "gamma": 1.02
    },
    "Warm Evening Light": {
        "kelvin": "2700K",
        "description": "Golden hour twilight and warm incandescent ambient glow.",
        "rgb_multiplier": (1.18, 1.02, 0.82),
        "contrast_factor": 1.08,
        "gamma": 0.94
    }
}


def simulate_daylight_lighting(
    image: Image.Image,
    condition_name: str = "Neutral Daylight",
    intensity: float = 0.85
) -> Image.Image:
    """
    Apply a physically inspired daylight simulation to the room photograph.
    Preserves luminance distribution while shifting spectral color balance and tone curve.
    Clearly labeled as an approximate computational simulation.
    """
    condition = LIGHTING_CONDITIONS.get(condition_name, LIGHTING_CONDITIONS["Neutral Daylight"])
    if condition_name == "Neutral Daylight" and intensity >= 0.99:
        return image.copy()
        
    img_arr = np.array(image.convert("RGB"), dtype=np.float32)
    
    # 1. Base ITU-R BT.709 Luminance
    lum = 0.2126 * img_arr[:, :, 0] + 0.7152 * img_arr[:, :, 1] + 0.0722 * img_arr[:, :, 2]
    
    # 2. Spectral shift (interpolated by intensity)
    mult = condition["rgb_multiplier"]
    effective_mult = (
        1.0 + (mult[0] - 1.0) * intensity,
        1.0 + (mult[1] - 1.0) * intensity,
        1.0 + (mult[2] - 1.0) * intensity
    )
    
    shifted = np.empty_like(img_arr)
    shifted[:, :, 0] = img_arr[:, :, 0] * effective_mult[0]
    shifted[:, :, 1] = img_arr[:, :, 1] * effective_mult[1]
    shifted[:, :, 2] = img_arr[:, :, 2] * effective_mult[2]
    
    # 3. Tone curve & contrast adjustment
    gamma = 1.0 + (condition["gamma"] - 1.0) * intensity
    contrast = 1.0 + (condition["contrast_factor"] - 1.0) * intensity
    
    # Normalize to 0-1 for gamma curve
    shifted_norm = np.clip(shifted / 255.0, 0.0, 1.0)
    shifted_gamma = np.power(shifted_norm, gamma)
    
    # Apply soft contrast curve around midpoint 0.5
    shifted_contrast = (shifted_gamma - 0.5) * contrast + 0.5
    
    # 4. Luminance preservation blend
    new_lum = 0.2126 * shifted_contrast[:, :, 0] + 0.7152 * shifted_contrast[:, :, 1] + 0.0722 * shifted_contrast[:, :, 2]
    # Soft ratio to prevent harsh burnouts
    lum_ratio = (lum / 255.0 + 0.05) / (new_lum + 0.05)
    lum_ratio_clipped = np.clip(lum_ratio[:, :, np.newaxis], 0.7, 1.3)
    
    final_arr = shifted_contrast * 255.0 * (0.8 + 0.2 * lum_ratio_clipped)
    final_arr = np.clip(final_arr, 0, 255).astype(np.uint8)
    
    return Image.fromarray(final_arr)
