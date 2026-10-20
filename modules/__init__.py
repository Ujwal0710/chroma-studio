"""Modules package for AI Interior Colour Palette Suggester."""
from modules.image_validation import validate_image_bytes, ImageValidationError
from modules.image_processing import (
    pil_to_numpy_rgb,
    numpy_rgb_to_pil,
    rgb_to_hex,
    hex_to_rgb,
    rgb_to_hsv,
    hsv_to_rgb,
    rgb_to_cielab,
    calculate_perceptual_luminance,
    classify_color_characteristics
)
from modules.colour_extraction import extract_dominant_colors
from modules.colour_theory import (
    generate_monochromatic_harmony,
    generate_analogous_harmony,
    generate_complementary_harmony,
    generate_neutral_accent_harmony
)
from modules.palette_engine import generate_recommended_palettes
from modules.wall_segmentation import generate_wall_mask
from modules.room_visualization import (
    apply_luminance_preserving_recolour,
    create_side_by_side_comparison,
    create_split_slider_comparison,
    create_mask_overlay_preview
)
from modules.storage import (
    save_palette,
    list_saved_palettes,
    get_saved_palette_by_id,
    delete_saved_palette,
    init_db
)
from modules.export_service import (
    export_palette_json,
    export_palette_csv,
    generate_swatch_sheet_png,
    generate_text_report
)

__all__ = [
    "validate_image_bytes",
    "ImageValidationError",
    "pil_to_numpy_rgb",
    "numpy_rgb_to_pil",
    "rgb_to_hex",
    "hex_to_rgb",
    "rgb_to_hsv",
    "hsv_to_rgb",
    "rgb_to_cielab",
    "calculate_perceptual_luminance",
    "classify_color_characteristics",
    "extract_dominant_colors",
    "generate_monochromatic_harmony",
    "generate_analogous_harmony",
    "generate_complementary_harmony",
    "generate_neutral_accent_harmony",
    "generate_recommended_palettes",
    "generate_wall_mask",
    "apply_luminance_preserving_recolour",
    "create_side_by_side_comparison",
    "create_split_slider_comparison",
    "create_mask_overlay_preview",
    "save_palette",
    "list_saved_palettes",
    "get_saved_palette_by_id",
    "delete_saved_palette",
    "init_db",
    "export_palette_json",
    "export_palette_csv",
    "generate_swatch_sheet_png",
    "generate_text_report"
]
