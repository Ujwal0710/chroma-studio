"""CHROMA STUDIO AI - Intelligent Architectural Colour & Interior Design Workspace.

Futuristic Premium Edition.
"""
import io
import os
import hashlib
import json
from typing import Optional, Dict, Any, List, Tuple
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
    UserProfile,
    PaintEstimateInput
)

# Core modules
from modules.image_validation import validate_image_bytes, ImageValidationError
from modules.colour_extraction import extract_dominant_colors
from modules.room_analysis import analyze_room_photograph
from modules.palette_engine import generate_recommended_palettes
from modules.wall_segmentation import generate_wall_mask
from modules.room_visualization import (
    apply_luminance_preserving_recolour,
    create_side_by_side_comparison,
    create_split_slider_comparison,
    create_mask_overlay_preview
)
from modules.ai_preview import request_ai_enhanced_preview
from modules.storage import (
    init_db,
    save_palette,
    list_saved_palettes,
    delete_saved_palette,
    get_saved_palette_by_id,
    save_user_preferences_preset,
    get_user_profile,
    update_user_profile,
    delete_user_account_cascade,
    export_user_data_bundle
)
from modules.export_service import (
    export_palette_json,
    export_palette_csv,
    generate_swatch_sheet_png,
    generate_text_report
)
from modules.preferences import (
    ATMOSPHERE_OPTIONS,
    TEMPERATURE_OPTIONS,
    LIGHTNESS_OPTIONS,
    COLORFULNESS_OPTIONS,
    ACCENT_INTENSITY_OPTIONS,
    BUDGET_OPTIONS,
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
    update_user_subscription,
    check_entitlement,
    record_usage_metric,
    get_user_usage,
    execute_test_sandbox_checkout,
    verify_razorpay_webhook_signature,
    process_payment_webhook
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
from modules.daylight_simulator import simulate_daylight_lighting, LIGHTING_CONDITIONS
from modules.material_palettes import evaluate_material_compatibility, ALL_MATERIALS
from modules.colour_swap import swap_palette_color
from modules.paint_estimator import estimate_paint_quantity
from modules.semantic_wall import generate_semantic_surface_masks, recolour_semantic_surface

# UI & Styling
from ui.styles import get_theme_css
from ui.components import (
    render_header,
    render_dominant_color_strip,
    render_room_analysis_card,
    render_palette_swatches_horizontal,
    render_explainability_card
)

# Page configuration
st.set_page_config(
    page_title=f"{APP_NAME} — Futuristic Premium Edition",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
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
    st.session_state.theme = "light"
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
def cached_wall_mask(image_bytes: bytes, sensitivity: float, upper_bias: float, edge_protection: float) -> Tuple[bytes, Dict[str, Any]]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    mask, meta = generate_wall_mask(
        img,
        sensitivity=sensitivity,
        upper_bias=upper_bias,
        edge_protection=edge_protection
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
with st.sidebar:
    st.markdown(f"### 🏛️ {APP_NAME}")
    
    nav_options = [
        "🏛️ Showcase / Landing",
        "🎨 Studio & Analysis",
        "🖼️ Visualization Studio",
        "🧪 Experimental AI Lab",
        "🌈 Harmony Explorer",
        "🧬 Chroma Memory & DNA",
        "⏳ Design Timeline",
        "📁 Saved Palettes & Exports",
        "💳 Subscription & Billing",
        "👤 Profile & Preferences",
        "🔐 Account & Security",
        "🔑 Sign In / Sign Up",
        "❓ Architectural Guide"
    ]
    
    # Auto-select index
    current_idx = 1
    if st.session_state.current_view in nav_options:
        current_idx = nav_options.index(st.session_state.current_view)
        
    selected_view = st.selectbox(
        "Navigation Workspace",
        nav_options,
        index=current_idx,
        label_visibility="collapsed"
    )
    
    if selected_view != st.session_state.current_view:
        st.session_state.current_view = selected_view
        st.rerun()

    st.markdown("---")

    # User Quick Status & Theme Switcher
    if st.session_state.current_user:
        st.caption(f"Signed in as **{st.session_state.current_user['full_name']}**")
        col_out, col_thm = st.columns([1, 1])
        with col_out:
            if st.button("Sign Out", use_container_width=True):
                st.session_state.current_user = None
                st.rerun()
        with col_thm:
            theme_label = "🌙 Dark" if st.session_state.theme == "light" else "☀️ Light"
            if st.button(theme_label, use_container_width=True):
                st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
                st.rerun()
    else:
        st.caption("Guest Session — All Local CV tools active")
        if st.button("🔑 Sign In / Sign Up", use_container_width=True):
            st.session_state.current_view = "🔑 Sign In / Sign Up"
            st.rerun()

    st.markdown("---")
    
    # Global Room Image Uploader (Shared across workspaces)
    st.markdown("### 📷 Room Image")
    uploaded_file = st.file_uploader(
        "Upload Room Photograph",
        type=["jpg", "jpeg", "png", "webp"],
        help="Upload physical room photo (JPG, PNG, WEBP, up to 15MB)."
    )
    if uploaded_file is not None:
        raw_bytes = uploaded_file.getvalue()
        if st.session_state.current_image_bytes != raw_bytes:
            # Check server-side analysis entitlement
            allowed, msg, _ = check_entitlement(active_user_id, "room_analysis")
            if not allowed:
                st.error(f"⚠️ Entitlement Limit: {msg}")
            else:
                st.session_state.current_image_bytes = raw_bytes
                st.session_state.selected_palette_id = None
                st.session_state.ai_preview_result = None
                record_usage_metric(active_user_id, "analysis")
                st.rerun()

    if st.session_state.current_image_bytes is not None:
        if st.button("🗑️ Clear Room Image", use_container_width=True):
            st.session_state.current_image_bytes = None
            st.session_state.image_metadata = None
            st.session_state.selected_palette_id = None
            st.session_state.ai_preview_result = None
            st.rerun()


# ====================================================
# VIEW 1: SHOWCASE / LANDING PAGE
# ====================================================
if st.session_state.current_view == "🏛️ Showcase / Landing":
    st.markdown(
        """
        <div class="custom-card" style="text-align: center; padding: 40px 20px;">
            <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.5rem; margin-bottom: 12px; color: var(--text-primary);">
                Elevate Physical Spaces with Architectural Colour Science
            </h2>
            <p style="font-size: 1.1rem; color: var(--text-secondary); max-width: 760px; margin: 0 auto 24px auto;">
                An intelligent design workspace that transforms uploaded room photographs into personalized colour concepts,
                luminance-preserving wall previews, and actionable specifications.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        st.markdown(
            """
            <div class="custom-card">
                <h4 style="color: var(--accent-primary); margin-top:0;">1. Computer Vision</h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary);">
                    K-Means clustering and ITU-R BT.709 perceptual luminance extract representative room tones while filtering sensor blowout.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_w2:
        st.markdown(
            """
            <div class="custom-card">
                <h4 style="color: var(--accent-primary); margin-top:0;">2. Harmony Engine</h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary);">
                    Generates 4 distinct architectural concepts enforcing the 60-30-10 interior rule with CIELAB Delta-E deduplication.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_w3:
        st.markdown(
            """
            <div class="custom-card">
                <h4 style="color: var(--accent-primary); margin-top:0;">3. Shading-Preserving Preview</h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary);">
                    Simulates paint application on segmented wall planes while strictly retaining ambient daylight falloff, texture, and shadows.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 💎 Distinctive Architectural Features")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        st.markdown(
            """
            <div class="custom-card">
                <strong>Chroma Memory</strong>
                <p style="font-size: 0.82rem; color: var(--text-secondary);">Adapts recommendations to your saved preferences and rejected tones over time.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_f2:
        st.markdown(
            """
            <div class="custom-card">
                <strong>Chroma DNA</strong>
                <p style="font-size: 0.82rem; color: var(--text-secondary);">Inspectable design signature profile with your core contrast and temperature tendencies.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_f3:
        st.markdown(
            """
            <div class="custom-card">
                <strong>Daylight Simulator</strong>
                <p style="font-size: 0.82rem; color: var(--text-secondary);">Visual simulation of Morning, Neutral, Overcast, and Evening ambient lighting conditions.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_f4:
        st.markdown(
            """
            <div class="custom-card">
                <strong>Material-Aware Ranking</strong>
                <p style="font-size: 0.82rem; color: var(--text-secondary);">Harmonizes recommendations against Oak, Walnut, Marble, Stone, Linen, and Brass.</p>
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
elif st.session_state.current_view == "🎨 Studio & Analysis":
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

        # Top section: Image & Observations
        col_img, col_info = st.columns([1.1, 1.4])
        with col_img:
            st.image(original_pil, caption=f"Room Photograph ({metadata['width']}x{metadata['height']})", use_container_width=True)
        with col_info:
            render_room_analysis_card(room_analysis)
            render_dominant_color_strip(extracted)

        st.markdown("---")
        st.markdown("### 🎨 Recommended Architectural Palettes")

        for pal in palettes:
            is_active = (pal.id == st.session_state.selected_palette_id)
            card_border = "var(--accent-primary)" if is_active else "var(--border-subtle)"

            st.markdown(
                f"""
                <div class="palette-card" style="border-color: {card_border}; border-width: {'2px' if is_active else '1px'};">
                    <div class="palette-header">
                        <div>
                            <span style="font-size: 0.76rem; text-transform: uppercase; font-weight: 700; color: var(--accent-primary); letter-spacing: 0.5px;">
                                {pal.concept_category} • {pal.harmony_type}
                            </span>
                            <h3 class="palette-title">{pal.name}</h3>
                        </div>
                        <div>
                            <span class="score-badge">Match Score: {pal.heuristic_score}%</span>
                        </div>
                    </div>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 4px 0 12px 0;">
                        {pal.description}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            render_palette_swatches_horizontal(pal)

            # Palette Card Actions
            b_col1, b_col2, b_col3, b_col4 = st.columns([1.2, 1, 1, 1.5])
            with b_col1:
                if st.button("👁️ Active Preview" if is_active else "👉 Preview", key=f"preview_{pal.id}", use_container_width=True, disabled=is_active):
                    st.session_state.selected_palette_id = pal.id
                    st.rerun()
            with b_col2:
                if st.button("💾 Save", key=f"save_{pal.id}", use_container_width=True):
                    # Check entitlement
                    allowed, msg, _ = check_entitlement(active_user_id, "save_palette")
                    if not allowed:
                        st.error(msg)
                    else:
                        rec_id = save_palette(
                            palette=pal,
                            custom_name=pal.name,
                            room_type=room_analysis.detected_room_type,
                            interior_style=room_analysis.detected_style,
                            preferences=current_preferences,
                            user_id=active_user_id
                        )
                        record_favorite_palette(active_user_id, pal, style=room_analysis.detected_style)
                        st.session_state.save_status_message = f"✅ Saved '{pal.name}' to library!"
                        st.rerun()
            with b_col3:
                if st.button("👎 Dismiss", key=f"dismiss_{pal.id}", use_container_width=True):
                    record_rejected_palette(active_user_id, pal)
                    st.caption("Noted in Chroma Memory.")
            with b_col4:
                st.code(f"{pal.primary_wall.hex}, {pal.secondary_wall.hex}, {pal.accent.hex}, {pal.trim.hex}", language="text")

            # Explainability & Confidence
            render_explainability_card(pal)
            st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.save_status_message:
            st.success(st.session_state.save_status_message)
            st.session_state.save_status_message = None


# ====================================================
# VIEW 3: ROOM VISUALIZATION STUDIO
# ====================================================
elif st.session_state.current_view == "🖼️ Visualization Studio":
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
        st.caption(f"Primary Wall Paint: **{active_palette.primary_wall.name}** ({active_palette.primary_wall.hex})")

        vis_tabs = st.tabs([
            "🛠️ Mode 1: Local Wall Recolouring (Shading & Texture Preserved)",
            "✨ Mode 2: AI-Enhanced Preview (Generative Render)"
        ])

        with vis_tabs[0]:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.session_state.recolour_intensity = st.slider("Paint Intensity", 0.2, 1.0, float(st.session_state.recolour_intensity), 0.05)
            with c2:
                st.session_state.mask_sensitivity = st.slider("Wall Sensitivity", 0.2, 0.9, float(st.session_state.mask_sensitivity), 0.05)
            with c3:
                st.session_state.edge_protection = st.slider("Edge Protection", 0.3, 0.95, float(st.session_state.edge_protection), 0.05)
            with c4:
                preview_type = st.selectbox("Comparison View", ["Side-by-Side Comparison", "Split Slider Comparison", "Full Recoloured Room", "Wall Mask Overlay"])

            mask_png_bytes, mask_meta = cached_wall_mask(
                st.session_state.current_image_bytes,
                st.session_state.mask_sensitivity,
                st.session_state.upper_bias,
                st.session_state.edge_protection
            )
            wall_mask_arr = np.array(Image.open(io.BytesIO(mask_png_bytes)).convert("L"))
            recoloured_room = apply_luminance_preserving_recolour(
                original_pil,
                wall_mask_arr,
                active_palette.primary_wall.rgb,
                intensity=st.session_state.recolour_intensity
            )

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

            # Download recoloured preview
            rec_buf = io.BytesIO()
            recoloured_room.save(rec_buf, format="PNG")
            st.download_button("⬇️ Download High-Res Preview (PNG)", rec_buf.getvalue(), "recoloured_room.png", "image/png")

        with vis_tabs[1]:
            st.markdown("#### AI-Enhanced Generative Preview")
            has_edit_key = bool(IMAGE_EDIT_API_KEY.strip())
            if not has_edit_key:
                st.info("ℹ️ AI Image Editing API key not detected in `.env`. Mode 1 local wall recolouring is active with 100% full luminance preservation.")
            
            # Check entitlement for AI preview
            can_ai, ai_msg, _ = check_entitlement(active_user_id, "ai_preview")
            if not can_ai:
                st.warning(f"⚠️ Plan Limit: {ai_msg}")
            
            if st.button("✨ Request AI-Enhanced Room Render", disabled=(not has_edit_key or not can_ai)):
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
# VIEW 4: EXPERIMENTAL AI LAB
# ====================================================
elif st.session_state.current_view == "🧪 Experimental AI Lab":
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
elif st.session_state.current_view == "🌈 Harmony Explorer":
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


# ====================================================
# VIEW 6: CHROMA MEMORY & DNA
# ====================================================
elif st.session_state.current_view == "🧬 Chroma Memory & DNA":
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
elif st.session_state.current_view == "⏳ Design Timeline":
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
elif st.session_state.current_view == "📁 Saved Palettes & Exports":
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

            exp_c1, exp_c2, exp_c3, exp_c4, exp_c5 = st.columns([1, 1, 1, 1, 1])
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
                st.download_button("🖼️ PNG Sheet", swatch_png.getvalue(), f"{pal_obj.name.lower()}_sheet.png", "image/png", key=f"dl_p_{rec['id']}")
            with exp_c5:
                # Text Report
                dummy_ext = ExtractedColorAnalysis(dominant_colors=[], overall_brightness=0.5, overall_temperature_tendency="neutral", mean_saturation=0.5, neutral_count=1, warm_count=1, cool_count=1, lighting_condition_estimate="Daylight")
                txt_rep = generate_text_report(pal_obj, None, dummy_ext)
                st.download_button("📝 Report", txt_rep, f"{pal_obj.name.lower()}_report.txt", "text/plain", key=f"dl_t_{rec['id']}")


# ====================================================
# VIEW 9: SUBSCRIPTION & BILLING (INR PRICING)
# ====================================================
elif st.session_state.current_view == "💳 Subscription & Billing":
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
# VIEW 10: USER PROFILE & PREFERENCES
# ====================================================
elif st.session_state.current_view == "👤 Profile & Preferences":
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
elif st.session_state.current_view == "🔐 Account & Security":
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
elif st.session_state.current_view == "🔑 Sign In / Sign Up":
    st.markdown("## 🔑 Account Access")
    
    auth_tabs = st.tabs(["Sign In", "Create Account", "Password Recovery"])

    with auth_tabs[0]:
        login_email = st.text_input("Email Address", key="login_email")
        login_pwd = st.text_input("Password", type="password", key="login_pwd")
        rem_me = st.checkbox("Remember this session", value=True)

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
elif st.session_state.current_view == "❓ Architectural Guide":
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
