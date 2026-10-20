"""Semantic Wall Editing: Multi-surface plane segmentation and targeted recolouring."""
from typing import Dict, Any, Tuple
from PIL import Image
import numpy as np
import cv2

from modules.wall_segmentation import generate_wall_mask
from modules.room_visualization import apply_luminance_preserving_recolour


def generate_semantic_surface_masks(
    original_img: Image.Image,
    base_wall_mask: np.ndarray
) -> Dict[str, np.ndarray]:
    """
    Generate sub-region masks from base wall mask:
    - 'Main Wall': dominant central/lateral wall planes.
    - 'Accent Wall': primary focal wall section (right/left quadrant).
    - 'Ceiling / Crown': upper perimeter region.
    """
    h, w = base_wall_mask.shape
    
    # 1. Ceiling / Crown: top 22% of detected upper structure
    ceiling_mask = np.zeros_like(base_wall_mask)
    ceiling_cutoff = int(h * 0.22)
    ceiling_mask[:ceiling_cutoff, :] = base_wall_mask[:ceiling_cutoff, :]
    
    # 2. Accent Wall: rightmost 45% of remaining wall mask
    accent_mask = np.zeros_like(base_wall_mask)
    split_x = int(w * 0.55)
    accent_mask[ceiling_cutoff:, split_x:] = base_wall_mask[ceiling_cutoff:, split_x:]
    
    # 3. Main Wall: remainder of wall mask
    main_wall_mask = base_wall_mask.copy()
    main_wall_mask[:ceiling_cutoff, :] = 0
    main_wall_mask[:, split_x:] = 0
    
    return {
        "Main Wall": main_wall_mask,
        "Accent Wall": accent_mask,
        "Ceiling / Upper Plane": ceiling_mask,
        "All Wall Surfaces": base_wall_mask
    }


def recolour_semantic_surface(
    original_img: Image.Image,
    surface_mask: np.ndarray,
    target_rgb: Tuple[int, int, int],
    intensity: float = 0.85
) -> Image.Image:
    """Apply luminance-preserving paint to the specified semantic surface mask."""
    return apply_luminance_preserving_recolour(
        original_img=original_img,
        wall_mask=surface_mask,
        target_rgb=target_rgb,
        intensity=intensity
    )
