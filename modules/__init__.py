"""Modules package for CHROMA STUDIO AI."""
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
from modules.auth import (
    hash_password,
    verify_password,
    register_user,
    authenticate_user,
    initiate_password_reset,
    complete_password_reset,
    change_user_password
)
from modules.subscription_service import (
    get_user_subscription,
    update_user_subscription,
    check_entitlement,
    record_usage_metric,
    get_user_usage,
    verify_razorpay_payment_signature,
    verify_razorpay_webhook_signature,
    process_payment_webhook,
    execute_test_sandbox_checkout
)
from modules.chroma_memory import (
    get_chroma_memory,
    record_favorite_palette,
    record_rejected_palette,
    clear_chroma_memory,
    evaluate_chroma_memory_influence
)
from modules.chroma_dna import generate_chroma_dna
from modules.design_timeline import (
    save_timeline_version,
    list_project_timeline,
    get_timeline_version
)
from modules.harmony_explorer import explore_color_harmonies
from modules.daylight_simulator import simulate_daylight_lighting
from modules.material_palettes import evaluate_material_compatibility, ALL_MATERIALS
from modules.colour_swap import swap_palette_color
from modules.paint_estimator import estimate_paint_quantity
from modules.semantic_wall import generate_semantic_surface_masks, recolour_semantic_surface

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
    "generate_text_report",
    "hash_password",
    "verify_password",
    "register_user",
    "authenticate_user",
    "initiate_password_reset",
    "complete_password_reset",
    "change_user_password",
    "get_user_subscription",
    "update_user_subscription",
    "check_entitlement",
    "record_usage_metric",
    "get_user_usage",
    "verify_razorpay_payment_signature",
    "verify_razorpay_webhook_signature",
    "process_payment_webhook",
    "execute_test_sandbox_checkout",
    "get_chroma_memory",
    "record_favorite_palette",
    "record_rejected_palette",
    "clear_chroma_memory",
    "evaluate_chroma_memory_influence",
    "generate_chroma_dna",
    "save_timeline_version",
    "list_project_timeline",
    "get_timeline_version",
    "explore_color_harmonies",
    "simulate_daylight_lighting",
    "evaluate_material_compatibility",
    "ALL_MATERIALS",
    "swap_palette_color",
    "estimate_paint_quantity",
    "generate_semantic_surface_masks",
    "recolour_semantic_surface"
]
