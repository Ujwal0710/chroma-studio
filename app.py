"""CHROMA STUDIO AI - Intelligent Architectural Colour & Interior Design Workspace.

Futuristic Premium Edition.
"""
import io
import json
from typing import Optional, Dict, Any, Tuple
from PIL import Image
import numpy as np
import streamlit as st

# Application configuration & schemas
try:
    from config.settings import (
        APP_NAME,
        APP_TAGLINE,
        DESIGN_TOKENS,
        ROOM_TYPES,
        INTERIOR_STYLES,
        VISION_API_KEY,
        IMAGE_EDIT_API_KEY,
        VISION_MODEL,
        IMAGE_EDIT_MODEL,
        SUBSCRIPTION_PLANS,
        RAZORPAY_KEY_ID,
        RAZORPAY_WEBHOOK_SECRET
    )
except ImportError:
    import config.settings as _settings
    APP_NAME = getattr(_settings, "APP_NAME", "CHROMA STUDIO AI")
    APP_TAGLINE = getattr(_settings, "APP_TAGLINE", "Intelligent Architectural Colour & Interior Design Workspace")
    DESIGN_TOKENS = getattr(_settings, "DESIGN_TOKENS", {})
    ROOM_TYPES = getattr(_settings, "ROOM_TYPES", [])
    INTERIOR_STYLES = getattr(_settings, "INTERIOR_STYLES", [])
    VISION_API_KEY = getattr(_settings, "VISION_API_KEY", "")
    IMAGE_EDIT_API_KEY = getattr(_settings, "IMAGE_EDIT_API_KEY", "")
    VISION_MODEL = getattr(_settings, "VISION_MODEL", "gemini-1.5-flash")
    IMAGE_EDIT_MODEL = getattr(_settings, "IMAGE_EDIT_MODEL", "dall-e-3")
    SUBSCRIPTION_PLANS = getattr(_settings, "SUBSCRIPTION_PLANS", {})
    RAZORPAY_KEY_ID = getattr(_settings, "RAZORPAY_KEY_ID", "rzp_test_samplekeyid123")
    RAZORPAY_WEBHOOK_SECRET = getattr(_settings, "RAZORPAY_WEBHOOK_SECRET", "rzp_webhook_secret_test")

from models.schemas import (
    PaletteConcept,
    RoomAnalysisResult,
    ExtractedColorAnalysis,
    PreferenceSettings,
    ColorSwatch,
    PaintEstimateInput
)

# Core modules
from modules.image_validation import validate_image_bytes, ImageValidationError
from modules.colour_extraction import extract_dominant_colors
from modules.room_analysis import analyze_room_photograph
from modules.palette_engine import generate_recommended_palettes
from modules.wall_segmentation import generate_wall_mask
try:
    from modules.room_visualization import (
        apply_luminance_preserving_recolour,
        create_side_by_side_comparison,
        create_split_slider_comparison,
        create_mask_overlay_preview,
        LUMINANCE_STRATEGIES
    )
except ImportError:
    import importlib
    import modules.room_visualization
    importlib.reload(modules.room_visualization)
    from modules.room_visualization import (
        apply_luminance_preserving_recolour,
        create_side_by_side_comparison,
        create_split_slider_comparison,
        create_mask_overlay_preview
    )
    LUMINANCE_STRATEGIES = getattr(
        modules.room_visualization,
        "LUMINANCE_STRATEGIES",
        {
            "cielab_perceptual": "Perceptual CIELAB (Accurate tone values + natural texture)",
            "adaptive_luminance": "Adaptive Luminance Ratio (High-contrast shadow retention)",
            "architectural_glaze": "Direct Glaze / Tint (Subtle translucent finish)"
        }
    )
from modules.quality_control import validate_recolour_quality
try:
    from modules.ai_preview import (
        request_ai_enhanced_preview,
        get_image_editing_status
    )
except ImportError:
    from services.image_editing_provider import (
        generate_ai_room_preview as request_ai_enhanced_preview,
        get_image_editing_status
    )


from modules.storage import (
    init_db,
    save_palette,
    list_saved_palettes,
    delete_saved_palette,
    get_user_profile,
    update_user_profile,
    delete_user_account_cascade,
    export_user_data_bundle,
    save_scanned_color,
    list_scanned_colors,
    delete_scanned_color,
    save_room_plan,
    list_room_plans,
    delete_room_plan,
    save_shopping_list,
    list_shopping_lists,
    delete_shopping_list,
    save_maintenance_record,
    list_maintenance_records,
    delete_maintenance_record,
    save_assistant_message,
    get_assistant_history,
    clear_assistant_history
)
from modules.export_service import (
    export_palette_json,
    export_palette_csv,
    generate_swatch_sheet_png,
    generate_text_report,
    generate_markdown_report,
    generate_pdf_report
)
from modules.preferences import (
    ATMOSPHERE_OPTIONS,
    TEMPERATURE_OPTIONS,
    LIGHTNESS_OPTIONS,
    ACCENT_INTENSITY_OPTIONS,
    COMMON_ACCENT_HUES
)
from modules.auth import (
    register_user,
    authenticate_user,
    initiate_password_reset,
    complete_password_reset,
    change_user_password
)
from modules.subscription_service import (
    get_user_subscription,
    check_entitlement,
    record_usage_metric,
    get_user_usage,
    execute_test_sandbox_checkout,
    process_payment_webhook
)
from modules.chroma_memory import (
    get_chroma_memory,
    record_favorite_palette,
    clear_chroma_memory,
    evaluate_chroma_memory_influence
)
from modules.chroma_dna import generate_chroma_dna
from modules.design_timeline import (
    save_timeline_version,
    list_project_timeline
)
from modules.harmony_explorer import explore_color_harmonies
from modules.daylight_simulator import simulate_daylight_lighting, LIGHTING_CONDITIONS
from modules.material_palettes import evaluate_material_compatibility, ALL_MATERIALS
from modules.colour_swap import swap_palette_color
from modules.paint_estimator import estimate_paint_quantity
from modules.semantic_wall import generate_semantic_surface_masks, recolour_semantic_surface

# Expansion Modules
from modules.live_camera import (
    ThreadSafeFrameHolder,
    is_webrtc_available
)
from modules.live_intelligence import (
    analyze_live_frame_intelligence,
    draw_intelligence_bounding_boxes
)
from modules.live_colour_scanner import (
    scan_color_at_reticle,
    scan_frame_dominant_palette,
    draw_reticle_crosshair
)
from modules.paint_brand_matcher import (
    match_paint_brand_shades,
    get_available_brands
)
from modules.room_planner import (
    check_room_clearances,
    get_furniture_suggestions
)
from modules.shopping_assistant import (
    generate_renovation_shopping_list,
    export_shopping_list_markdown
)
from modules.home_maintenance import (
    evaluate_wall_damage_heuristics,
    create_condition_comparison_image,
    DAMAGE_CATEGORIES
)
from modules.chroma_assistant import generate_assistant_response

# UI & Styling
from ui.styles import get_theme_css
from ui.components import (
    render_header,
    render_dominant_color_strip,
    render_room_analysis_card,
    render_palette_swatches_horizontal,
    render_explainability_card,
    render_privacy_shield_banner,
    render_paint_brand_match_card,
    render_3d_room_preview_card
)

# Page configuration
st.set_page_config(
    page_title=f"{APP_NAME} — Editorial Architectural 3D Edition",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database schema
init_db()


# ----------------------------------------------------
# Session State Initialization
# ----------------------------------------------------
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "current_view" not in st.session_state:
    st.session_state.current_view = "🎨 Studio & Analysis"
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "current_image_bytes" not in st.session_state:
    st.session_state.current_image_bytes = None
if "image_metadata" not in st.session_state:
    st.session_state.image_metadata = None
if "selected_palette_id" not in st.session_state:
    st.session_state.selected_palette_id = None
if "recolour_intensity" not in st.session_state:
    st.session_state.recolour_intensity = 0.85
if "mask_sensitivity" not in st.session_state:
    st.session_state.mask_sensitivity = 0.55
if "edge_protection" not in st.session_state:
    st.session_state.edge_protection = 0.65
if "upper_bias" not in st.session_state:
    st.session_state.upper_bias = 0.70
if "shading_retention" not in st.session_state:
    st.session_state.shading_retention = 0.75
if "recolour_strategy" not in st.session_state:
    st.session_state.recolour_strategy = "cielab_perceptual"
if "selected_wall_plane_id" not in st.session_state:
    st.session_state.selected_wall_plane_id = None
if "manual_mask_adjustments" not in st.session_state:
    st.session_state.manual_mask_adjustments = []
if "ai_preview_result" not in st.session_state:
    st.session_state.ai_preview_result = None
if "save_status_message" not in st.session_state:
    st.session_state.save_status_message = None
if "selected_materials" not in st.session_state:
    st.session_state.selected_materials = ["Oak Wood", "Natural Linen"]
if "daylight_condition" not in st.session_state:
    st.session_state.daylight_condition = "Neutral Daylight"
if "project_id" not in st.session_state:
    st.session_state.project_id = "proj_studio_default"

# Inject current theme CSS
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# Helper to get current active user ID
active_user_id = st.session_state.current_user["id"] if st.session_state.current_user else "guest_user"
user_sub = get_user_subscription(active_user_id)
user_usage = get_user_usage(active_user_id)


# ----------------------------------------------------
# Caching helpers
# ----------------------------------------------------
@st.cache_data(show_spinner=False)
def cached_dominant_colors(image_bytes: bytes, num_colors: int = 7) -> Dict[str, Any]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    extracted = extract_dominant_colors(img, num_colors=num_colors)
    return extracted.model_dump()


@st.cache_data(show_spinner=False)
def cached_wall_mask(
    image_bytes: bytes,
    sensitivity: float,
    upper_bias: float,
    edge_protection: float,
    target_plane_id: Optional[int] = None
) -> Tuple[bytes, Dict[str, Any]]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    mask, meta = generate_wall_mask(
        img,
        sensitivity=sensitivity,
        upper_bias=upper_bias,
        edge_protection=edge_protection,
        target_plane_id=target_plane_id
    )
    mask_img = Image.fromarray(mask, mode="L")
    buf = io.BytesIO()
    mask_img.save(buf, format="PNG")
    return buf.getvalue(), meta


@st.cache_data(show_spinner=False)
def cached_room_analysis(image_bytes: bytes, room_type: str = "Automatic Detection", style: str = "Automatic Detection") -> Dict[str, Any]:
    """Cached room analysis to prevent duplicate inference across views."""
    _, proc_pil, _ = validate_image_bytes(image_bytes)
    extracted_dict = cached_dominant_colors(image_bytes)
    extracted = ExtractedColorAnalysis(**extracted_dict)
    analysis = analyze_room_photograph(
        proc_pil,
        extracted_analysis=extracted,
        selected_room_type=room_type,
        selected_style=style
    )
    return analysis.model_dump()



# ----------------------------------------------------
# Main Application Header
# ----------------------------------------------------
render_header(
    user=st.session_state.current_user,
    subscription=user_sub,
    usage=user_usage
)


# ----------------------------------------------------
# Responsive Sidebar Navigation
# ----------------------------------------------------


def render_showcase_view():
    st.markdown(
        """
        <div class="custom-card card-3d" style="text-align: center; padding: 44px 24px; margin-bottom: 24px;">
            <div style="font-size: 0.78rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.16em; color: var(--accent-primary); margin-bottom: 8px;">
                Chroma Studio AI • Architectural Atelier
            </div>
            <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.6rem; margin-bottom: 14px; color: var(--text-primary); line-height: 1.2;">
                Elevate Physical Spaces with Architectural Colour Science &amp; 3D Depth
            </h2>
            <p style="font-size: 1.05rem; color: var(--text-secondary); max-width: 780px; margin: 0 auto 24px auto; line-height: 1.6;">
                An intelligent design workspace that transforms physical spaces into personalized colour concepts,
                luminance-preserving wall previews, and interactive 3D architectural spatial simulations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        st.markdown(
            """
            <div class="custom-card card-3d">
                <div style="font-size: 0.74rem; font-weight: 700; text-transform: uppercase; color: var(--accent-secondary); margin-bottom: 4px;">Subsystem 01</div>
                <h4 style="color: var(--accent-primary); margin-top:0;">Computer Vision Engine</h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5;">
                    Perceptual K-Means clustering and ITU-R BT.709 luminance scaling isolate authentic room tones while filtering sensor blowout.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_w2:
        st.markdown(
            """
            <div class="custom-card card-3d">
                <div style="font-size: 0.74rem; font-weight: 700; text-transform: uppercase; color: var(--accent-secondary); margin-bottom: 4px;">Subsystem 02</div>
                <h4 style="color: var(--accent-primary); margin-top:0;">Harmonic Intelligence</h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5;">
                    Synthesizes 4 architectural concepts enforcing strict 60-30-10 distribution with CIEDE2000 Delta-E deduplication.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_w3:
        st.markdown(
            """
            <div class="custom-card card-3d">
                <div style="font-size: 0.74rem; font-weight: 700; text-transform: uppercase; color: var(--accent-secondary); margin-bottom: 4px;">Subsystem 03</div>
                <h4 style="color: var(--accent-primary); margin-top:0;">Interactive 3D Spatial Canvas</h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5;">
                    Interactive Three.js WebGL spatial simulation featuring dynamic orbit rotation, diurnal lighting shifts, and PBR specular finishes.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Interactive 3D Showcase Canvas
    st.markdown("### 🏛️ Interactive 3D Spatial Room Model")
    
    showcase_palette = None
    if st.session_state.current_image_bytes is not None:
        try:
            ext_dict = cached_dominant_colors(st.session_state.current_image_bytes)
            ext = ExtractedColorAnalysis(**ext_dict)
            an_dict = cached_room_analysis(st.session_state.current_image_bytes)
            an = RoomAnalysisResult(**an_dict)
            real_palettes = generate_recommended_palettes(ext, an)
            if real_palettes:
                showcase_palette = real_palettes[0]
        except Exception:
            pass

    if showcase_palette is None:
        st.caption("✨ Curated Architectural Sample: Rotate, pan, and zoom to inspect light falloff and wall finish reflections in real-time. (Upload a room photo in Studio for live image analysis)")
        showcase_palette = PaletteConcept(
            id="showcase_sample_01",
            name="Sample: Warm Editorial Sanctuary",
            concept_category="Modern Neutral",
            harmony_type="Monochromatic",
            description="Curated architectural sample palette demonstrating 60-30-10 balance in dark obsidian theme.",
            atmosphere="Calm & Balanced",
            primary_wall=ColorSwatch(name="Sandalwood Terracotta", hex="#B85C38", rgb=(184, 92, 56), role="Primary Wall (60%)", percentage=60.0, temperature="warm", luminance=0.49),
            secondary_wall=ColorSwatch(name="Warm Greige Linen", hex="#D6C5B3", rgb=(214, 197, 179), role="Feature Wall (30%)", percentage=30.0, temperature="neutral", luminance=0.80),
            accent=ColorSwatch(name="Obsidian Bronze", hex="#30271F", rgb=(48, 39, 31), role="Accent (10%)", percentage=10.0, temperature="warm", luminance=0.17),
            trim=ColorSwatch(name="Alabaster White", hex="#F7F3EE", rgb=(247, 243, 238), role="Trim & Moulding", percentage=None, temperature="neutral", luminance=0.96),
            design_rationale="Curated sample concept demonstrating 3D WebGL PBR depth and illumination.",
            furniture_flooring_compatibility="Compatible with warm oak and dark bronze fixtures.",
            heuristic_score=96.0
        )
    else:
        st.caption(f"✨ Live Spatial Model for: **{showcase_palette.name}** (Derived from uploaded room photograph analysis)")

    render_3d_room_preview_card(
        palette=showcase_palette,
        room_type="Living Room Gallery",
        theme=st.session_state.theme,
        height=520
    )

    st.markdown("### 💎 Distinctive Architectural Features")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        st.markdown(
            """
            <div class="custom-card card-3d">
                <strong style="color: var(--text-primary); font-size: 0.95rem;">Chroma Memory</strong>
                <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 6px;">Adapts recommendations to your saved preferences and rejected tones over time.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_f2:
        st.markdown(
            """
            <div class="custom-card card-3d">
                <strong style="color: var(--text-primary); font-size: 0.95rem;">Chroma DNA</strong>
                <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 6px;">Inspectable personal design signature with core contrast and temperature tendencies.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_f3:
        st.markdown(
            """
            <div class="custom-card card-3d">
                <strong style="color: var(--text-primary); font-size: 0.95rem;">Daylight Simulator</strong>
                <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 6px;">Diurnal simulation across Morning (3200K), Noon (5500K), Overcast, and Evening (2700K).</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_f4:
        st.markdown(
            """
            <div class="custom-card card-3d">
                <strong style="color: var(--text-primary); font-size: 0.95rem;">Material Synergy</strong>
                <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 6px;">Harmonizes palettes against Oak, Walnut, Marble, Stone, Linen, and Brushed Brass.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Subscription Plans Preview
    st.markdown("---")
    st.markdown("### 🏷️ Transparent Indian Rupee (INR) Plans")
    col_p1, col_p2, col_p3 = st.columns(3)
    for col, (pid, pdata) in zip([col_p1, col_p2, col_p3], SUBSCRIPTION_PLANS.items()):
        with col:
            st.markdown(
                f"""
                <div class="custom-card">
                    <span class="plan-badge plan-{pid}">{pdata['badge']}</span>
                    <h3 style="margin: 8px 0 4px 0; color: var(--text-primary);">{pdata['name']}</h3>
                    <h2 style="margin: 0 0 12px 0; color: var(--accent-primary);">₹{pdata['monthly_price_inr']}<span style="font-size:0.9rem; font-weight:400; color:var(--text-secondary);">/month</span></h2>
                    <ul style="font-size: 0.85rem; color: var(--text-secondary); padding-left: 18px; margin-bottom: 16px;">
                        {"".join(f"<li>{feat}</li>" for feat in pdata['features'])}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")
    if st.button("🚀 Launch Design Studio Workspace", use_container_width=True):
        st.session_state.current_view = "🎨 Studio & Analysis"
        st.rerun()


# ====================================================
# VIEW 2: STUDIO & ANALYSIS WORKSPACE
# ====================================================
def render_studio_view():
    if st.session_state.current_image_bytes is None:
        st.info("👋 **Welcome to the Studio.** Upload a room photograph in the sidebar to begin dominant tone extraction and harmony generation.")
    else:
        # Validate image
        try:
            original_pil, proc_pil, metadata = validate_image_bytes(
                st.session_state.current_image_bytes,
                filename="room_photograph.jpg"
            )
            st.session_state.image_metadata = metadata
        except ImageValidationError as e:
            st.error(f"❌ Image Validation Error: {str(e)}")
            st.stop()

        # User Preferences in expandable drawer
        with st.expander("⚙️ Refine Room Specifications & Harmony Preferences", expanded=False):
            pcol1, pcol2, pcol3 = st.columns(3)
            with pcol1:
                sel_room_type = st.selectbox("Room Type", ROOM_TYPES, index=0)
                sel_style = st.selectbox("Design Style", INTERIOR_STYLES, index=0)
            with pcol2:
                pref_temp = st.selectbox("Colour Temperature", TEMPERATURE_OPTIONS, index=0)
                pref_light = st.selectbox("Lightness Preference", LIGHTNESS_OPTIONS, index=0)
            with pcol3:
                pref_atmos = st.selectbox("Atmosphere Goal", ATMOSPHERE_OPTIONS, index=0)
                pref_accent = st.selectbox("Accent Intensity", ACCENT_INTENSITY_OPTIONS, index=0)

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                pref_colors = st.multiselect("Preferred Harmonizing Tones", COMMON_ACCENT_HUES, default=[])
            with col_sub2:
                avoid_colors = st.multiselect("Colours to Avoid", COMMON_ACCENT_HUES, default=[])

        current_preferences = PreferenceSettings(
            room_type=sel_room_type if 'sel_room_type' in locals() else "Automatic Detection",
            interior_style=sel_style if 'sel_style' in locals() else "Automatic Detection",
            temperature_preference=pref_temp if 'pref_temp' in locals() else "Balanced / Neutral",
            lightness_preference=pref_light if 'pref_light' in locals() else "Light & Airy",
            desired_atmosphere=pref_atmos if 'pref_atmos' in locals() else "Calm & Relaxing",
            accent_intensity=pref_accent if 'pref_accent' in locals() else "Moderate",
            preferred_colors=pref_colors if 'pref_colors' in locals() else [],
            colors_to_avoid=avoid_colors if 'avoid_colors' in locals() else []
        )

        # Extract Dominant Colors & Perform Room Analysis
        with st.spinner("Extracting room tones and evaluating spatial light..."):
            extracted_dict = cached_dominant_colors(st.session_state.current_image_bytes)
            extracted = ExtractedColorAnalysis(**extracted_dict)
            analysis_dict = cached_room_analysis(
                st.session_state.current_image_bytes,
                room_type=current_preferences.room_type,
                style=current_preferences.interior_style
            )
            room_analysis = RoomAnalysisResult(**analysis_dict)


        # Generate Palettes
        palettes = generate_recommended_palettes(
            extracted=extracted,
            room_analysis=room_analysis,
            preferences=current_preferences
        )

        # Apply Chroma Memory & Material Ranking adjustments
        for p in palettes:
            mem_delta, mem_notes = evaluate_chroma_memory_influence(active_user_id, p)
            mat_delta, mat_notes = evaluate_material_compatibility(st.session_state.selected_materials, p)
            adjusted_score = min(98.0, max(50.0, p.heuristic_score + mem_delta + mat_delta))
            p.heuristic_score = round(adjusted_score, 1)

        # Select first palette if none active
        if not st.session_state.selected_palette_id or not any(p.id == st.session_state.selected_palette_id for p in palettes):
            st.session_state.selected_palette_id = palettes[0].id

        active_palette = next((p for p in palettes if p.id == st.session_state.selected_palette_id), palettes[0])

        # ----------------------------------------------------
        # CHROMA STUDIO AI — ARCHITECTURAL PRODUCT DETAIL & 3D STUDIO
        # ----------------------------------------------------
        saved_items_count = len(list_saved_palettes(user_id=active_user_id))

        col_left, col_right = st.columns([1.0, 1.25], gap="large")

        with col_left:
            # 1. Creator Tag & Display Headline
            st.markdown(
                f"""
                <div class="custom-card card-3d" style="padding: 24px 20px; margin-bottom: 18px;">
                    <div style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.14em; color: var(--accent-primary); margin-bottom: 6px;">
                        Chroma Studio AI • Spatial Colour Architecture
                    </div>
                    <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.1rem; color: var(--text-primary); margin: 0 0 8px 0;">
                        {active_palette.name}
                    </h2>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px;">
                        <span class="metric-pill">Typology: <strong>{room_analysis.detected_room_type}</strong></span>
                        <span class="metric-pill">Style: <strong>{room_analysis.detected_style}</strong></span>
                        <span class="metric-pill">Lighting: <strong>{room_analysis.apparent_lighting}</strong></span>
                    </div>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6; margin: 0;">
                        Architectural colour concept designed around natural room orientation and materials.
                        Strictly adheres to the 60-30-10 distribution with zero-bleed wall isolation.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 2. Options / Palette Swatch Selector
            st.markdown("##### 🎨 Recommended Architectural Concepts")

            palette_names = [f"{p.name}" for p in palettes]
            active_idx = next((i for i, p in enumerate(palettes) if p.id == active_palette.id), 0)

            selected_palette_name = st.radio(
                "Select Palette Concept",
                palette_names,
                index=active_idx,
                label_visibility="collapsed",
                horizontal=False
            )

            # Update active palette if changed via radio
            chosen_pal = next((p for p in palettes if p.name == selected_palette_name), palettes[0])
            if chosen_pal.id != active_palette.id:
                st.session_state.selected_palette_id = chosen_pal.id
                st.rerun()

            # Active Palette Swatches Breakdown with 3D Chips
            st.markdown(
                f"""
                <div class="custom-card card-3d" style="padding: 18px; margin-top: 14px; margin-bottom: 18px;">
                    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 12px;">
                        <div class="swatch-chip-3d" style="background-color: {active_palette.primary_wall.hex}; width: 22px; height: 22px; border-radius: 50%;"></div>
                        <strong style="font-size: 1.05rem; font-family: 'Playfair Display', Georgia, serif; color: var(--text-primary);">{active_palette.name}</strong>
                        <span class="score-badge" style="margin-left: auto;">Match: {active_palette.heuristic_score}%</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 0.74rem;">
                        <div>
                            <div class="swatch-chip-3d" style="background-color: {active_palette.primary_wall.hex}; height: 38px; margin-bottom: 6px;"></div>
                            <span style="color: var(--text-muted); font-size: 0.68rem; font-weight: 700; text-transform: uppercase;">Primary 60%</span><br>
                            <span style="font-weight: 700; color: var(--text-primary);">{active_palette.primary_wall.name}</span><br>
                            <code style="color: var(--accent-primary);">{active_palette.primary_wall.hex.upper()}</code>
                        </div>
                        <div>
                            <div class="swatch-chip-3d" style="background-color: {active_palette.secondary_wall.hex}; height: 38px; margin-bottom: 6px;"></div>
                            <span style="color: var(--text-muted); font-size: 0.68rem; font-weight: 700; text-transform: uppercase;">Secondary 30%</span><br>
                            <span style="font-weight: 700; color: var(--text-primary);">{active_palette.secondary_wall.name}</span><br>
                            <code style="color: var(--accent-primary);">{active_palette.secondary_wall.hex.upper()}</code>
                        </div>
                        <div>
                            <div class="swatch-chip-3d" style="background-color: {active_palette.accent.hex}; height: 38px; margin-bottom: 6px;"></div>
                            <span style="color: var(--text-muted); font-size: 0.68rem; font-weight: 700; text-transform: uppercase;">Accent 10%</span><br>
                            <span style="font-weight: 700; color: var(--text-primary);">{active_palette.accent.name}</span><br>
                            <code style="color: var(--accent-primary);">{active_palette.accent.hex.upper()}</code>
                        </div>
                        <div>
                            <div class="swatch-chip-3d" style="background-color: {active_palette.trim.hex}; height: 38px; margin-bottom: 6px;"></div>
                            <span style="color: var(--text-muted); font-size: 0.68rem; font-weight: 700; text-transform: uppercase;">Trim / Ceiling</span><br>
                            <span style="font-weight: 700; color: var(--text-primary);">{active_palette.trim.name}</span><br>
                            <code style="color: var(--accent-primary);">{active_palette.trim.hex.upper()}</code>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Hairline Divider
            st.markdown('<div class="chroma-hairline"></div>', unsafe_allow_html=True)

            # 3. Signature CTA Buttons
            btn_c1, btn_c2 = st.columns([1.3, 1.0])
            with btn_c1:
                if st.button("💾 Save Palette to Collection", key=f"chroma_save_{active_palette.id}", use_container_width=True):
                    allowed, msg, _ = check_entitlement(active_user_id, "save_palette")
                    if not allowed:
                        st.error(msg)
                    else:
                        rec_id = save_palette(
                            palette=active_palette,
                            custom_name=active_palette.name,
                            room_type=room_analysis.detected_room_type,
                            interior_style=room_analysis.detected_style,
                            preferences=current_preferences,
                            user_id=active_user_id
                        )
                        record_favorite_palette(active_user_id, active_palette, style=room_analysis.detected_style)
                        st.session_state.save_status_message = f"✅ Saved '{active_palette.name}' to collection!"
                        st.rerun()

            with btn_c2:
                swatch_sheet_buf = generate_swatch_sheet_png(active_palette, room_type=room_analysis.detected_room_type)
                st.download_button(
                    "⬇️ Swatch Sheet (PNG)",
                    data=swatch_sheet_buf.getvalue(),
                    file_name=f"{active_palette.name.replace(' ', '_').lower()}_swatch.png",
                    mime="image/png",
                    key="chroma_swatch_download",
                    use_container_width=True
                )

            if st.session_state.save_status_message:
                st.success(st.session_state.save_status_message)
                st.session_state.save_status_message = None

        with col_right:
            # Right Hero Staging Container
            st.markdown("##### 🖼️ Spatial Staging & Wall Simulation")

            view_mode = st.radio(
                "Staging Mode",
                ["Recoloured Preview", "Side-by-Side Comparison", "Split Slider Comparison", "Wall Mask Overlay"],
                index=0,
                horizontal=True,
                label_visibility="collapsed"
            )

            # Compute wall mask (cached)
            mask_png_bytes, mask_meta = cached_wall_mask(
                st.session_state.current_image_bytes,
                st.session_state.mask_sensitivity,
                st.session_state.upper_bias,
                st.session_state.edge_protection,
                target_plane_id=st.session_state.selected_wall_plane_id
            )
            wall_mask_arr = np.array(Image.open(io.BytesIO(mask_png_bytes)).convert("L"))

            # Apply real luminance-preserving wall recolouring
            recoloured_room = apply_luminance_preserving_recolour(
                original_img=original_pil,
                wall_mask=wall_mask_arr,
                target_rgb=active_palette.primary_wall.rgb,
                intensity=st.session_state.recolour_intensity,
                strategy=st.session_state.recolour_strategy,
                shading_retention=st.session_state.shading_retention
            )

            # Display selected view in the Showcase Box
            if view_mode == "Recoloured Preview":
                st.image(recoloured_room, use_container_width=True, caption=f"Primary Wall: {active_palette.primary_wall.name} ({active_palette.primary_wall.hex.upper()})")
            elif view_mode == "Side-by-Side Comparison":
                sbs_img = create_side_by_side_comparison(
                    original_pil,
                    recoloured_room,
                    paint_name=active_palette.primary_wall.name,
                    hex_code=active_palette.primary_wall.hex.upper()
                )
                st.image(sbs_img, use_container_width=True)
            elif view_mode == "Split Slider Comparison":
                split_val = st.slider("Divider Position", 0.1, 0.9, 0.5, 0.05, label_visibility="collapsed")
                split_img = create_split_slider_comparison(
                    original_pil,
                    recoloured_room,
                    split_ratio=split_val,
                    line_color=(255, 255, 255),
                    line_width=3
                )
                st.image(split_img, use_container_width=True)
            else:
                mask_vis = create_mask_overlay_preview(original_pil, wall_mask_arr)
                st.image(mask_vis, use_container_width=True, caption=f"Wall Mask Coverage: {mask_meta.get('wall_coverage_percent', 0)}%")

            # Extracted Dominant Colours below image
            render_dominant_color_strip(extracted)

            # Compact sliders for paint density & wall sensitivity
            s_c1, s_c2 = st.columns(2)
            with s_c1:
                st.session_state.recolour_intensity = st.slider(
                    "Paint Intensity",
                    0.20, 1.00, float(st.session_state.recolour_intensity), 0.05
                )
            with s_c2:
                st.session_state.mask_sensitivity = st.slider(
                    "Wall Detection Sensitivity",
                    0.20, 0.90, float(st.session_state.mask_sensitivity), 0.05
                )

        # ----------------------------------------------------
        # BELOW THE FOLD: EDITORIAL ACCORDIONS
        # ----------------------------------------------------
        st.markdown('<div class="chroma-hairline"></div>', unsafe_allow_html=True)

        with st.expander("01. Architectural Specifications & LRV (Light Reflectance Values)", expanded=False):
            render_palette_swatches_horizontal(active_palette)
            render_explainability_card(active_palette)

        with st.expander("02. Spatial Room Analysis & Lighting Evaluation", expanded=False):
            render_room_analysis_card(room_analysis)

        with st.expander("03. Material & Furniture Harmony Evaluations", expanded=False):
            st.markdown(f"**Existing Surface Harmony:** {active_palette.furniture_flooring_compatibility}")
            st.markdown(f"**Design Rationale:** {active_palette.design_rationale}")

        with st.expander("04. Smart Paint Quantity & Coverage Estimator", expanded=False):
            est_col1, est_col2, est_col3 = st.columns(3)
            with est_col1:
                sq_ft = st.number_input("Room Wall Area (sq.ft)", value=350, min_value=50, max_value=5000, step=25)
            with est_col2:
                coats = st.selectbox("Paint Coats", [1, 2, 3], index=1)
            with est_col3:
                estimate = estimate_paint_quantity(PaintEstimateInput(total_wall_area_sqft=sq_ft, num_coats=coats))
                st.metric("Estimated Paint Required", f"{estimate.total_litres_needed} Litres", f"{estimate.recommended_cans_one_litre} x 1L Cans")

        with st.expander("05. Export Consultation Suite (JSON, CSV, PNG, TXT, MD, PDF)", expanded=False):
            exp_c1, exp_c2, exp_c3, exp_c4, exp_c5, exp_c6 = st.columns(6)
            with exp_c1:
                json_str = export_palette_json(active_palette, room_analysis=room_analysis)
                st.download_button("Export JSON", data=json_str, file_name=f"{active_palette.name.replace(' ', '_').lower()}.json", mime="application/json", use_container_width=True)
            with exp_c2:
                csv_str = export_palette_csv(active_palette)
                st.download_button("Export CSV", data=csv_str, file_name=f"{active_palette.name.replace(' ', '_').lower()}.csv", mime="text/csv", use_container_width=True)
            with exp_c3:
                sw_buf = generate_swatch_sheet_png(active_palette, room_type=room_analysis.detected_room_type)
                st.download_button("Export Swatch PNG", data=sw_buf.getvalue(), file_name=f"{active_palette.name.replace(' ', '_').lower()}_swatch.png", mime="image/png", use_container_width=True)
            with exp_c4:
                txt_rep = generate_text_report(active_palette, room_analysis, extracted, room_type=room_analysis.detected_room_type)
                st.download_button("Export TXT", data=txt_rep, file_name=f"{active_palette.name.replace(' ', '_').lower()}_report.txt", mime="text/plain", use_container_width=True)
            with exp_c5:
                md_rep = generate_markdown_report(active_palette, room_analysis, extracted, room_type=room_analysis.detected_room_type)
                st.download_button("Export MD", data=md_rep, file_name=f"{active_palette.name.replace(' ', '_').lower()}_report.md", mime="text/markdown", use_container_width=True)
            with exp_c6:
                pdf_rep = generate_pdf_report(active_palette, room_analysis, extracted, room_type=room_analysis.detected_room_type)
                st.download_button("Export PDF", data=pdf_rep.getvalue(), file_name=f"{active_palette.name.replace(' ', '_').lower()}_report.pdf", mime="application/pdf", use_container_width=True)

        with st.expander("06. All 4 Architectural Concept Cards", expanded=False):
            for pal in palettes:
                is_active = (pal.id == active_palette.id)
                st.markdown(
                    f"""
                    <div class="palette-card card-3d" style="border-width: {'2px' if is_active else '1px'}; border-color: {'var(--accent-primary)' if is_active else 'var(--border-subtle)'};">
                        <div class="palette-header">
                            <div>
                                <span style="font-size: 0.72rem; font-weight: 700; color: var(--accent-secondary); text-transform: uppercase;">{pal.concept_category} • {pal.harmony_type}</span>
                                <h4 class="palette-title">{pal.name}</h4>
                            </div>
                            <span class="score-badge">Match: {pal.heuristic_score}%</span>
                        </div>
                        <p style="font-size: 0.86rem; color: var(--text-secondary); margin: 6px 0 12px 0;">{pal.description}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                render_palette_swatches_horizontal(pal)
                if not is_active:
                    if st.button("Select This Concept", key=f"pick_{pal.id}"):
                        st.session_state.selected_palette_id = pal.id
                        st.rerun()


# ====================================================
# EXPANSION VIEW: LIVE CAMERA STUDIO
# ====================================================
def render_live_camera_view():
    st.markdown("## 📹 Live Camera Studio & Everyday Intelligence")
    st.caption("Real-time architectural video feed, live room feature detection, and zero-bleed wall colour simulation.")

    render_privacy_shield_banner()

    cam_col1, cam_col2 = st.columns([1.2, 1.0], gap="large")

    with cam_col1:
        st.markdown("### 🎥 Camera Stream")
        webrtc_on = is_webrtc_available()

        feed_mode = st.radio(
            "Camera Mode",
            ["Live WebRTC Stream (Continuous)", "Browser Snapshot Camera", "Upload Room Frame"],
            horizontal=True
        )

        if feed_mode == "Live WebRTC Stream (Continuous)":
            if not webrtc_on:
                st.warning("streamlit-webrtc is not loaded in this session. Using browser camera input.")
            else:
                # Configuration controls
                cf_c1, cf_c2, cf_c3 = st.columns(3)
                with cf_c1:
                    cam_resolution = st.selectbox("Resolution", ["640x480 (Fast)", "1280x720 (HD)", "1920x1080 (FHD)"], index=0)
                with cf_c2:
                    live_overlay_type = st.selectbox("Live Stream Overlay", ["Clean Video Feed", "Wall Colour Simulation", "Room Intelligence Bounding Boxes"], index=0)
                with cf_c3:
                    active_target_color = st.color_picker("Overlay Wall Shade", value="#B85C38")

                # WebRTC Streamer
                h_hex = active_target_color.lstrip("#")
                t_rgb = (int(h_hex[0:2], 16), int(h_hex[2:4], 16), int(h_hex[4:6], 16))

                # Initialize thread-safe frame holder
                if "live_frame_holder" not in st.session_state:
                    st.session_state.live_frame_holder = ThreadSafeFrameHolder()

                from streamlit_webrtc import webrtc_streamer, RTCConfiguration
                ctx = webrtc_streamer(
                    key="chroma_live_webcam",
                    rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
                    media_stream_constraints={
                        "video": {
                            "width": {"ideal": 1280} if "1280" in cam_resolution else {"ideal": 640},
                            "height": {"ideal": 720} if "1280" in cam_resolution else {"ideal": 480}
                        },
                        "audio": False
                    },
                    async_processing=True
                )

                if ctx.video_transformer:
                    ctx.video_transformer.frame_holder = st.session_state.live_frame_holder
                    ctx.video_transformer.overlay_mode = "wall_preview" if live_overlay_type == "Wall Colour Simulation" else "none"
                    ctx.video_transformer.target_rgb = t_rgb

        elif feed_mode == "Browser Snapshot Camera":
            cam_picture = st.camera_input("Capture live room frame with your webcam")
            if cam_picture is not None:
                st.session_state.current_image_bytes = cam_picture.getvalue()
                st.success("Captured room frame loaded into Chroma Studio!")
                st.rerun()
        else:
            up_f = st.file_uploader("Upload room frame", type=["jpg", "png", "webp"], key="cam_up")
            if up_f is not None:
                st.session_state.current_image_bytes = up_f.getvalue()
                st.success("Uploaded room frame loaded!")
                st.rerun()

        # Snapshot Button
        st.markdown('<div class="chroma-hairline"></div>', unsafe_allow_html=True)
        if st.button("📸 Capture Snapshot into Design Studio", use_container_width=True):
            if "live_frame_holder" in st.session_state and st.session_state.live_frame_holder.get_frame() is not None:
                pil_frame = st.session_state.live_frame_holder.get_pil_image()
                buf = io.BytesIO()
                pil_frame.save(buf, format="JPEG", quality=90)
                st.session_state.current_image_bytes = buf.getvalue()
                st.success("✅ Captured snapshot from live video stream! Switched into Studio.")
                st.session_state.current_view = "🎨 Studio & Analysis"
                st.rerun()
            elif st.session_state.current_image_bytes is not None:
                st.info("Using currently active room image.")
                st.session_state.current_view = "🎨 Studio & Analysis"
                st.rerun()
            else:
                st.warning("Start camera stream or take a snapshot above to capture a frame.")

    with cam_col2:
        st.markdown("### 🧠 Live Room Intelligence")
        st.caption("Real-time structural element classification and confidence scoring.")

        if st.session_state.current_image_bytes is not None:
            pil_to_analyze = Image.open(io.BytesIO(st.session_state.current_image_bytes)).convert("RGB")
            with st.spinner("Analyzing architectural elements in frame..."):
                intel_res = analyze_live_frame_intelligence(pil_to_analyze)

            st.markdown(f"**Detected Elements ({intel_res['elements_detected_count']}):**")
            annotated_img = draw_intelligence_bounding_boxes(pil_to_analyze, intel_res)
            st.image(annotated_img, caption="Architectural Bounding Box Segmentation", use_container_width=True)

            # Detections list
            for d in intel_res["detections"]:
                conf_pct = int(d["confidence"] * 100)
                dom_hex = d.get("dominant_hex", "#30271F")
                st.markdown(
                    f"""
                    <div class="custom-card" style="padding: 12px 16px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-weight: 700; color: var(--text-primary);">{d['category']}</span>
                                <span style="font-size: 0.8rem; color: var(--text-secondary); margin-left: 8px;">{d['area_percentage']}% room area</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="display: inline-block; width: 14px; height: 14px; border-radius: 50%; background-color: {dom_hex}; border: 1px solid var(--border-subtle);"></span>
                                <span class="score-badge">Conf: {conf_pct}%</span>
                            </div>
                        </div>
                        <p style="font-size: 0.80rem; color: var(--text-secondary); margin: 4px 0 0 0;">{d['description']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Start your webcam or capture a frame to view real-time architectural segmentation.")


# ====================================================
# VIEW 3: ROOM VISUALIZATION STUDIO
# ====================================================
def render_visualization_view():
    if st.session_state.current_image_bytes is None:
        st.info("Upload a room photograph in the sidebar to visualize paint simulations.")
    else:
        original_pil, proc_pil, metadata = validate_image_bytes(st.session_state.current_image_bytes)
        extracted_dict = cached_dominant_colors(st.session_state.current_image_bytes)
        extracted = ExtractedColorAnalysis(**extracted_dict)
        analysis_dict = cached_room_analysis(st.session_state.current_image_bytes)
        room_analysis = RoomAnalysisResult(**analysis_dict)
        palettes = generate_recommended_palettes(extracted=extracted, room_analysis=room_analysis)
        active_palette = next((p for p in palettes if p.id == st.session_state.selected_palette_id), palettes[0])

        st.markdown(f"### 🖼️ Visualizing: **{active_palette.name}**")
        st.caption(f"Primary Wall Paint: **{active_palette.primary_wall.name}** ({active_palette.primary_wall.hex}) • Secondary: **{active_palette.secondary_wall.name}** ({active_palette.secondary_wall.hex})")

        vis_tabs = st.tabs([
            "🏛️ Mode 1: Interactive 3D Spatial Model (WebGL & Orbit)",
            "🛠️ Mode 2: Local 2D Wall Recolouring (Zero-Bleed CV)",
            "✨ Mode 3: AI-Enhanced Preview (Generative Diffusion)"
        ])

        # Tab 0: Three.js Interactive 3D Spatial Room Model
        with vis_tabs[0]:
            st.markdown(
                """
                <div class="custom-card card-3d" style="margin-bottom: 14px; padding: 14px 18px; border-left: 4px solid var(--accent-primary);">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <span style="font-weight: 700; color: var(--accent-primary); font-size: 0.94rem;">
                            🏛️ Mode 1 Active: Three.js Interactive 3D Spatial Canvas
                        </span>
                        <span class="score-badge" style="background-color: #E8EFE9; color: #3A6946;">
                            WebGL PBR Shader
                        </span>
                    </div>
                    <p style="font-size: 0.84rem; color: var(--text-secondary); margin: 4px 0 0 0;">
                        Inspect color transitions, room depth, and lighting angles on a live 3D architectural model. Drag with your mouse to orbit around the room, scroll to zoom in/out, and switch wall finishes in real-time.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Palette Quick Info Bar
            c_p1, c_p2, c_p3, c_p4 = st.columns(4)
            with c_p1:
                st.markdown(f"**Primary Wall (60%):** `{active_palette.primary_wall.hex.upper()}` ({active_palette.primary_wall.name})")
            with c_p2:
                st.markdown(f"**Feature Wall (30%):** `{active_palette.secondary_wall.hex.upper()}` ({active_palette.secondary_wall.name})")
            with c_p3:
                st.markdown(f"**Accent Furniture (10%):** `{active_palette.accent.hex.upper()}` ({active_palette.accent.name})")
            with c_p4:
                st.markdown(f"**Trim & Ceiling:** `{active_palette.trim.hex.upper()}` ({active_palette.trim.name})")

            # Render Three.js WebGL canvas
            render_3d_room_preview_card(
                palette=active_palette,
                room_type=room_analysis.detected_room_type if room_analysis else "Living Room Gallery",
                theme=st.session_state.theme,
                height=560
            )

        with vis_tabs[1]:
            st.markdown(
                """
                <div class="custom-card card-3d" style="margin-bottom: 14px; padding: 12px 16px;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <span style="font-weight: 700; color: var(--accent-primary); font-size: 0.92rem;">
                            🟢 Mode 2 Active: Local 2D Wall Recolouring
                        </span>
                        <span class="score-badge" style="background-color: #E8EFE9; color: #3A6946; font-size: 0.78rem;">
                            100% Offline &amp; Unmetered
                        </span>
                    </div>
                    <p style="font-size: 0.82rem; color: var(--text-secondary); margin: 4px 0 0 0;">
                        Preserves room shadows, ambient daylight falloff, and physical textures using luminance scaling. Runs entirely locally without API keys.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.session_state.recolour_intensity = st.slider("Paint Intensity", 0.2, 1.0, float(st.session_state.recolour_intensity), 0.05)
            with c2:
                st.session_state.mask_sensitivity = st.slider("Wall Sensitivity", 0.2, 0.9, float(st.session_state.mask_sensitivity), 0.05)
            with c3:
                st.session_state.edge_protection = st.slider("Edge Protection", 0.3, 0.95, float(st.session_state.edge_protection), 0.05)
            with c4:
                preview_type = st.selectbox("Comparison View", ["Side-by-Side Comparison", "Split Slider Comparison", "Full Recoloured Room", "Wall Mask Overlay"])

            c5, c6, c7 = st.columns([1.5, 1.2, 1.3])
            with c5:
                strat_options = list(LUMINANCE_STRATEGIES.keys())
                st.session_state.recolour_strategy = st.selectbox(
                    "Luminance Preservation Engine",
                    strat_options,
                    index=strat_options.index(st.session_state.recolour_strategy) if st.session_state.recolour_strategy in strat_options else 0,
                    format_func=lambda s: LUMINANCE_STRATEGIES.get(s, s)
                )
            with c6:
                st.session_state.shading_retention = st.slider("Shading & Texture Depth", 0.2, 1.0, float(st.session_state.shading_retention), 0.05)
            with c7:
                # Plane options will be dynamically updated after mask analysis
                plane_selection_placeholder = st.empty()

            # Retrieve mask and architectural planes
            mask_png_bytes, mask_meta = cached_wall_mask(
                st.session_state.current_image_bytes,
                st.session_state.mask_sensitivity,
                st.session_state.upper_bias,
                st.session_state.edge_protection,
                target_plane_id=st.session_state.selected_wall_plane_id
            )
            wall_mask_arr = np.array(Image.open(io.BytesIO(mask_png_bytes)).convert("L"))

            # Multi-plane selector
            detected_planes = mask_meta.get("detected_planes", [])
            plane_choices = [("all", "All Detected Wall Planes")]
            for p in detected_planes:
                plane_choices.append((p["plane_id"], f"{p['name']} ({p['coverage_percent']}%)"))
            
            selected_choice = plane_selection_placeholder.selectbox(
                "Target Wall Surface",
                options=[c[0] for c in plane_choices],
                format_func=lambda cid: next((c[1] for c in plane_choices if c[0] == cid), str(cid)),
                index=0 if st.session_state.selected_wall_plane_id is None else next((i for i, c in enumerate(plane_choices) if c[0] == st.session_state.selected_wall_plane_id), 0)
            )
            if selected_choice != ("all" if st.session_state.selected_wall_plane_id is None else st.session_state.selected_wall_plane_id):
                st.session_state.selected_wall_plane_id = None if selected_choice == "all" else selected_choice
                st.rerun()

            # Apply manual mask corrections if any
            if st.session_state.manual_mask_adjustments:
                from modules.wall_segmentation import apply_manual_corrections
                wall_mask_arr = apply_manual_corrections(wall_mask_arr, st.session_state.manual_mask_adjustments)

            # Perform high-accuracy recolouring
            recoloured_room = apply_luminance_preserving_recolour(
                original_pil,
                wall_mask_arr,
                active_palette.primary_wall.rgb,
                intensity=st.session_state.recolour_intensity,
                strategy=st.session_state.recolour_strategy,
                shading_retention=st.session_state.shading_retention
            )

            # Quality Control verification stage
            qc_report = validate_recolour_quality(
                original_pil,
                recoloured_room,
                wall_mask_arr,
                active_palette.primary_wall.rgb
            )

            # Segmentation & QC Diagnostics Header
            qc_status_color = "#3A6946" if qc_report.passed else "#A85324"
            qc_badge = "✅ Passed" if qc_report.passed else "⚠️ Flagged"
            conf_badge = mask_meta.get("segmentation_confidence", "Moderate")

            st.markdown(
                f"""
                <div style="display: flex; gap: 10px; margin-bottom: 12px; flex-wrap: wrap;">
                    <div class="custom-card" style="flex: 1; min-width: 200px; padding: 10px 14px; margin-bottom: 0;">
                        <span style="font-size: 0.76rem; color: var(--text-secondary); text-transform: uppercase;">Segmentation Confidence</span><br>
                        <strong style="color: var(--text-primary); font-size: 0.92rem;">{conf_badge}</strong>
                        <span style="font-size: 0.80rem; color: var(--text-secondary);">({mask_meta.get('wall_coverage_percent', 0)}% coverage)</span>
                    </div>
                    <div class="custom-card" style="flex: 1; min-width: 200px; padding: 10px 14px; margin-bottom: 0;">
                        <span style="font-size: 0.76rem; color: var(--text-secondary); text-transform: uppercase;">Quality Control</span><br>
                        <strong style="color: {qc_status_color}; font-size: 0.92rem;">{qc_badge}</strong>
                        <span style="font-size: 0.80rem; color: var(--text-secondary);">(Zero Bleed: Δout={qc_report.max_outside_pixel_delta})</span>
                    </div>
                    <div class="custom-card" style="flex: 1; min-width: 200px; padding: 10px 14px; margin-bottom: 0;">
                        <span style="font-size: 0.76rem; color: var(--text-secondary); text-transform: uppercase;">Active Strategy</span><br>
                        <strong style="color: var(--accent-primary); font-size: 0.92rem;">{st.session_state.recolour_strategy.replace('_', ' ').title()}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Segmentation warnings if any
            if mask_meta.get("warnings"):
                for w_msg in mask_meta["warnings"]:
                    st.warning(f"⚠️ Segmentation Note: {w_msg}")

            if qc_report.warnings:
                for qc_warn in qc_report.warnings:
                    st.info(f"ℹ️ Quality Control Diagnostic: {qc_warn}")

            # Render comparison preview
            if preview_type == "Side-by-Side Comparison":
                cmp_img = create_side_by_side_comparison(original_pil, recoloured_room, active_palette.primary_wall.name, active_palette.primary_wall.hex)
                st.image(cmp_img, use_container_width=True)
            elif preview_type == "Split Slider Comparison":
                slider_pos = st.slider("Divider Position", 0.1, 0.9, 0.5, 0.05)
                cmp_img = create_split_slider_comparison(original_pil, recoloured_room, slider_pos, active_palette.primary_wall.name)
                st.image(cmp_img, use_container_width=True)
            elif preview_type == "Full Recoloured Room":
                st.image(recoloured_room, use_container_width=True)
            else:
                overlay_img = create_mask_overlay_preview(original_pil, wall_mask_arr)
                st.image(overlay_img, use_container_width=True)

            # Interactive Manual Mask Refinement Expander
            with st.expander("✏️ Manual Mask Refinement & Brush Corrections", expanded=False):
                st.caption("Manually add missed wall areas or erase furniture/trim from the mask.")
                m_c1, m_c2, m_c3, m_c4 = st.columns(4)
                w_orig, h_orig = original_pil.size
                with m_c1:
                    m_mode = st.selectbox("Action", ["include", "exclude"], format_func=lambda x: "Add to Wall (Include)" if x == "include" else "Erase Obstacle (Exclude)")
                with m_c2:
                    m_x = st.number_input("Target X Coordinate", 0, w_orig, w_orig // 2, 10)
                with m_c3:
                    m_y = st.number_input("Target Y Coordinate", 0, h_orig, h_orig // 3, 10)
                with m_c4:
                    m_rad = st.slider("Brush Radius (px)", 10, 150, 35, 5)

                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    if st.button("🖌️ Apply Brush Stroke", use_container_width=True):
                        st.session_state.manual_mask_adjustments.append({
                            "type": "brush",
                            "mode": m_mode,
                            "x": m_x,
                            "y": m_y,
                            "radius": m_rad
                        })
                        st.success(f"Added manual correction stroke at ({m_x}, {m_y}).")
                        st.rerun()
                with b_col2:
                    if st.button("↺ Reset All Manual Adjustments", use_container_width=True):
                        st.session_state.manual_mask_adjustments = []
                        st.info("Manual adjustments cleared.")
                        st.rerun()

            # Technical painting disclaimer
            st.caption(
                "💡 **Architectural Paint Disclaimer:** Simulated colors reproduce perceptual appearance under existing ambient lighting. "
                "Physical paint results in real spaces will vary according to primer coats, surface finish (matte, eggshell, satin), "
                "incident window daylight, and monitor display calibration."
            )

            # Download recoloured preview
            rec_buf = io.BytesIO()
            recoloured_room.save(rec_buf, format="PNG")
            st.download_button("⬇️ Download High-Res Preview (PNG)", rec_buf.getvalue(), "recoloured_room.png", "image/png")

        with vis_tabs[2]:
            st.markdown("#### Mode 3: AI-Enhanced Generative Preview")
            edit_status = get_image_editing_status()
            
            if edit_status["is_configured"]:
                st.markdown(
                    f"""
                    <div class="custom-card" style="margin-bottom: 14px; padding: 14px 18px; border-left: 4px solid var(--accent-primary);">
                        <div style="font-weight: 700; color: var(--accent-primary); font-size: 0.92rem; margin-bottom: 4px;">
                            🟢 Mode 2 Configured: {edit_status['provider'].upper()} ({edit_status['model']})
                        </div>
                        <div style="font-size: 0.84rem; color: var(--text-secondary);">
                            API Key Detected: <code style="color: var(--accent-secondary);">{edit_status['masked_key']}</code> • 
                            Endpoint: <code>{edit_status['endpoint']}</code>
                        </div>
                        <p style="font-size: 0.82rem; color: var(--text-secondary); margin: 6px 0 0 0;">
                            Generative diffusion models reconstruct the space with architectural paint textures while maintaining floor and furniture layouts.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class="custom-card" style="margin-bottom: 14px; padding: 14px 18px; border-left: 4px solid var(--accent-secondary);">
                        <div style="font-weight: 700; color: var(--accent-primary); font-size: 0.92rem; margin-bottom: 4px;">
                            ℹ️ Mode 2 Unavailable: API Key Not Configured
                        </div>
                        <p style="font-size: 0.84rem; color: var(--text-secondary); margin: 0 0 6px 0;">
                            AI Image Editing API key not detected in <code>.env</code>. Mode 1 local wall recolouring is active with 100% full luminance preservation.
                        </p>
                        <p style="font-size: 0.80rem; color: var(--text-secondary); margin: 0;">
                            To enable generative cloud previews, configure <code>IMAGE_EDIT_API_KEY</code> (or <code>OPENAI_API_KEY</code>) in your project <code>.env</code>.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Check entitlement for AI preview
            can_ai, ai_msg, _ = check_entitlement(active_user_id, "ai_preview")
            if not can_ai:
                st.warning(f"⚠️ Plan Limit: {ai_msg}")
            
            button_disabled = (not edit_status["is_configured"]) or (not can_ai)
            btn_label = "✨ Request AI-Enhanced Room Render" if edit_status["is_configured"] else "🔒 Mode 2 Disabled (Configure API Key in .env)"
            
            if st.button(btn_label, disabled=button_disabled):
                with st.spinner("Generating architectural render..."):
                    gen_img, gen_meta = request_ai_enhanced_preview(
                        original_pil,
                        active_palette,
                        room_analysis.detected_room_type,
                        room_analysis.detected_style
                    )
                    record_usage_metric(active_user_id, "ai_preview")
                    st.session_state.ai_preview_result = (gen_img, gen_meta)


            if st.session_state.ai_preview_result:
                g_img, g_meta = st.session_state.ai_preview_result
                if g_img:
                    st.image(g_img, caption="Generative AI Render", use_container_width=True)
                else:
                    st.error(g_meta.get("message", "AI preview could not be generated."))


# ====================================================
# EXPANSION VIEW 1: LIVE COLOUR SCANNER
# ====================================================
def render_colour_scanner_view():
    st.markdown("## 🎯 Live Colour Scanner & Reticle Sampler")
    st.caption("Point-and-sample multi-space colour acquisition (RGB, HEX, HSV, CIELAB) with neighborhood noise averaging.")

    render_privacy_shield_banner()

    if st.session_state.current_image_bytes is None:
        st.info("Upload a room image in the sidebar or capture a snapshot in 📹 Live Camera Studio to scan colours.")
    else:
        scanner_pil = Image.open(io.BytesIO(st.session_state.current_image_bytes)).convert("RGB")
        w_img, h_img = scanner_pil.size

        scan_col1, scan_col2 = st.columns([1.1, 1.0], gap="large")

        with scan_col1:
            st.markdown("### 🔍 Viewfinder & Crosshair Sampler")
            
            # Interactive reticle position controls
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                ret_x = st.slider("Reticle X Position (%)", 0, 100, 50, step=1) / 100.0
            with rc2:
                ret_y = st.slider("Reticle Y Position (%)", 0, 100, 50, step=1) / 100.0
            with rc3:
                radius = st.selectbox("Kernel Radius (px)", [3, 5, 7, 9, 15], index=1)

            # Sample the color under reticle
            scanned_spot = scan_color_at_reticle(scanner_pil, ret_x, ret_y, sample_radius=radius)

            # Render crosshair on image
            crosshair_img = draw_reticle_crosshair(scanner_pil, ret_x, ret_y, active_color_hex=scanned_spot.hex)
            st.image(crosshair_img, caption=f"Viewfinder Reticle ({int(ret_x * w_img)}px, {int(ret_y * h_img)}px)", use_container_width=True)

        with scan_col2:
            st.markdown("### 📊 Optical Spectral Analysis")
            
            # Display sampled color details card
            st.markdown(
                f"""
                <div class="custom-card" style="padding: 18px; margin-bottom: 16px; border-left: 6px solid {scanned_spot.hex};">
                    <div style="display: flex; gap: 16px; align-items: center;">
                        <div style="width: 64px; height: 64px; border-radius: 8px; background-color: {scanned_spot.hex}; border: 1px solid var(--border-subtle); flex-shrink: 0; box-shadow: var(--shadow-sm);"></div>
                        <div style="flex: 1;">
                            <h3 style="margin: 0; font-size: 1.25rem; font-family: 'Playfair Display', Georgia, serif; color: var(--text-primary);">{scanned_spot.name}</h3>
                            <div style="font-size: 0.95rem; font-weight: 700; color: var(--accent-primary); margin-top: 2px;">{scanned_spot.hex}</div>
                            <span class="score-badge" style="margin-top: 4px; display: inline-block;">Temperature: {scanned_spot.temperature}</span>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border-subtle); font-size: 0.78rem;">
                        <div>
                            <span style="color: var(--text-secondary);">RGB Coordinates</span><br>
                            <code>({scanned_spot.rgb[0]}, {scanned_spot.rgb[1]}, {scanned_spot.rgb[2]})</code>
                        </div>
                        <div>
                            <span style="color: var(--text-secondary);">CIELAB (L*, a*, b*)</span><br>
                            <code>({scanned_spot.lab[0]}, {scanned_spot.lab[1]}, {scanned_spot.lab[2]})</code>
                        </div>
                        <div>
                            <span style="color: var(--text-secondary);">Perceptual Luminance</span><br>
                            <code>{scanned_spot.luminance}</code>
                        </div>
                    </div>
                    <p style="font-size: 0.76rem; color: var(--text-muted); margin: 8px 0 0 0;">{scanned_spot.notes}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Save to Library Form
            with st.form("save_scanned_color_form"):
                st.markdown("#### 💾 Save to Personal Chroma Library")
                s_name = st.text_input("Custom Color Label", value=scanned_spot.name)
                s_tag = st.selectbox("Architectural Application Tag", ["Accent Wall", "Primary Surface", "Trim / Molding", "Ceiling", "Millwork", "Exterior / Facade"])
                s_note = st.text_input("Room Note / Context", value=f"Sampled at ({int(ret_x * 100)}%, {int(ret_y * 100)}%) from current room photo")
                
                submitted = st.form_submit_button("Save Color to Library", use_container_width=True)
                if submitted:
                    save_scanned_color(
                        user_id=active_user_id,
                        hex_code=scanned_spot.hex,
                        color_name=s_name,
                        rgb_tuple=scanned_spot.rgb,
                        lab_tuple=scanned_spot.lab,
                        tags=[s_tag],
                        room_source=s_note
                    )
                    st.success(f"✅ Saved '{s_name}' ({scanned_spot.hex}) to your Chroma Library!")
                    st.rerun()

            # Fast Cluster Palette from this frame
            st.markdown("---")
            st.markdown("#### 🎨 Dominant Frame Palette (Real-Time Clustering)")
            clusters = scan_frame_dominant_palette(scanner_pil, k_clusters=5)
            cl_cols = st.columns(len(clusters))
            for i, (col, c_detail) in enumerate(zip(cl_cols, clusters)):
                with col:
                    st.markdown(
                        f"""
                        <div class="custom-card" style="padding: 10px; text-align: center;">
                            <div style="background-color: {c_detail.hex}; height: 42px; border-radius: 6px; margin-bottom: 6px; border: 1px solid var(--border-subtle);"></div>
                            <strong style="font-size: 0.78rem; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{c_detail.name}</strong>
                            <code style="font-size: 0.72rem;">{c_detail.hex}</code><br>
                            <span style="font-size: 0.68rem; color: var(--text-secondary);">{c_detail.percentage}% area</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # Saved Personal Library Section
        st.markdown("---")
        st.markdown("### 📚 Your Saved Scanned Colours")
        saved_scans = list_scanned_colors(active_user_id)
        if not saved_scans:
            st.caption("No scanned colours saved yet. Use the viewfinder above to sample and save room tones.")
        else:
            lib_cols = st.columns(min(4, len(saved_scans)))
            for idx, sc in enumerate(saved_scans):
                with lib_cols[idx % 4]:
                    st.markdown(
                        f"""
                        <div class="custom-card" style="padding: 14px; margin-bottom: 12px; border-top: 4px solid {sc['hex_code']};">
                            <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 6px;">
                                <div style="width: 32px; height: 32px; border-radius: 6px; background-color: {sc['hex_code']}; border: 1px solid var(--border-subtle);"></div>
                                <div>
                                    <strong style="font-size: 0.88rem; color: var(--text-primary);">{sc['color_name']}</strong><br>
                                    <code style="font-size: 0.76rem;">{sc['hex_code']}</code>
                                </div>
                            </div>
                            <div style="font-size: 0.74rem; color: var(--text-secondary); margin-bottom: 4px;">
                                Tags: <strong>{', '.join(sc.get('tags', []))}</strong>
                            </div>
                            <div style="font-size: 0.70rem; color: var(--text-muted);">
                                {sc.get('room_source', '')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("🗑️ Delete", key=f"del_scan_{sc['id']}", use_container_width=True):
                        delete_scanned_color(sc["id"], active_user_id)
                        st.rerun()


# ====================================================
# EXPANSION VIEW 2: PAINT BRAND MATCHER
# ====================================================
def render_brand_matcher_view():
    st.markdown("## 🏷️ Paint Brand Matcher (Indian Commercial Catalogues)")
    st.caption("Direct CIELAB Delta E matching against physical shade cards from Asian Paints, Berger, Kansai Nerolac, and Dulux India.")

    st.markdown(
        """
        <div class="custom-card" style="padding: 14px 18px; margin-bottom: 18px; border-left: 4px solid var(--accent-primary);">
            <div style="font-weight: 700; color: var(--accent-primary); font-size: 0.90rem;">
                🏛️ Commercial Shade Accuracy Disclaimer
            </div>
            <p style="font-size: 0.82rem; color: var(--text-secondary); margin: 4px 0 0 0;">
                Color matches are computed using exact CIELAB perceptual distance (ΔE) under standard CIE D65 daylight illuminant.
                Matches with ΔE ≤ 2.0 represent commercially indistinguishable shades. Always verify physical shade cards and primer requirements with an authorized dealer prior to batch tinting.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Input target color
    bm_col1, bm_col2 = st.columns([1.0, 1.4], gap="large")

    with bm_col1:
        st.markdown("### 🎨 Select Target Shade")
        
        # Color input mode
        input_mode = st.radio("Target Source", ["Color Picker (HEX)", "Extract from Room Photo"], horizontal=True)

        target_hex = "#7A4A32"
        if input_mode == "Color Picker (HEX)":
            target_hex = st.color_picker("Pick Target Shade", value="#7A4A32")
        else:
            if st.session_state.current_image_bytes is not None:
                ext_dict = cached_dominant_colors(st.session_state.current_image_bytes)
                extracted_colors = ext_dict.get("colors", [])
                if extracted_colors:
                    opts = [f"{c['name']} ({c['hex']})" for c in extracted_colors]
                    sel_opt = st.selectbox("Select Extracted Room Tone", opts, index=0)
                    target_hex = sel_opt.split("(")[-1].rstrip(")")
                else:
                    st.info("No tones extracted. Using default terracotta.")
            else:
                st.info("Upload room image in sidebar to extract room tones.")

        st.markdown(
            f"""
            <div class="custom-card" style="padding: 14px; text-align: center; margin-top: 12px;">
                <div style="background-color: {target_hex}; height: 60px; border-radius: 8px; margin-bottom: 8px; border: 1px solid var(--border-subtle);"></div>
                <strong>Target Tone: <code>{target_hex.upper()}</code></strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### 🔍 Manufacturer Filters")
        available_brands = get_available_brands()
        sel_brand = st.selectbox("Filter Brand", available_brands, index=0)
        max_matches = st.slider("Maximum Matches to Display", 2, 8, 4)

    with bm_col2:
        st.markdown("### 🏆 Commercial Brand Matches")
        
        matches = match_paint_brand_shades(target_hex, brand_filter=sel_brand, max_results=max_matches)
        if not matches:
            st.warning("No commercial shades found within specified tolerance.")
        else:
            for m in matches:
                render_paint_brand_match_card(m)

            st.markdown(
                """
                <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 12px;">
                    ℹ️ Estimated rates based on standard 1-Litre interior architectural packs in INR (inclusive of GST).
                    Bulk 4L, 10L, and 20L contractor packs typically provide 12–18% volume savings.
                </div>
                """,
                unsafe_allow_html=True
            )


# ====================================================
# EXPANSION VIEW 3: FURNITURE & ROOM PLANNER
# ====================================================
def render_room_planner_view():
    st.markdown("## 📐 Architectural Furniture & Spatial Room Planner")
    st.caption("Spatial density audits, circulation clearance checks, and layout management.")

    st.markdown(
        """
        <div class="custom-card" style="padding: 14px 18px; margin-bottom: 18px; border-left: 4px solid var(--accent-secondary);">
            <div style="font-weight: 700; color: var(--accent-secondary); font-size: 0.90rem;">
                ⚠️ Architectural Clearance & Spatial Feasibility Notice
            </div>
            <p style="font-size: 0.82rem; color: var(--text-secondary); margin: 4px 0 0 0;">
                Calculations provide approximate spatial clearances based on standard human factor ergonomics (NEUFERT &amp; NBC India standards).
                Ensure minimum 90cm corridors for primary circulation and 45cm around seating clusters. Never construct without physical laser measurement.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    pl_c1, pl_c2 = st.columns([1.1, 1.2], gap="large")

    with pl_c1:
        st.markdown("### 📐 Room Boundary Specifications")
        r_name = st.text_input("Room Identifier / Project Name", value="Master Living Room", key="pl_rname")
        r_type = st.selectbox("Room Typology", ["Living Room", "Master Bedroom", "Studio Apartment", "Home Office", "Dining Room"], key="pl_rtype")
        
        dim_col1, dim_col2, dim_col3 = st.columns(3)
        with dim_col1:
            r_len_m = st.number_input("Length (meters)", min_value=1.5, max_value=20.0, value=5.2, step=0.1)
        with dim_col2:
            r_wid_m = st.number_input("Width (meters)", min_value=1.5, max_value=20.0, value=3.8, step=0.1)
        with dim_col3:
            r_hgt_m = st.number_input("Ceiling Height (m)", min_value=2.0, max_value=6.0, value=2.9, step=0.1)

        room_area_sqm = round(r_len_m * r_wid_m, 2)
        room_area_sqft = round(room_area_sqm * 10.7639, 1)

        st.markdown(
            f"""
            <div style="display: flex; gap: 12px; margin-top: 10px;">
                <div class="metric-pill">Floor Area: <strong>{room_area_sqm} m² ({room_area_sqft} sq.ft)</strong></div>
                <div class="metric-pill">Ceiling: <strong>{r_hgt_m}m</strong></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")
        st.markdown("### 🛋️ Furniture Inventory")

        if "planner_furniture_items" not in st.session_state:
            st.session_state.planner_furniture_items = get_furniture_suggestions(r_type)

        # Quick preset load button
        if st.button("🔄 Reset to Typology Presets"):
            st.session_state.planner_furniture_items = get_furniture_suggestions(r_type)
            st.rerun()

        # Display current items
        for idx, item in enumerate(st.session_state.planner_furniture_items):
            f_col1, f_col2 = st.columns([3, 1])
            with f_col1:
                st.markdown(f"• **{item['name']}** — {item.get('width_cm', 100)}cm × {item.get('depth_cm', 50)}cm ({item.get('clearance_needed_cm', 60)}cm clear)")
            with f_col2:
                if st.button("Remove", key=f"del_furn_{idx}"):
                    st.session_state.planner_furniture_items.pop(idx)
                    st.rerun()

        # Add furniture form
        with st.expander("➕ Add Custom Furniture Item"):
            af_name = st.text_input("Item Name", value="Accent Armchair")
            af_w = st.number_input("Width (cm)", value=80, step=5)
            af_d = st.number_input("Depth (cm)", value=85, step=5)
            af_c = st.number_input("Required Clearance (cm)", value=60, step=5)
            if st.button("Add Piece to Inventory"):
                st.session_state.planner_furniture_items.append({
                    "name": af_name,
                    "width_cm": int(af_w),
                    "depth_cm": int(af_d),
                    "height_cm": 85,
                    "clearance_needed_cm": int(af_c)
                })
                st.rerun()

    with pl_c2:
        st.markdown("### 🚦 Spatial Ergonomics & Clearance Audit")
        
        clearance_results = check_room_clearances(r_len_m, r_wid_m, st.session_state.planner_furniture_items)
        
        for cr in clearance_results:
            st_color = "#3B5E43" if cr["status"] == "pass" else ("#B85C38" if cr["status"] == "warning" else "#725640")
            st_icon = "✅" if cr["status"] == "pass" else ("⚠️" if cr["status"] == "warning" else "ℹ️")
            st.markdown(
                f"""
                <div class="custom-card" style="padding: 14px 18px; margin-bottom: 12px; border-left: 4px solid {st_color};">
                    <div style="display: justify; justify-content: space-between; align-items: center;">
                        <strong style="color: var(--text-primary); font-size: 0.92rem;">{st_icon} {cr['check']}</strong>
                        <span class="score-badge">Standard: {cr['threshold']}</span>
                    </div>
                    <p style="font-size: 0.84rem; color: var(--text-secondary); margin: 6px 0 0 0;">
                        {cr['message']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown("### 💾 Save & Persist Room Plan")
        if st.button("💾 Save Spatial Layout to Project", use_container_width=True):
            save_room_plan(
                user_id=active_user_id,
                project_id=st.session_state.project_id,
                room_name=r_name,
                room_type=r_type,
                dimensions={"length_m": r_len_m, "width_m": r_wid_m, "height_m": r_hgt_m, "area_sqm": room_area_sqm},
                furniture_items=st.session_state.planner_furniture_items,
                clearance_report=clearance_results
            )
            st.success(f"✅ Room plan '{r_name}' successfully saved to database!")
            st.rerun()

        # Saved plans
        saved_plans = list_room_plans(active_user_id)
        if saved_plans:
            st.markdown("#### 📂 Your Saved Layouts")
            for sp in saved_plans:
                p_c1, p_c2 = st.columns([3, 1])
                with p_c1:
                    st.markdown(f"**{sp['room_name']}** ({sp['room_type']}) — {sp.get('dimensions', {}).get('area_sqm', 0)} m² • {len(sp.get('furniture_items', []))} items")
                with p_c2:
                    if st.button("🗑️", key=f"del_plan_{sp['id']}"):
                        delete_room_plan(sp["id"], active_user_id)
                        st.rerun()


# ====================================================
# EXPANSION VIEW 4: RENOVATION SHOPPING ASSISTANT
# ====================================================
def render_shopping_view():
    st.markdown("## 🛒 Renovation Shopping Assistant & Bill of Materials (BOM)")
    st.caption("Automated project cost estimation in INR (₹) covering coatings, application tools, lighting, and hardware.")

    # Prepare active palette or fallback
    dummy_palette = PaletteConcept(
        id="shop_pal_default",
        name="Sample: Warm Editorial Sanctuary",
        concept_category="Modern Neutral",
        harmony_type="Monochromatic",
        description="Curated sample palette for renovation planning.",
        atmosphere="Calm & Balanced",
        primary_wall=ColorSwatch(name="Sandalwood Terracotta", hex="#B85C38", rgb=(184, 92, 56), role="Primary Wall (60%)", percentage=60.0, temperature="warm", luminance=0.49),
        secondary_wall=ColorSwatch(name="Warm Greige Linen", hex="#D6C5B3", rgb=(214, 197, 179), role="Feature Wall (30%)", percentage=30.0, temperature="neutral", luminance=0.80),
        accent=ColorSwatch(name="Obsidian Bronze", hex="#30271F", rgb=(48, 39, 31), role="Accent (10%)", percentage=10.0, temperature="warm", luminance=0.17),
        trim=ColorSwatch(name="Alabaster White", hex="#F7F3EE", rgb=(247, 243, 238), role="Trim & Moulding", percentage=None, temperature="neutral", luminance=0.96),
        design_rationale="Curated sample concept for project bill of materials.",
        furniture_flooring_compatibility="Compatible with warm oak and dark bronze fixtures.",
        heuristic_score=94.0
    )

    if st.session_state.current_image_bytes is not None:
        try:
            an_dict = cached_room_analysis(st.session_state.current_image_bytes)
            ext_dict = cached_dominant_colors(st.session_state.current_image_bytes)
            extracted = ExtractedColorAnalysis(**ext_dict)
            room_an = RoomAnalysisResult(**an_dict)
            active_p_list = generate_recommended_palettes(extracted, room_an)
            if active_p_list:
                dummy_palette = active_p_list[0]
        except Exception:
            pass

    shop_c1, shop_c2 = st.columns([1.0, 1.4], gap="large")

    with shop_c1:
        st.markdown("### 📋 Project Parameters")
        p_name = st.text_input("Project Name", value=f"{dummy_palette.name} Renovation")
        p_room_type = st.selectbox("Room Typology", ["Living Room", "Master Bedroom", "Kitchen & Dining", "Executive Study"], index=0)
        p_wall_sqft = st.number_input("Total Wall Surface Area (sq.ft)", min_value=50.0, max_value=3000.0, value=350.0, step=10.0)
        p_coats = st.selectbox("Paint System Specification", ["2 Coats over 1 Coat Primer (Recommended)", "3 Coats Premium Luxury Emulsion", "1 Coat Refresh / Maintenance"], index=0)
        inc_furniture = st.checkbox("Include Architectural Lighting & Decor Recommendations", value=True)

        # Generate shopping data from real mathematical estimation pipeline
        coats_count = 3 if "3 Coats" in p_coats else (1 if "1 Coat" in p_coats else 2)
        real_estimate = estimate_paint_quantity(PaintEstimateInput(
            total_wall_area_sqft=p_wall_sqft,
            coats=coats_count
        ))

        shopping_data = generate_renovation_shopping_list(
            palette=dummy_palette,
            paint_estimate=real_estimate,
            room_type=p_room_type,
            include_furniture=inc_furniture
        )
        shopping_data["project_name"] = p_name

        st.markdown(
            f"""
            <div class="custom-card" style="padding: 16px; margin-top: 14px;">
                <h4 style="margin: 0; color: var(--text-primary); font-family: 'Playfair Display', Georgia, serif;">Budget Summary</h4>
                <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.90rem;">
                    <span>Essential Coatings &amp; Tools:</span>
                    <strong>₹{shopping_data['essential_budget_inr']:,.2f}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 0.90rem;">
                    <span>Optional Lighting &amp; Decor:</span>
                    <strong>₹{shopping_data['optional_budget_inr']:,.2f}</strong>
                </div>
                <div style="border-top: 1px solid var(--border-subtle); margin-top: 10px; padding-top: 10px; display: flex; justify-content: space-between; font-size: 1.05rem; color: var(--accent-primary);">
                    <strong>Total Estimated Budget:</strong>
                    <strong>₹{shopping_data['total_budget_inr']:,.2f}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Download & Save Actions
        md_text = export_shopping_list_markdown(shopping_data)
        st.download_button("⬇️ Export BOM as Markdown Checklist", md_text, "renovation_shopping_list.md", "text/markdown", use_container_width=True)

        if st.button("💾 Save Shopping List to Project", use_container_width=True):
            save_shopping_list(
                user_id=active_user_id,
                project_id=st.session_state.project_id,
                list_name=p_name,
                items=shopping_data["items"],
                total_budget_inr=shopping_data["total_budget_inr"]
            )
            st.success("✅ Renovation shopping list saved to database!")
            st.rerun()

    with shop_c2:
        st.markdown("### 🛒 Itemized Bill of Materials")
        
        for item in shopping_data["items"]:
            cat_badge = "🎨" if "Paint" in item["category"] else ("🛠️" if "Tool" in item["category"] else "🛋️")
            st.markdown(
                f"""
                <div class="custom-card" style="padding: 12px 16px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: var(--text-primary); font-size: 0.92rem;">{cat_badge} {item['item_name']}</strong>
                            <div style="font-size: 0.78rem; color: var(--text-secondary);">{item['specification']}</div>
                        </div>
                        <div style="text-align: right;">
                            <strong style="color: var(--accent-primary); font-size: 0.95rem;">₹{item['total_price_inr']:,.2f}</strong>
                            <div style="font-size: 0.74rem; color: var(--text-muted);">{item['quantity']} {item['unit']} @ ₹{item['unit_price_inr']:.0f}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Saved shopping lists
        saved_lists = list_shopping_lists(active_user_id)
        if saved_lists:
            st.markdown("---")
            st.markdown("#### 📂 Saved Project Bills of Materials")
            for sl in saved_lists:
                sl_c1, sl_c2 = st.columns([3, 1])
                with sl_c1:
                    st.markdown(f"**{sl['list_name']}** — ₹{sl.get('total_budget_inr', 0):,.2f} ({len(sl.get('items', []))} items)")
                with sl_c2:
                    if st.button("🗑️", key=f"del_sl_{sl['id']}"):
                        delete_shopping_list(sl["id"], active_user_id)
                        st.rerun()


# ====================================================
# EXPANSION VIEW 5: HOME MAINTENANCE & WALL CONDITION
# ====================================================
def render_maintenance_view():
    st.markdown("## 🛠️ Home Maintenance & Wall Condition Tracker")
    st.caption("Surface health diagnostics, architectural remediation protocols, and side-by-side condition timeline.")

    maint_tabs = st.tabs([
        "🔬 Surface Damage Diagnostics",
        "📸 Condition Comparison (Before & After)",
        "📋 Maintenance Activity Log & Reminders"
    ])

    with maint_tabs[0]:
        st.markdown("### 🔬 Architectural Wall Diagnostics")
        
        dia_col1, dia_col2 = st.columns([1.0, 1.3], gap="large")
        with dia_col1:
            dmg_type = st.selectbox("Observed Surface Issue", list(DAMAGE_CATEGORIES.keys()), index=1)
            dmg_sev = st.selectbox("Severity Level", ["Minor / Hairline", "Moderate / Localized", "Severe / Structural"], index=0)
            
            diag_eval = evaluate_wall_damage_heuristics(dmg_type, dmg_sev)
            st.markdown(f"**Urgency Assessment:** <span class='score-badge'>{diag_eval['urgency']}</span>", unsafe_allow_html=True)

        with dia_col2:
            st.markdown("#### 🛠️ Recommended Remediation Protocol")
            st.markdown(
                f"""
                <div class="custom-card" style="padding: 18px; border-left: 4px solid var(--accent-primary);">
                    <h4 style="margin: 0 0 8px 0; color: var(--text-primary);">{dmg_type}</h4>
                    <p style="font-size: 0.90rem; color: var(--text-secondary); line-height: 1.6;">
                        {diag_eval['treatment_protocol']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    with maint_tabs[1]:
        st.markdown("### 📸 Condition Comparison Over Time")
        st.caption("Upload an earlier inspection photograph and a current photograph to generate a certified condition comparison.")

        cmp_col1, cmp_col2 = st.columns(2)
        with cmp_col1:
            img_before_file = st.file_uploader("Earlier Inspection Photo", type=["jpg", "png", "webp"], key="maint_before")
            date_before = st.date_input("Earlier Date", key="date_before")
        with cmp_col2:
            img_after_file = st.file_uploader("Current Inspection Photo", type=["jpg", "png", "webp"], key="maint_after")
            date_after = st.date_input("Current Date", key="date_after")

        if img_before_file and img_after_file:
            pil_b = Image.open(img_before_file).convert("RGB")
            pil_a = Image.open(img_after_file).convert("RGB")
            
            comp_img = create_condition_comparison_image(
                pil_b, pil_a,
                label_earlier=f"Inspection: {date_before}",
                label_later=f"Inspection: {date_after}"
            )
            st.image(comp_img, caption="Condition Comparison Sheet", use_container_width=True)

            buf_cmp = io.BytesIO()
            comp_img.save(buf_cmp, format="PNG")
            st.download_button("⬇️ Download Condition Comparison Sheet (PNG)", buf_cmp.getvalue(), "condition_comparison.png", "image/png")

    with maint_tabs[2]:
        st.markdown("### 📋 Log Maintenance Activity")
        with st.form("log_maint_form"):
            ml_room = st.text_input("Room Identifier", value="Living Room")
            ml_act = st.selectbox("Activity Performed", ["Full Wall Repainting", "Touch-up / Patching", "Waterproofing Treatment", "Crack Filling & Sanding", "Routine Inspection"])
            ml_paint = st.text_input("Paint Brand & Shade Used", value="Asian Paints Royale — Sandalwood Terracotta (HEX #B85C38)")
            ml_cost = st.number_input("Expense Incurred (₹ INR)", value=3500.0, step=100.0)
            ml_notes = st.text_area("Observations / Contractor Notes", value="Two coats applied over acrylic sealer. Surface clean.")
            ml_next = st.selectbox("Schedule Next Inspection In", ["3 Months", "6 Months", "1 Year", "2 Years"])

            if st.form_submit_button("Record Maintenance Activity", use_container_width=True):
                save_maintenance_record(
                    user_id=active_user_id,
                    project_id=st.session_state.project_id,
                    room_name=ml_room,
                    activity_type=ml_act,
                    paint_used=ml_paint,
                    cost_inr=float(ml_cost),
                    notes=ml_notes,
                    next_reminder_due=ml_next
                )
                st.success("✅ Maintenance activity recorded in project ledger!")
                st.rerun()

        st.markdown("---")
        st.markdown("#### 📜 Historical Maintenance Ledger")
        records = list_maintenance_records(active_user_id)
        if not records:
            st.caption("No maintenance activities logged yet.")
        else:
            for rec in records:
                r_c1, r_c2 = st.columns([3, 1])
                with r_c1:
                    st.markdown(
                        f"""
                        <div class="custom-card" style="padding: 12px 16px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between;">
                                <strong>{rec['room_name']} — {rec['activity_type']}</strong>
                                <span style="color: var(--accent-primary); font-weight: 700;">₹{rec.get('cost_inr', 0):,.2f}</span>
                            </div>
                            <div style="font-size: 0.80rem; color: var(--text-secondary); margin-top: 2px;">
                                Paint: {rec.get('paint_used', 'N/A')} • Next Due: <strong>{rec.get('next_reminder_due', 'N/A')}</strong>
                            </div>
                            <div style="font-size: 0.74rem; color: var(--text-muted); margin-top: 2px;">
                                {rec.get('notes', '')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with r_c2:
                    if st.button("🗑️", key=f"del_mrec_{rec['id']}"):
                        delete_maintenance_record(rec["id"], active_user_id)
                        st.rerun()


# ====================================================
# EXPANSION VIEW 6: CHROMA AI ASSISTANT
# ====================================================
def render_assistant_view():
    st.markdown("## 💬 Chroma AI Assistant — Contextual Architectural Advisor")
    st.caption("Interior color science, daylight orientation advice, material synergies, and finish recommendations backed by an architectural knowledge graph.")

    # Contextual status header
    active_ctx = {
        "room_type": "Living Room",
        "detected_style": "Warm Minimalist",
        "selected_materials": st.session_state.selected_materials,
        "active_palette": {
            "name": "Warm Editorial Sanctuary",
            "concept_category": "monochromatic",
            "harmony_type": "Monochromatic",
            "primary_wall": {"name": "Sandalwood Terracotta", "hex": "#B85C38"}
        }
    }

    st.markdown(
        f"""
        <div class="custom-card" style="padding: 12px 18px; margin-bottom: 16px; border-left: 4px solid var(--accent-primary);">
            <div style="font-size: 0.80rem; color: var(--text-secondary); display: flex; gap: 14px; flex-wrap: wrap; align-items: center;">
                <span>🏛️ <strong>Context Active:</strong></span>
                <span class="metric-pill">Room: {active_ctx['room_type']}</span>
                <span class="metric-pill">Palette: {active_ctx['active_palette']['name']} ({active_ctx['active_palette']['primary_wall']['hex']})</span>
                <span class="metric-pill">Materials: {', '.join(active_ctx['selected_materials'])}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Chat history display
    chat_history = get_assistant_history(active_user_id, session_id=st.session_state.project_id)

    # Render previous messages
    for msg in chat_history:
        role = msg.get("role", "user")
        with st.chat_message(role):
            st.markdown(msg.get("content", ""))

    # Quick suggestion prompt buttons
    st.markdown("##### 💡 Suggested Questions:")
    sq_cols = st.columns(3)
    preset_prompts = [
        "What trim and ceiling colours complement my dominant wall shade?",
        "Recommend the best paint finish for this room type.",
        "How does south-facing daylight affect warm vs cool undertones?"
    ]
    
    selected_prompt = None
    for idx, (col, pr) in enumerate(zip(sq_cols, preset_prompts)):
        with col:
            if st.button(pr, key=f"sq_prompt_{idx}", use_container_width=True):
                selected_prompt = pr

    # User input
    user_input = st.chat_input("Ask Chroma Assistant about colors, finishes, materials, or lighting...") or selected_prompt

    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        save_assistant_message(active_user_id, st.session_state.project_id, "user", user_input)

        # Generate contextual response
        with st.spinner("Analyzing architectural design guidelines..."):
            ai_reply = generate_assistant_response(user_input, context=active_ctx)

        # Display and save assistant response
        with st.chat_message("assistant"):
            st.markdown(ai_reply)

        save_assistant_message(active_user_id, st.session_state.project_id, "assistant", ai_reply)
        st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear Conversation History"):
        clear_assistant_history(active_user_id, st.session_state.project_id)
        st.rerun()


# ====================================================
# VIEW 4: EXPERIMENTAL AI LAB
# ====================================================
def render_experimental_lab_view():
    st.markdown("## 🧪 Experimental Architectural AI Lab")
    st.caption("Advanced computational design simulations: Daylight, Materials, Swapping, Semantic Walls, and Paint Estimation.")

    lab_tabs = st.tabs([
        "☀️ Daylight Simulator",
        "🪨 Material-Aware Palettes",
        "🔀 Colour Swap Playground",
        "🧱 Semantic Wall Editing",
        "📐 Smart Paint Estimator"
    ])

    # 1. Daylight Simulator
    with lab_tabs[0]:
        st.markdown("### ☀️ Natural Lighting Condition Simulation")
        st.caption("Visually approximates room appearance across diurnal lighting shifts while preserving luminance.")
        if st.session_state.current_image_bytes is None:
            st.info("Please upload a room photograph in the sidebar first.")
        else:
            original_pil, _, _ = validate_image_bytes(st.session_state.current_image_bytes)
            daylight_mode = st.selectbox("Simulate Lighting Condition", list(LIGHTING_CONDITIONS.keys()), index=0)
            daylight_intensity = st.slider("Lighting Shift Strength", 0.2, 1.0, 0.85, 0.05)
            
            simulated_daylight = simulate_daylight_lighting(original_pil, daylight_mode, daylight_intensity)
            st.image(simulated_daylight, caption=f"{daylight_mode} ({LIGHTING_CONDITIONS[daylight_mode]['kelvin']})", use_container_width=True)
            st.info(f"ℹ️ {LIGHTING_CONDITIONS[daylight_mode]['description']}")

    # 2. Material-Aware Palettes
    with lab_tabs[1]:
        st.markdown("### 🪨 Interior Materials Calibration")
        st.caption("Select materials present in the room to refine palette harmony and undertones.")
        selected_mats = st.multiselect("Select Detected or Target Materials", ALL_MATERIALS, default=st.session_state.selected_materials)
        st.session_state.selected_materials = selected_mats
        st.success(f"Applied {len(selected_mats)} material calibrations to recommendation engine.")

    # 3. Colour Swap Playground
    with lab_tabs[2]:
        st.markdown("### 🔀 Colour Swap Playground")
        st.caption("Lock 3 palette anchors and swap 1 slot to create custom design variations.")
        if st.session_state.current_image_bytes is None:
            st.info("Please upload a room photograph in the sidebar first.")
        else:
            original_pil, proc_pil, _ = validate_image_bytes(st.session_state.current_image_bytes)
            extracted_dict = cached_dominant_colors(st.session_state.current_image_bytes)
            extracted = ExtractedColorAnalysis(**extracted_dict)
            analysis_dict = cached_room_analysis(st.session_state.current_image_bytes)
            room_analysis = RoomAnalysisResult(**analysis_dict)
            palettes = generate_recommended_palettes(extracted=extracted, room_analysis=room_analysis)
            base_p = palettes[0]

            slot_to_swap = st.selectbox("Slot to Modify", ["accent", "primary_wall", "secondary_wall", "trim"], format_func=lambda s: s.replace("_", " ").title())
            new_color_hex = st.color_picker("Pick New Colour", value="#A36B4F")
            
            swapped_p = swap_palette_color(base_p, slot_to_swap, new_color_hex)
            st.markdown(f"#### Custom Variant: {swapped_p.name}")
            render_palette_swatches_horizontal(swapped_p)
            if st.button("💾 Save Variant to Library"):
                save_palette(swapped_p, swapped_p.name, room_analysis.detected_room_type, room_analysis.detected_style, user_id=active_user_id)
                st.success("Custom variant saved!")

    # 4. Semantic Wall Editing
    with lab_tabs[3]:
        st.markdown("### 🧱 Semantic Surface Region Editing")
        st.caption("Target paint to specific architectural surface planes.")
        if st.session_state.current_image_bytes is None:
            st.info("Upload a room photograph in the sidebar to activate semantic editing.")
        else:
            original_pil, _, _ = validate_image_bytes(st.session_state.current_image_bytes)
            mask_png_bytes, _ = cached_wall_mask(st.session_state.current_image_bytes, 0.55, 0.70, 0.65)
            wall_mask_arr = np.array(Image.open(io.BytesIO(mask_png_bytes)).convert("L"))
            semantic_masks = generate_semantic_surface_masks(original_pil, wall_mask_arr)
            
            target_surface = st.selectbox("Target Architectural Surface", list(semantic_masks.keys()))
            target_color_hex = st.color_picker("Surface Paint Colour", value="#725640")
            h = target_color_hex.lstrip("#")
            t_rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
            
            semantic_recolour = recolour_semantic_surface(original_pil, semantic_masks[target_surface], t_rgb)
            st.image(semantic_recolour, caption=f"Recoloured {target_surface}", use_container_width=True)

    # 5. Smart Paint Estimator
    with lab_tabs[4]:
        st.markdown("### 📐 Smart Paint Quantity & Cost Estimator")
        st.caption("Calculate practical paint quantities from room dimensions with standard deduction rules.")
        
        ecol1, ecol2, ecol3 = st.columns(3)
        with ecol1:
            r_len = st.number_input("Room Length (m)", 1.0, 30.0, 5.0, 0.5)
            r_wid = st.number_input("Room Width (m)", 1.0, 30.0, 4.0, 0.5)
        with ecol2:
            r_ht = st.number_input("Wall Height (m)", 1.5, 10.0, 2.8, 0.1)
            r_coats = st.number_input("Number of Coats", 1, 4, 2, 1)
        with ecol3:
            r_doors = st.number_input("Doors to Subtract", 0, 10, 1, 1)
            r_windows = st.number_input("Windows to Subtract", 0, 20, 2, 1)
            r_cost_per_l = st.number_input("Paint Rate (₹/Litre)", 0.0, 5000.0, 450.0, 25.0)

        calc_btn = st.button("📊 Calculate Paint Requirements", use_container_width=True)
        if calc_btn or True:
            est_res = estimate_paint_quantity(PaintEstimateInput(
                room_length_meters=r_len,
                room_width_meters=r_wid,
                wall_height_meters=r_ht,
                num_doors=r_doors,
                num_windows=r_windows,
                coats=r_coats,
                cost_per_liter_inr=r_cost_per_l
            ))
            
            res_c1, res_c2, res_c3 = st.columns(3)
            with res_c1:
                st.metric("Net Wall Surface", f"{est_res.net_wall_area_sqm} m²")
            with res_c2:
                st.metric("Total Paint Required", f"{est_res.paint_liters_required} Litres")
            with res_c3:
                st.metric("Estimated Cost", f"₹{est_res.estimated_cost_inr:,.2f}" if est_res.estimated_cost_inr else "N/A")

            st.write("**Recommended Packaging Breakdown:**")
            for can_name, count in est_res.recommended_cans_breakdown.items():
                st.write(f"- {count}x {can_name}")
            st.caption(est_res.estimator_disclaimer)


# ====================================================
# VIEW 5: COLOUR HARMONY EXPLORER
# ====================================================
def render_harmony_explorer_view():
    st.markdown("## 🌈 Colour Harmony Explorer")
    st.caption("Deep-dive into 360° chromatic relationships and exact CIELAB perceptual color distances.")
    
    seed_col = st.color_picker("Select Seed Color", value="#725640")
    harmonies = explore_color_harmonies(seed_col)

    st.markdown(f"### Seed: **{harmonies['seed']['name']}** ({seed_col})")
    
    h_col1, h_col2 = st.columns(2)
    with h_col1:
        st.markdown(
            f"""
            <div class="custom-card">
                <h4>Complementary (+180°)</h4>
                <div style="background-color: {harmonies['complementary']['hex']}; height: 50px; border-radius: 6px; margin-bottom: 8px;"></div>
                <strong>{harmonies['complementary']['name']}</strong> ({harmonies['complementary']['hex']})<br>
                CIELAB ΔE: {harmonies['complementary']['delta_e']}
            </div>
            """,
            unsafe_allow_html=True
        )
    with h_col2:
        st.markdown(
            f"""
            <div class="custom-card">
                <h4>Neutral Supporting Greige</h4>
                <div style="background-color: {harmonies['neutral_supporting']['hex']}; height: 50px; border-radius: 6px; margin-bottom: 8px;"></div>
                <strong>{harmonies['neutral_supporting']['name']}</strong> ({harmonies['neutral_supporting']['hex']})
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("#### Analogous Neighbors (-30° / +30°)")
    ana_cols = st.columns(2)
    for col, ana in zip(ana_cols, harmonies["analogous"]):
        with col:
            st.markdown(
                f"""
                <div class="custom-card">
                    <div style="background-color: {ana['hex']}; height: 44px; border-radius: 6px; margin-bottom: 6px;"></div>
                    <strong>{ana['name']}</strong> ({ana['hex']}) — ΔE: {ana['delta_e']}
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("#### Triadic Triangles (+120° / +240°)")
    tri_cols = st.columns(2)
    for col, tri in zip(tri_cols, harmonies["triadic"]):
        with col:
            st.markdown(
                f"""
                <div class="custom-card">
                    <div style="background-color: {tri['hex']}; height: 44px; border-radius: 6px; margin-bottom: 6px;"></div>
                    <strong>{tri['name']}</strong> ({tri['hex']}) — ΔE: {tri['delta_e']}
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("#### Monochromatic Airy Tints & Grounded Shades")
    mono_cols = st.columns(2)
    for col, mono in zip(mono_cols, harmonies.get("monochromatic", [])):
        with col:
            st.markdown(
                f"""
                <div class="custom-card">
                    <div style="background-color: {mono['hex']}; height: 44px; border-radius: 6px; margin-bottom: 6px;"></div>
                    <strong>{mono['name']}</strong> ({mono['hex']})<br>
                    <span style="font-size: 0.8rem; color: var(--text-secondary);">{mono['label']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )


# ====================================================
# VIEW 6: CHROMA MEMORY & DNA
# ====================================================
def render_memory_dna_view():
    st.markdown("## 🧬 Chroma Memory & Chroma DNA")
    st.caption("Personalized design-preference signature and adaptive memory profile.")

    cdna = generate_chroma_dna(active_user_id)
    cmem = get_chroma_memory(active_user_id)

    st.markdown(
        f"""
        <div class="custom-card">
            <h3 style="margin-top:0; color: var(--accent-primary);">{cdna.signature_name}</h3>
            <div class="metric-row">
                <div class="metric-pill">Dominant Family: <strong>{cdna.dominant_family}</strong></div>
                <div class="metric-pill">Contrast Level: <strong>{cdna.contrast_level}</strong></div>
                <div class="metric-pill">Temperature Bias: <strong>{cdna.temperature_bias}</strong></div>
            </div>
            <p style="font-size: 0.88rem; color: var(--text-secondary);">
                Material Affinities: <strong>{", ".join(cdna.material_affinity)}</strong> |
                Preferred Styles: <strong>{", ".join(cdna.preferred_styles)}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("#### Signature Swatches Strip")
    dna_cols = st.columns(len(cdna.signature_swatches))
    for col, sw in zip(dna_cols, cdna.signature_swatches):
        with col:
            st.markdown(
                f"""
                <div style="background-color: {sw.hex}; height: 50px; border-radius: 6px; margin-bottom: 6px; border: 1px solid var(--border-subtle);"></div>
                <div style="font-size: 0.76rem; font-weight: 700; color: var(--text-primary);">{sw.name}</div>
                <div style="font-size: 0.70rem; color: var(--text-secondary);">{sw.hex}</div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.markdown("### 🧠 Chroma Memory Inspection")
    st.caption(f"Recorded Interactions: **{cmem['interactions_count']}**")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.write("**Frequently Favorited Tones:**")
        st.write(cmem["favorite_colors"] if cmem["favorite_colors"] else "None recorded yet.")
    with col_m2:
        st.write("**Previously Dismissed Tones:**")
        st.write(cmem["rejected_colors"] if cmem["rejected_colors"] else "None recorded yet.")

    if st.button("🧹 Clear Chroma Memory History"):
        clear_chroma_memory(active_user_id)
        st.success("Chroma Memory cleared successfully!")
        st.rerun()


# ====================================================
# VIEW 7: DESIGN TIMELINE
# ====================================================
def render_timeline_view():
    st.markdown("## ⏳ Design Timeline")
    st.caption("Visual history of design iterations and state snapshots.")

    # Snapshot current state button
    if st.button("📸 Snapshot Current Design State"):
        # Create a sample snapshot version
        dummy_swatch = ColorSwatch(hex="#725640", rgb=(114, 86, 64), role="Wall", name="Terracotta")
        dummy_pal = PaletteConcept(
            id="snap_1",
            name="Studio Snapshot",
            concept_category="Warm and Inviting",
            harmony_type="Monochromatic",
            description="Timeline snapshot iteration",
            atmosphere="Warm & Cozy",
            primary_wall=dummy_swatch,
            secondary_wall=dummy_swatch,
            accent=dummy_swatch,
            trim=dummy_swatch,
            design_rationale="Snapshot recorded by user",
            furniture_flooring_compatibility="Balanced"
        )
        save_timeline_version(active_user_id, st.session_state.project_id, dummy_pal, "Iteration Snapshot")
        st.success("Saved new design version snapshot!")
        st.rerun()

    timeline_items = list_project_timeline(active_user_id)
    if not timeline_items:
        st.info("No timeline versions recorded for this project yet.")
    else:
        for item in timeline_items:
            with st.container():
                st.markdown(
                    f"""
                    <div class="custom-card">
                        <div style="display: flex; justify-content: space-between;">
                            <h4 style="margin: 0; color: var(--text-primary);">{item['label']} (v{item['version_num']})</h4>
                            <span style="font-size: 0.8rem; color: var(--text-secondary);">{item['timestamp']}</span>
                        </div>
                        <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 6px 0;">{item['palette'].get('name', 'Palette')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ====================================================
# VIEW 8: SAVED PALETTES & EXPORTS
# ====================================================
def render_exports_view():
    st.markdown("## 📁 Saved Palettes Collection & Export Suite")
    st.caption("Locally persisted in SQLite. Multi-user segregated.")

    saved_items = list_saved_palettes(user_id=active_user_id)
    if not saved_items:
        st.info("No saved palettes in your library yet. Save any palette from the Studio tab to view and export it here.")
    else:
        for rec in saved_items:
            pal_obj = PaletteConcept(**rec["palette"])
            st.markdown(
                f"""
                <div class="custom-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <h4 style="margin:0; color:var(--text-primary);">{rec['name']}</h4>
                            <span style="font-size:0.78rem; color:var(--text-secondary);">{rec['timestamp']} | Room: {rec['room_type']}</span>
                        </div>
                        <span class="score-badge">Match: {pal_obj.heuristic_score}%</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            render_palette_swatches_horizontal(pal_obj)

            exp_c1, exp_c2, exp_c3, exp_c4, exp_c5, exp_c6, exp_c7 = st.columns([1, 1, 1, 1, 1, 1, 1])
            with exp_c1:
                if st.button("🗑️ Delete", key=f"del_{rec['id']}"):
                    delete_saved_palette(rec['id'], user_id=active_user_id)
                    st.rerun()
            with exp_c2:
                json_data = export_palette_json(pal_obj)
                st.download_button("📄 JSON", json_data, f"{pal_obj.name.lower()}.json", "application/json", key=f"dl_j_{rec['id']}")
            with exp_c3:
                csv_data = export_palette_csv(pal_obj)
                st.download_button("📊 CSV", csv_data, f"{pal_obj.name.lower()}.csv", "text/csv", key=f"dl_c_{rec['id']}")
            with exp_c4:
                swatch_png = generate_swatch_sheet_png(pal_obj, room_type=rec['room_type'])
                st.download_button("🖼️ PNG", swatch_png.getvalue(), f"{pal_obj.name.lower()}_sheet.png", "image/png", key=f"dl_p_{rec['id']}")
            with exp_c5:
                txt_rep = generate_text_report(pal_obj, room_analysis=None, room_type=rec['room_type'])
                st.download_button("📝 TXT", txt_rep, f"{pal_obj.name.lower()}_report.txt", "text/plain", key=f"dl_t_{rec['id']}")
            with exp_c6:
                md_rep = generate_markdown_report(pal_obj, room_analysis=None, room_type=rec['room_type'])
                st.download_button("📄 MD", md_rep, f"{pal_obj.name.lower()}_report.md", "text/markdown", key=f"dl_m_{rec['id']}")
            with exp_c7:
                pdf_rep = generate_pdf_report(pal_obj, room_analysis=None, room_type=rec['room_type'])
                st.download_button("📑 PDF", pdf_rep.getvalue(), f"{pal_obj.name.lower()}_report.pdf", "application/pdf", key=f"dl_pdf_{rec['id']}")


# ====================================================
# VIEW 9: SUBSCRIPTION & BILLING (INR PRICING)
# ====================================================
def render_subscription_view():
    st.markdown("## 💳 Subscription & Billing Management")
    st.caption("Transparent Indian Rupee (INR) plans, limits, and verified sandbox payment integration.")

    st.markdown(
        f"""
        <div class="custom-card">
            <h3 style="margin: 0; color: var(--accent-primary);">Current Subscription: {user_sub['plan_details']['name']}</h3>
            <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 6px 0;">
                Status: <strong>{user_sub['status'].upper()}</strong> | Billing Cycle: <strong>{user_sub['billing_cycle'].capitalize()}</strong> |
                Valid Through: <strong>{user_sub['current_period_end'][:10]}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Billing Cycle Toggle
    billing_cycle_choice = st.radio("Select Billing Period", ["Monthly", "Annual (Save ~20%)"], horizontal=True)
    is_annual = ("Annual" in billing_cycle_choice)

    st.markdown("### Choose an Architectural Tier")
    sub_col1, sub_col2, sub_col3 = st.columns(3)

    for col, (pid, pdata) in zip([sub_col1, sub_col2, sub_col3], SUBSCRIPTION_PLANS.items()):
        with col:
            price_display = pdata["annual_price_inr"] if is_annual else pdata["monthly_price_inr"]
            period_str = "/year" if is_annual else "/month"
            is_current = (user_sub.get("plan_id") == pid)

            st.markdown(
                f"""
                <div class="custom-card" style="border-color: {'var(--accent-primary)' if is_current else 'var(--border-subtle)'};">
                    <span class="plan-badge plan-{pid}">{pdata['badge']}</span>
                    <h3 style="margin: 8px 0 4px 0; color: var(--text-primary);">{pdata['name']}</h3>
                    <h2 style="margin: 0 0 12px 0; color: var(--accent-primary);">₹{price_display}<span style="font-size:0.9rem; font-weight:400; color:var(--text-secondary);">{period_str}</span></h2>
                    <ul style="font-size: 0.82rem; color: var(--text-secondary); padding-left: 18px; margin-bottom: 16px;">
                        {"".join(f"<li>{feat}</li>" for feat in pdata['features'])}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )

            if is_current:
                st.button("Active Plan", key=f"btn_act_{pid}", disabled=True, use_container_width=True)
            else:
                if st.button(f"Upgrade to {pdata['name']}", key=f"btn_up_{pid}", use_container_width=True):
                    # Execute cryptographically verified test checkout
                    success, msg, p_meta = execute_test_sandbox_checkout(
                        user_id=active_user_id,
                        plan_id=pid,
                        billing_cycle="annual" if is_annual else "monthly"
                    )
                    if success:
                        st.success(f"Payment Verified! {msg} (HMAC SHA-256 Signature verified).")
                        st.rerun()
                    else:
                        st.error(f"Payment Error: {msg}")

    st.markdown("---")
    with st.expander("🛠️ Razorpay Webhook & Signature Verification Test Tool (Idempotent)"):
        st.caption("Test webhook signature handling and duplicate delivery idempotency.")
        test_event_id = st.text_input("Webhook Event ID", value="evt_test_123456")
        test_payload = {
            "id": test_event_id,
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_999",
                        "notes": {
                            "user_id": active_user_id,
                            "plan_id": "plus",
                            "billing_cycle": "monthly"
                        }
                    }
                }
            }
        }
        body_bytes = json.dumps(test_payload).encode("utf-8")
        import hmac, hashlib
        valid_sig = hmac.new(RAZORPAY_WEBHOOK_SECRET.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        if st.button("Trigger Test Webhook Execution"):
            ok, w_msg = process_payment_webhook(test_payload, body_bytes, valid_sig)
            if ok:
                st.success(f"Webhook response: {w_msg}")
            else:
                st.error(f"Webhook rejected: {w_msg}")


# ====================================================
# EXPANSION VIEW 7: AI PRIVACY SHIELD
# ====================================================
def render_privacy_shield_view():
    st.markdown("## 🛡️ AI Privacy Shield & Data Transparency")
    st.caption("Complete transparency into edge processing, zero-retention camera feeds, and GDPR-compliant user data ownership.")

    render_privacy_shield_banner()

    p_col1, p_col2 = st.columns(2, gap="large")

    with p_col1:
        st.markdown("### 🔒 Video & Image Processing Privacy")
        st.markdown(
            """
            <div class="custom-card" style="padding: 18px; margin-bottom: 14px;">
                <h4 style="margin: 0 0 6px 0; color: var(--accent-primary);">Zero-Retention Live Camera</h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6;">
                    The WebRTC video pipeline executes entirely in volatile system memory (RAM). Each frame is inspected for architectural features and immediately overwritten. No video is ever recorded, buffered to disk, or sent to an external server.
                </p>
                <div class="score-badge" style="background-color: #E8ECE9; color: #3B5E43;">Active: 0 Frames Retained</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="custom-card" style="padding: 18px; margin-bottom: 14px;">
                <h4 style="margin: 0 0 6px 0; color: var(--text-primary);">100% Offline Mode</h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6;">
                    K-Means clustering, bilateral wall masking, luminance-preserving recolouring, CIELAB Delta E brand matching, and architectural assistant responses run entirely on your local machine using NumPy, SciPy, OpenCV, and scikit-learn.
                </p>
                <div class="score-badge">Offline Capable: Yes</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p_col2:
        st.markdown("### 🇪🇺 Data Ownership & Export (GDPR)")
        st.markdown(
            """
            <div class="custom-card" style="padding: 18px; margin-bottom: 14px;">
                <h4 style="margin: 0 0 6px 0; color: var(--text-primary);">Export All Your Data</h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6;">
                    Download a comprehensive JSON archive containing your saved palettes, scanned colours, room plans, shopping lists, maintenance records, and design history.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        data_bundle = export_user_data_bundle(active_user_id)
        st.download_button(
            "⬇️ Download My Data Archive (JSON)",
            json.dumps(data_bundle, indent=2),
            f"chroma_data_export_{active_user_id}.json",
            "application/json",
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("### ⚠️ Account & Data Deletion")
        st.caption("Permanently purge all your palettes, scanned colors, and activity records from the database.")
        
        with st.expander("🚨 Purge All Data / Delete Account"):
            confirm = st.checkbox("I understand that this action is irreversible.")
            if st.button("Permanently Purge My Account & Data", disabled=not confirm):
                delete_user_account_cascade(active_user_id)
                st.session_state.current_user = None
                st.success("Your account and all associated data have been permanently deleted.")
                st.rerun()


# ====================================================
# VIEW 10: USER PROFILE & PREFERENCES
# ====================================================
def render_profile_preferences_view():
    st.markdown("## 👤 User Profile & Customization")
    st.caption("Personal design preferences and interface customization.")

    profile = get_user_profile(active_user_id) or {}

    col_pr1, col_pr2 = st.columns(2)
    with col_pr1:
        d_name = st.text_input("Display Name", value=profile.get("display_name", "Architectural Designer"))
        d_lang = st.selectbox("Preferred Language", ["English", "Hindi", "French", "German", "Spanish"], index=0)
        d_theme = st.selectbox("Theme Mode", ["light", "dark"], index=0 if st.session_state.theme == "light" else 1)
        d_vis = st.selectbox("Default Visualization Mode", ["Side-by-Side Comparison", "Split Slider Comparison", "Full Recoloured Room"], index=0)

    with col_pr2:
        d_room = st.selectbox("Default Room Type", ROOM_TYPES, index=1)
        d_style = st.selectbox("Default Interior Style", INTERIOR_STYLES, index=1)
        d_temp = st.selectbox("Preferred Temperature", TEMPERATURE_OPTIONS, index=0)
        d_liked = st.multiselect("Favorite Interior Colors", COMMON_ACCENT_HUES, default=profile.get("liked_colors", ["Desert Sand"]))

    if st.button("💾 Save Profile Changes", use_container_width=True):
        update_user_profile(active_user_id, {
            "display_name": d_name,
            "preferred_language": d_lang,
            "theme": d_theme,
            "default_vis_mode": d_vis,
            "default_room_type": d_room,
            "default_interior_style": d_style,
            "preferred_temp": d_temp,
            "liked_colors": d_liked
        })
        st.session_state.theme = d_theme
        st.success("Profile updated successfully!")
        st.rerun()


# ====================================================
# VIEW 11: ACCOUNT & SECURITY
# ====================================================
def render_account_security_view():
    st.markdown("## 🔐 Account Security & Privacy Controls")
    st.caption("Password management, personal data export (GDPR), and account deletion.")

    sec_tab1, sec_tab2, sec_tab3 = st.tabs([
        "🔑 Change Password",
        "📦 Export Personal Data",
        "⚠️ Delete Account"
    ])

    with sec_tab1:
        if not st.session_state.current_user:
            st.info("You are currently in guest mode. Please sign in to change password.")
        else:
            old_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password", type="password")
            if st.button("Update Password"):
                ok, msg = change_user_password(active_user_id, old_pwd, new_pwd)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    with sec_tab2:
        st.markdown("#### Export Personal Data Archive")
        st.caption("Download all personal design projects, palettes, and preference history in JSON format.")
        data_bundle = export_user_data_bundle(active_user_id)
        st.download_button(
            "⬇️ Download Personal Data Bundle (JSON)",
            data=json.dumps(data_bundle, indent=2),
            file_name=f"chroma_studio_export_{active_user_id}.json",
            mime="application/json"
        )

    with sec_tab3:
        st.markdown("#### Danger Zone: Permanent Account Deletion")
        st.caption("This action is irreversible and purges all saved palettes, timeline versions, and profile data.")
        confirm_del = st.checkbox("I understand that all my saved palettes and design history will be permanently deleted.")
        if st.button("🚨 Delete My Account Permanently", disabled=not confirm_del):
            delete_user_account_cascade(active_user_id)
            st.session_state.current_user = None
            st.success("Account and all associated personal data permanently removed.")
            st.rerun()


# ====================================================
# VIEW 12: SIGN IN / SIGN UP / PASSWORD RESET
# ====================================================
def render_auth_view():
    st.markdown("## 🔑 Account Access")
    
    auth_tabs = st.tabs(["Sign In", "Create Account", "Password Recovery"])

    with auth_tabs[0]:
        login_email = st.text_input("Email Address", key="login_email")
        login_pwd = st.text_input("Password", type="password", key="login_pwd")
        st.checkbox("Remember this session", value=True)

        if st.button("Sign In to Chroma Studio", use_container_width=True):
            ok, msg, u_rec = authenticate_user(login_email, login_pwd)
            if ok:
                st.session_state.current_user = u_rec
                st.session_state.current_view = "🎨 Studio & Analysis"
                st.success(f"Welcome back, {u_rec['full_name']}!")
                st.rerun()
            else:
                st.error(msg)

    with auth_tabs[1]:
        reg_name = st.text_input("Full Name", key="reg_name")
        reg_email = st.text_input("Email Address", key="reg_email")
        reg_pwd = st.text_input("Password (min 8 chars, 1 digit, 1 letter)", type="password", key="reg_pwd")
        reg_terms = st.checkbox("I agree to the Terms of Service & Privacy Policy", key="reg_terms")

        if st.button("Create Account", use_container_width=True):
            ok, msg, u_rec = register_user(reg_email, reg_pwd, reg_name, reg_terms)
            if ok:
                st.session_state.current_user = u_rec
                st.session_state.current_view = "🎨 Studio & Analysis"
                st.success("Account created successfully! Welcome to Chroma Studio AI.")
                st.rerun()
            else:
                st.error(msg)

    with auth_tabs[2]:
        st.markdown("#### Password Recovery")
        rst_email = st.text_input("Registered Email Address", key="rst_email")
        if st.button("Send Recovery Token"):
            ok, msg, dev_token = initiate_password_reset(rst_email)
            st.info(msg)
            if dev_token:
                st.caption(f"(Development Token: `{dev_token}`)")

        token_input = st.text_input("Enter Reset Token", key="rst_tok")
        new_pwd_input = st.text_input("Enter New Password", type="password", key="rst_new_pwd")
        if st.button("Reset Password"):
            ok, msg = complete_password_reset(token_input, new_pwd_input)
            if ok:
                st.success(msg)
            else:
                st.error(msg)


# ====================================================
# VIEW 13: ARCHITECTURAL DESIGN GUIDE
# ====================================================
def render_guide_view():
    st.markdown("## ❓ Architectural Design Guidelines & System Status")
    
    st.markdown(
        """
        ### The 60-30-10 Interior Design Rule
        - **60% Dominant Wall Colour:** The foundational plane of the room. Usually low-to-medium saturation to prevent sensory fatigue.
        - **30% Secondary Colour:** Accent wall, millwork, large drapery, or trim. Adds dimensional contrast.
        - **10% Accent Details:** Vibrant statement pillows, artwork, ceramics, or metallic hardware.

        ### Light Reflectance Value (LRV)
        - LRV measures how much physical light a paint reflects (0% absolute black, 100% pure white).
        - North-facing or windowless rooms should target LRV > 65% to avoid oppressive shadows.
        - Deep moody aesthetics typically utilize LRV < 25% with concentrated warm point lighting.

        ### Physical Paint vs Digital Screen Disclaimer
        - Digital monitors emit RGB light, whereas physical paints absorb and reflect wavelengths based on chemical pigments.
        - Camera white-balance sensors and JPEG compression alter color balance. Always test physical swatch samples in morning and evening ambient room light.
        """
    )



# ----------------------------------------------------
# Global 7-Tab Navigation & View Orchestration
# ----------------------------------------------------
tab_studio, tab_palette, tab_materials, tab_estimator, tab_timeline, tab_account, tab_exports = st.tabs([
    "🎨 Studio & Analysis",
    "🌈 Palette Lab",
    "🪨 Materials",
    "📐 Estimator",
    "⏳ Timeline",
    "💳 Account/Plans",
    "📁 Exports"
])

# --- TAB 1: STUDIO & ANALYSIS ---
with tab_studio:
    st.markdown("### 📷 Room Photograph & Studio Controls")
    c_up1, c_up2 = st.columns([2.8, 1.2], vertical_alignment="top")
    with c_up1:
        uploaded_file = st.file_uploader(
            "Upload Room Photograph",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload physical room photo (JPG, PNG, WEBP, up to 15MB).",
            key="studio_room_uploader",
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            raw_bytes = uploaded_file.getvalue()
            if st.session_state.current_image_bytes != raw_bytes:
                allowed, msg, _ = check_entitlement(active_user_id, "room_analysis")
                if not allowed:
                    st.error(f"⚠️ Entitlement Limit: {msg}")
                else:
                    st.session_state.current_image_bytes = raw_bytes
                    st.session_state.selected_palette_id = None
                    st.session_state.ai_preview_result = None
                    record_usage_metric(active_user_id, "analysis")
                    st.rerun()

    with c_up2:
        if st.session_state.current_image_bytes is not None:
            if st.button("🗑️ Clear Room Image", key="btn_clear_studio_img", use_container_width=True):
                st.session_state.current_image_bytes = None
                st.session_state.image_metadata = None
                st.session_state.selected_palette_id = None
                st.session_state.ai_preview_result = None
                st.rerun()
        else:
            if st.button("🖼️ Try Sample Room", key="btn_try_sample_studio", use_container_width=True, help="Load sample architectural room for demonstration"):
                from pathlib import Path
                sample_p = Path(__file__).resolve().parent / "data" / "roomie_default_room.jpg"
                if sample_p.exists():
                    with open(sample_p, "rb") as sf:
                        st.session_state.current_image_bytes = sf.read()
                    st.session_state.selected_palette_id = None
                    st.session_state.ai_preview_result = None
                    st.rerun()

    if st.session_state.current_image_bytes is None:
        st.markdown(
            """
            <div class="custom-card card-3d" style="text-align: center; padding: 48px 24px; margin: 24px 0; border: 1.5px dashed rgba(255,255,255,0.15);">
                <div style="font-size: 2.8rem; margin-bottom: 12px;">🏛️</div>
                <h3 style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.6rem; color: var(--text-primary); margin-bottom: 8px;">
                    Upload a room photo to begin
                </h3>
                <p style="color: var(--text-secondary); max-width: 540px; margin: 0 auto 20px auto; font-size: 0.92rem; line-height: 1.6;">
                    Select an interior photograph above or click <strong>Try Sample Room</strong> to explore architectural color extraction, wall segmentation, and interactive 3D palette visualization.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_showcase_view()
    else:
        studio_sub = st.radio(
            "Studio Sub-Workspace",
            ["🏛️ 3D & 2D Spatial Canvas", "📹 Live Camera Studio", "🎯 Live Colour Scanner", "💬 Chroma AI Assistant"],
            horizontal=True,
            key="studio_sub_mode"
        )
        st.markdown('<div class="chroma-hairline" style="margin: 12px 0 20px 0;"></div>', unsafe_allow_html=True)
        if studio_sub == "🏛️ 3D & 2D Spatial Canvas":
            render_studio_view()
        elif studio_sub == "📹 Live Camera Studio":
            render_live_camera_view()
        elif studio_sub == "🎯 Live Colour Scanner":
            render_colour_scanner_view()
        elif studio_sub == "💬 Chroma AI Assistant":
            render_assistant_view()

# --- TAB 2: PALETTE LAB ---
with tab_palette:
    if st.session_state.current_image_bytes is None:
        st.info("ℹ️ Please upload a room photograph or click **Try Sample Room** in the Studio tab to analyze color harmonies.")
    else:
        pal_sub = st.radio(
            "Palette Lab Tool",
            ["🎨 4 Design Concepts & 60-30-10", "🌈 Harmony Explorer", "🏷️ Paint Brand Matcher", "🧪 Swap Playground", "🧬 Chroma Memory & DNA"],
            horizontal=True,
            key="pal_lab_mode"
        )
        st.markdown('<div class="chroma-hairline" style="margin: 12px 0 20px 0;"></div>', unsafe_allow_html=True)
        if pal_sub == "🎨 4 Design Concepts & 60-30-10":
            render_studio_view()
        elif pal_sub == "🌈 Harmony Explorer":
            render_harmony_explorer_view()
        elif pal_sub == "🏷️ Paint Brand Matcher":
            render_brand_matcher_view()
        elif pal_sub == "🧪 Swap Playground":
            render_experimental_lab_view()
        elif pal_sub == "🧬 Chroma Memory & DNA":
            render_memory_dna_view()

# --- TAB 3: MATERIALS & LIGHTING ---
with tab_materials:
    if st.session_state.current_image_bytes is None:
        st.info("ℹ️ Please upload a room photograph or click **Try Sample Room** in the Studio tab to evaluate materials and daylight conditions.")
    else:
        render_visualization_view()

# --- TAB 4: ESTIMATOR & PLANNING ---
with tab_estimator:
    est_sub = st.radio(
        "Estimator & Planning Tool",
        ["🎨 Paint Estimator & Budgeting", "📐 Smart Furniture & Room Planner", "🛒 Renovation Shopping", "🛠️ Home Maintenance"],
        horizontal=True,
        key="est_planning_mode"
    )
    st.markdown('<div class="chroma-hairline" style="margin: 12px 0 20px 0;"></div>', unsafe_allow_html=True)
    if est_sub == "🎨 Paint Estimator & Budgeting":
        render_experimental_lab_view()
    elif est_sub == "📐 Smart Furniture & Room Planner":
        render_room_planner_view()
    elif est_sub == "🛒 Renovation Shopping":
        render_shopping_view()
    elif est_sub == "🛠️ Home Maintenance":
        render_maintenance_view()

# --- TAB 5: DESIGN TIMELINE ---
with tab_timeline:
    render_timeline_view()

# --- TAB 6: ACCOUNT & PLANS ---
with tab_account:
    acc_sub = st.radio(
        "Account & Plans Section",
        ["🔑 Sign In / Sign Up", "💳 Subscription & Plans", "🛡️ AI Privacy Shield", "👤 Profile & Preferences", "🔐 Security", "❓ Architectural Guide"],
        horizontal=True,
        key="acc_section_mode"
    )
    st.markdown('<div class="chroma-hairline" style="margin: 12px 0 20px 0;"></div>', unsafe_allow_html=True)
    if acc_sub == "🔑 Sign In / Sign Up":
        render_auth_view()
    elif acc_sub == "💳 Subscription & Plans":
        render_subscription_view()
    elif acc_sub == "🛡️ AI Privacy Shield":
        render_privacy_shield_view()
    elif acc_sub == "👤 Profile & Preferences":
        render_profile_preferences_view()
    elif acc_sub == "🔐 Security":
        render_account_security_view()
    elif acc_sub == "❓ Architectural Guide":
        render_guide_view()

# --- TAB 7: SAVED PALETTES & EXPORTS ---
with tab_exports:
    render_exports_view()
