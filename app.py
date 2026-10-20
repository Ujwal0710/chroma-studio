"""AI Interior Colour Palette Suggester - Main Streamlit Application."""
import io
import os
import hashlib
from typing import Optional, Dict, Any, List
from PIL import Image
import numpy as np

# Streamlit import
import streamlit as st

# Application modules
from config.settings import (
    DESIGN_TOKENS,
    ROOM_TYPES,
    INTERIOR_STYLES,
    VISION_API_KEY,
    IMAGE_EDIT_API_KEY,
    VISION_MODEL,
    IMAGE_EDIT_MODEL
)
from models.schemas import (
    PaletteConcept,
    RoomAnalysisResult,
    ExtractedColorAnalysis,
    PreferenceSettings,
    ColorSwatch
)
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
    save_user_preferences_preset,
    list_saved_preferences_presets
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
    COMMON_ACCENT_HUES,
    create_default_preferences
)
from ui.styles import MAIN_CSS
from ui.components import (
    render_header,
    render_dominant_color_strip,
    render_room_analysis_card,
    render_palette_swatches_horizontal
)

# Page configuration
st.set_page_config(
    page_title="AI Interior Colour Palette Suggester",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom design system CSS
st.markdown(MAIN_CSS, unsafe_allow_html=True)

# Initialize database
init_db()


# ----------------------------------------------------
# Caching helpers
# ----------------------------------------------------
def get_image_bytes_hash(img_bytes: bytes) -> str:
    """Compute MD5 hash for image bytes to serve as stable cache key."""
    return hashlib.md5(img_bytes).hexdigest()


@st.cache_data(show_spinner=False)
def cached_dominant_colors(image_bytes: bytes, num_colors: int = 7) -> Dict[str, Any]:
    """Cached dominant color extraction."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    extracted = extract_dominant_colors(img, num_colors=num_colors)
    return extracted.model_dump()


@st.cache_data(show_spinner=False)
def cached_wall_mask(image_bytes: bytes, sensitivity: float, upper_bias: float, edge_protection: float) -> Tuple[bytes, Dict[str, Any]]:
    """Cached wall mask computation. Returns mask bytes and metadata."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    mask, meta = generate_wall_mask(
        img,
        sensitivity=sensitivity,
        upper_bias=upper_bias,
        edge_protection=edge_protection
    )
    # Convert uint8 mask to PNG bytes for caching
    mask_img = Image.fromarray(mask, mode="L")
    buf = io.BytesIO()
    mask_img.save(buf, format="PNG")
    return buf.getvalue(), meta


# ----------------------------------------------------
# Session State Initialization
# ----------------------------------------------------
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


# ----------------------------------------------------
# Main Application Header
# ----------------------------------------------------
render_header()

# Top Navigation Tabs
tab_studio, tab_saved, tab_settings = st.tabs([
    "🎨 Palette Studio & Room Visualizer",
    "📁 Saved Palettes & History",
    "⚙️ Model Configuration & Design Guide"
])


# ====================================================
# TAB 1: STUDIO & ROOM VISUALIZER
# ====================================================
with tab_studio:
    # Sidebar: Upload, Room Type, & Interactive Preferences
    with st.sidebar:
        st.markdown("### 1. Room Image")
        uploaded_file = st.file_uploader(
            "Upload Room Photograph",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a real photograph of an interior room (JPG, PNG, or WEBP, max 15MB)."
        )

        # Image replace / clear actions
        if uploaded_file is not None:
            raw_bytes = uploaded_file.getvalue()
            if st.session_state.current_image_bytes != raw_bytes:
                st.session_state.current_image_bytes = raw_bytes
                st.session_state.selected_palette_id = None
                st.session_state.ai_preview_result = None

        if st.session_state.current_image_bytes is not None:
            col_rm, col_info = st.columns([1, 1])
            with col_rm:
                if st.button("🗑️ Remove Image", use_container_width=True):
                    st.session_state.current_image_bytes = None
                    st.session_state.image_metadata = None
                    st.session_state.selected_palette_id = None
                    st.session_state.ai_preview_result = None
                    st.rerun()

        st.markdown("---")
        st.markdown("### 2. Room Specifications")
        sel_room_type = st.selectbox("Room Type", ROOM_TYPES, index=0)
        sel_style = st.selectbox("Interior Design Style", INTERIOR_STYLES, index=0)

        st.markdown("---")
        st.markdown("### 3. Interactive Preferences")
        pref_temp = st.selectbox("Colour Temperature", TEMPERATURE_OPTIONS, index=0)
        pref_light = st.selectbox("Lightness Level", LIGHTNESS_OPTIONS, index=0)
        pref_color = st.selectbox("Colour Saturation", COLORFULNESS_OPTIONS, index=0)
        pref_atmos = st.selectbox("Desired Atmosphere", ATMOSPHERE_OPTIONS, index=0)
        pref_accent = st.selectbox("Accent Intensity", ACCENT_INTENSITY_OPTIONS, index=0)

        pref_colors = st.multiselect(
            "Preferred Tones (Guide harmonies)",
            COMMON_ACCENT_HUES,
            default=[]
        )

        avoid_colors = st.multiselect(
            "Colours to Avoid",
            COMMON_ACCENT_HUES,
            default=[]
        )

        furniture_constraint = st.text_input(
            "Existing Furniture / Flooring Notes",
            value="Warm oak flooring, light linen sofa",
            help="Describe dominant furniture materials to calibrate compatibility scoring."
        )

        budget_cat = st.selectbox("Budget Category", BUDGET_OPTIONS, index=0)

        btn_apply = st.button("✨ Apply Preferences & Regenerate", use_container_width=True)

    # Active preferences bundle
    current_preferences = PreferenceSettings(
        room_type=sel_room_type,
        interior_style=sel_style,
        temperature_preference=pref_temp,
        lightness_preference=pref_light,
        colorfulness_preference=pref_color,
        desired_atmosphere=pref_atmos,
        accent_intensity=pref_accent,
        preferred_colors=pref_colors,
        colors_to_avoid=avoid_colors,
        furniture_flooring_constraints=furniture_constraint,
        budget_category=budget_cat
    )

    # Main Area: Processing and Results
    if st.session_state.current_image_bytes is None:
        # Empty state prompt
        st.info("👋 **Welcome to the AI Interior Colour Palette Suggester.** Please upload a room photograph in the sidebar to begin analysis and wall colour simulation.")

        # Display sample workflow guide
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            st.markdown(
                """
                <div class="custom-card">
                    <h4 style="color: #725640; margin-top:0;">1. Computer Vision</h4>
                    <p style="font-size: 0.85rem; color: #786B60;">
                        Extracts dominant room tones with K-Means clustering, calculates perceptual luminance, and estimates ambient lighting tendencies.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_g2:
            st.markdown(
                """
                <div class="custom-card">
                    <h4 style="color: #725640; margin-top:0;">2. Harmony Engine</h4>
                    <p style="font-size: 0.85rem; color: #786B60;">
                        Creates 4 distinct architectural concepts (Warm & Inviting, Cool & Calming, Modern Neutral, Bold Accent) using colour theory.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_g3:
            st.markdown(
                """
                <div class="custom-card">
                    <h4 style="color: #725640; margin-top:0;">3. Wall Recolouring</h4>
                    <p style="font-size: 0.85rem; color: #786B60;">
                        Simulates new paint on detected wall planes while preserving real room lighting, shadows, furniture, and woodwork.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    else:
        # Step 3: Validate and decode image
        try:
            original_pil, proc_pil, metadata = validate_image_bytes(
                st.session_state.current_image_bytes,
                filename="room_photograph.jpg"
            )
            st.session_state.image_metadata = metadata
        except ImageValidationError as e:
            st.error(f"❌ Image Validation Error: {str(e)}")
            st.stop()

        # Step 4 & 5: Colour Extraction and Room Analysis
        with st.spinner("Analyzing room photograph and extracting colour palette..."):
            extracted_dict = cached_dominant_colors(st.session_state.current_image_bytes)
            extracted = ExtractedColorAnalysis(**extracted_dict)

            # Room analysis (Vision API or Local Fallback)
            room_analysis = analyze_room_photograph(
                proc_pil,
                extracted_analysis=extracted,
                selected_room_type=sel_room_type,
                selected_style=sel_style
            )

        # Step 6: Recommendation Engine generates 4 concepts
        palettes = generate_recommended_palettes(
            extracted=extracted,
            room_analysis=room_analysis,
            preferences=current_preferences
        )

        # Set default selection if none selected
        if not st.session_state.selected_palette_id or not any(p.id == st.session_state.selected_palette_id for p in palettes):
            st.session_state.selected_palette_id = palettes[0].id

        active_palette = next((p for p in palettes if p.id == st.session_state.selected_palette_id), palettes[0])

        # Top section: Image and Extracted Colours
        col_img, col_info = st.columns([1.1, 1.4])
        with col_img:
            st.image(original_pil, caption=f"Original Photograph ({metadata['width']}x{metadata['height']}, {metadata['size_mb']} MB)", use_container_width=True)

        with col_info:
            render_room_analysis_card(room_analysis)
            render_dominant_color_strip(extracted)

        st.markdown("---")

        # Step 7: Recommended Palette Concepts
        st.markdown("## 🎨 Recommended Architectural Palettes")
        st.caption("Each palette is mathematically balanced using color theory and tuned to your room's optical properties and preferences.")

        # Render 4 Palette Concept Cards
        for i, pal in enumerate(palettes):
            is_active = (pal.id == st.session_state.selected_palette_id)
            card_border = "#725640" if is_active else "#E3D8CB"
            badge_bg = "#725640" if is_active else "#F0E8DD"
            badge_text = "#FFFFFF" if is_active else "#725640"

            st.markdown(
                f"""
                <div class="palette-card" style="border-color: {card_border}; border-width: {'2px' if is_active else '1px'};">
                    <div class="palette-header">
                        <div>
                            <span style="font-size: 0.78rem; text-transform: uppercase; font-weight: 700; color: #725640; letter-spacing: 0.5px;">
                                {pal.concept_category} • {pal.harmony_type}
                            </span>
                            <h3 class="palette-title">{pal.name}</h3>
                        </div>
                        <div style="text-align: right;">
                            <span class="score-badge" style="background-color: {badge_bg}; color: {badge_text};">
                                Match Score: {pal.heuristic_score}%
                            </span>
                        </div>
                    </div>
                    <p style="font-size: 0.88rem; color: #786B60; margin: 4px 0 12px 0;">
                        {pal.description}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Swatches row
            render_palette_swatches_horizontal(pal)

            # Actions inside card
            btn_col1, btn_col2, btn_col3 = st.columns([1.2, 1, 1.5])
            with btn_col1:
                if st.button(
                    "👁️ Active Preview" if is_active else "👉 Preview This Palette",
                    key=f"btn_preview_{pal.id}",
                    use_container_width=True,
                    disabled=is_active
                ):
                    st.session_state.selected_palette_id = pal.id
                    st.rerun()

            with btn_col2:
                # Quick save button
                if st.button("💾 Save Palette", key=f"btn_save_{pal.id}", use_container_width=True):
                    rec_id = save_palette(
                        palette=pal,
                        custom_name=pal.name,
                        room_type=room_analysis.detected_room_type,
                        interior_style=room_analysis.detected_style,
                        preferences=current_preferences,
                        notes=f"Saved from studio recommendation. Atmosphere: {pal.atmosphere}"
                    )
                    st.session_state.save_status_message = f"✅ Saved '{pal.name}' to database (ID: {rec_id})!"
                    st.rerun()

            with btn_col3:
                # Copy hex codes summary
                hex_summary = f"{pal.primary_wall.hex}, {pal.secondary_wall.hex}, {pal.accent.hex}, {pal.trim.hex}"
                st.code(hex_summary, language="text")

            with st.expander(f"Architectural Details & Furniture Compatibility for {pal.name}"):
                st.markdown(f"**Atmosphere Goal:** {pal.atmosphere}")
                st.markdown(f"**Design Rationale:** {pal.design_rationale}")
                st.markdown(f"**Furniture & Flooring Harmony:** {pal.furniture_flooring_compatibility}")
                st.markdown("**Heuristic Score Breakdown:**")
                st.json(pal.score_breakdown)

            st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.save_status_message:
            st.success(st.session_state.save_status_message)
            st.session_state.save_status_message = None

        st.markdown("---")

        # Step 8: Room Colour Visualization (Mode 1 & Mode 2)
        st.markdown("## 🖼️ Room Colour Visualization")
        st.caption(f"Currently Visualizing: **{active_palette.name}** | Primary Wall Colour: **{active_palette.primary_wall.name}** ({active_palette.primary_wall.hex})")

        vis_tab1, vis_tab2 = st.tabs([
            "🛠️ Mode 1: Local Wall Recolouring (Shading & Texture Preserved)",
            "✨ Mode 2: AI-Enhanced Preview (Generative Model)"
        ])

        with vis_tab1:
            # Controls for Wall Recolouring
            ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1, 1, 1, 1])
            with ctrl_col1:
                st.session_state.recolour_intensity = st.slider(
                    "Paint Intensity",
                    min_value=0.20,
                    max_value=1.00,
                    value=float(st.session_state.recolour_intensity),
                    step=0.05,
                    help="Controls the density of new paint applied to the walls."
                )
            with ctrl_col2:
                st.session_state.mask_sensitivity = st.slider(
                    "Wall Detection Sensitivity",
                    min_value=0.20,
                    max_value=0.90,
                    value=float(st.session_state.mask_sensitivity),
                    step=0.05,
                    help="Higher values expand detected wall areas; lower values restrict to clear center planes."
                )
            with ctrl_col3:
                st.session_state.edge_protection = st.slider(
                    "Edge Protection",
                    min_value=0.30,
                    max_value=0.95,
                    value=float(st.session_state.edge_protection),
                    step=0.05,
                    help="Protects furniture contours, window frames, and floorboards from paint spill."
                )
            with ctrl_col4:
                preview_mode_type = st.selectbox(
                    "Comparison View",
                    ["Side-by-Side Comparison", "Split Slider Comparison", "Full Recoloured Room", "Wall Mask Overlay"],
                    index=0
                )

            # Compute wall mask (cached)
            mask_png_bytes, mask_meta = cached_wall_mask(
                st.session_state.current_image_bytes,
                sensitivity=st.session_state.mask_sensitivity,
                upper_bias=st.session_state.upper_bias,
                edge_protection=st.session_state.edge_protection
            )
            wall_mask_arr = np.array(Image.open(io.BytesIO(mask_png_bytes)).convert("L"))

            # Apply real luminance-preserving wall recolouring
            recoloured_room = apply_luminance_preserving_recolour(
                original_img=original_pil,
                wall_mask=wall_mask_arr,
                target_rgb=active_palette.primary_wall.rgb,
                intensity=st.session_state.recolour_intensity
            )

            # Render selected comparison view
            if preview_mode_type == "Side-by-Side Comparison":
                comparison_img = create_side_by_side_comparison(
                    original_img=original_pil,
                    recoloured_img=recoloured_room,
                    paint_name=active_palette.primary_wall.name,
                    hex_code=active_palette.primary_wall.hex
                )
                st.image(comparison_img, use_container_width=True)

            elif preview_mode_type == "Split Slider Comparison":
                split_slider_val = st.slider("Divider Position", min_value=0.10, max_value=0.90, value=0.50, step=0.05)
                split_img = create_split_slider_comparison(
                    original_img=original_pil,
                    recoloured_img=recoloured_room,
                    split_ratio=split_slider_val,
                    paint_name=active_palette.primary_wall.name
                )
                st.image(split_img, use_container_width=True)

            elif preview_mode_type == "Full Recoloured Room":
                st.image(recoloured_room, caption=f"Recoloured with {active_palette.primary_wall.name} ({active_palette.primary_wall.hex})", use_container_width=True)

            else:  # Wall Mask Overlay
                overlay_img = create_mask_overlay_preview(original_pil, wall_mask_arr)
                st.image(overlay_img, caption=f"Wall Detection Mask Overlay (Coverage: {mask_meta['wall_coverage_percent']}%, Confidence: {mask_meta['segmentation_confidence']})", use_container_width=True)

            st.caption(
                f"Segmentation Coverage: **{mask_meta['wall_coverage_percent']}%** | "
                f"Status: **{mask_meta['segmentation_confidence']}** | "
                f"Luminance blending preserves ambient light falloff, physical shadows, and wall texture."
            )

            # Download button for recoloured preview
            rec_buf = io.BytesIO()
            recoloured_room.save(rec_buf, format="PNG")
            st.download_button(
                "⬇️ Download Recoloured Room Image (PNG)",
                data=rec_buf.getvalue(),
                file_name=f"room_recoloured_{active_palette.name.replace(' ', '_').lower()}.png",
                mime="image/png"
            )

        with vis_tab2:
            st.markdown("### AI-Enhanced Generative Preview")
            st.write(
                "If an image-generation model is configured (e.g. OpenAI DALL-E or Image Edit API), "
                "you can request an architectural render reflecting the chosen palette."
            )

            ai_key_configured = bool(IMAGE_EDIT_API_KEY.strip())
            if not ai_key_configured:
                st.warning(
                    "⚠️ **AI Image Editing API is not configured.** "
                    "You can still use the local Mode 1 wall recolouring pipeline above with full luminance and texture preservation. "
                    "To enable AI-enhanced previews, set `IMAGE_EDIT_API_KEY` in your `.env` or in the Configuration tab."
                )

            if st.button("✨ Request AI-Enhanced Room Render", disabled=not ai_key_configured):
                with st.spinner("Calling AI Image Editing Provider..."):
                    gen_img, gen_meta = request_ai_enhanced_preview(
                        original_img=original_pil,
                        palette=active_palette,
                        room_type=room_analysis.detected_room_type,
                        interior_style=room_analysis.detected_style
                    )
                    st.session_state.ai_preview_result = (gen_img, gen_meta)

            if st.session_state.ai_preview_result:
                gen_img, gen_meta = st.session_state.ai_preview_result
                if gen_img:
                    st.success(f"Generated via {gen_meta.get('provider', 'AI Provider')}")
                    st.image(gen_img, caption="AI-Generated Architectural Preview", use_container_width=True)
                    st.info(gen_meta.get("notice", "AI-generated visualization."))
                else:
                    st.error(gen_meta.get("message", "AI preview could not be generated."))

        st.markdown("---")

        # Step 11: Export and Download Suite
        st.markdown("## 📦 Export Consultation Suite")
        st.caption("Export full architectural documentation, digital swatches, and color specifications.")

        exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)

        # 1. JSON Export
        with exp_col1:
            json_data = export_palette_json(active_palette, room_analysis=room_analysis)
            st.download_button(
                "📄 Export Palette as JSON",
                data=json_data,
                file_name=f"{active_palette.name.replace(' ', '_').lower()}.json",
                mime="application/json",
                use_container_width=True
            )

        # 2. CSV Export
        with exp_col2:
            csv_data = export_palette_csv(active_palette)
            st.download_button(
                "📊 Export Swatches as CSV",
                data=csv_data,
                file_name=f"{active_palette.name.replace(' ', '_').lower()}_swatches.csv",
                mime="text/csv",
                use_container_width=True
            )

        # 3. Swatch Sheet PNG
        with exp_col3:
            swatch_png = generate_swatch_sheet_png(active_palette, room_type=room_analysis.detected_room_type)
            st.download_button(
                "🖼️ Download Swatch Sheet (PNG)",
                data=swatch_png.getvalue(),
                file_name=f"{active_palette.name.replace(' ', '_').lower()}_swatch_sheet.png",
                mime="image/png",
                use_container_width=True
            )

        # 4. Plaintext Consultation Report
        with exp_col4:
            txt_report = generate_text_report(active_palette, room_analysis, extracted, room_type=room_analysis.detected_room_type)
            st.download_button(
                "📝 Download Design Report (TXT)",
                data=txt_report,
                file_name=f"{active_palette.name.replace(' ', '_').lower()}_report.txt",
                mime="text/plain",
                use_container_width=True
            )


# ====================================================
# TAB 2: SAVED PALETTES & HISTORY
# ====================================================
with tab_saved:
    st.markdown("## 📁 Saved Palettes Collection")
    st.caption("Locally persisted in SQLite (`data/palettes.db`). Metadata and color specifications are preserved.")

    saved_items = list_saved_palettes()

    if not saved_items:
        st.info("No saved palettes in your library yet. Save any palette concept from the Studio tab to view it here.")
    else:
        search_query = st.text_input("🔍 Search Saved Palettes by Name or Style", value="")
        filtered_items = [
            item for item in saved_items
            if search_query.lower() in item["name"].lower()
            or search_query.lower() in item["room_type"].lower()
            or search_query.lower() in item["interior_style"].lower()
        ] if search_query else saved_items

        st.write(f"Showing **{len(filtered_items)}** saved records:")

        for rec in filtered_items:
            pal_dict = rec["palette"]
            pal_obj = PaletteConcept(**pal_dict)

            with st.container():
                st.markdown(
                    f"""
                    <div class="custom-card" style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0; color: #30271F;">{rec['name']}</h4>
                                <span style="font-size: 0.78rem; color: #786B60;">
                                    Saved: {rec['timestamp']} | Room: {rec['room_type']} | Style: {rec['interior_style']}
                                </span>
                            </div>
                            <span class="score-badge">Match: {pal_obj.heuristic_score}%</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Show swatches
                render_palette_swatches_horizontal(pal_obj)

                # Actions for this saved record
                act_col1, act_col2, act_col3 = st.columns([1, 1, 3])
                with act_col1:
                    if st.button("🗑️ Delete", key=f"del_{rec['id']}"):
                        delete_saved_palette(rec['id'])
                        st.success(f"Deleted '{rec['name']}'")
                        st.rerun()

                with act_col2:
                    swatch_buf = generate_swatch_sheet_png(pal_obj, room_type=rec['room_type'])
                    st.download_button(
                        "🖼️ Swatch PNG",
                        data=swatch_buf.getvalue(),
                        file_name=f"{rec['name'].replace(' ', '_').lower()}_swatch.png",
                        mime="image/png",
                        key=f"dl_sw_{rec['id']}"
                    )

                with act_col3:
                    json_str = export_palette_json(pal_obj)
                    st.download_button(
                        "📄 Download JSON",
                        data=json_str,
                        file_name=f"{rec['name'].replace(' ', '_').lower()}.json",
                        mime="application/json",
                        key=f"dl_json_{rec['id']}"
                    )

                st.markdown("<hr style='border: none; border-top: 1px solid #E3D8CB; margin: 16px 0;'>", unsafe_allow_html=True)


# ====================================================
# TAB 3: CONFIGURATION & DESIGN GUIDE
# ====================================================
with tab_settings:
    st.markdown("## ⚙️ Model Configuration & System Health")
    st.caption("Verify API connection status, review local fallback capabilities, and inspect design guidelines.")

    cfg_col1, cfg_col2 = st.columns(2)

    with cfg_col1:
        st.markdown(
            """
            <div class="custom-card">
                <h4 class="card-title">Vision LLM Integration</h4>
                <p style="font-size: 0.85rem; color: #786B60;">
                    Vision models perform semantic scene understanding, detecting furniture materials, flooring tones, and architectural layout strengths.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        vision_active = bool(VISION_API_KEY.strip())
        if vision_active:
            st.success(f"✅ Vision API Key Detected (Model: {VISION_MODEL})")
        else:
            st.info("ℹ️ No VISION_API_KEY detected. The application is running in **Deterministic Local CV Mode** using K-Means clustering and ITU-R BT.709 luminance.")

    with cfg_col2:
        st.markdown(
            """
            <div class="custom-card">
                <h4 class="card-title">AI Image Editing Integration</h4>
                <p style="font-size: 0.85rem; color: #786B60;">
                    Generative models generate alternative room concepts from text and image prompts.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        edit_active = bool(IMAGE_EDIT_API_KEY.strip())
        if edit_active:
            st.success(f"✅ Image Editing Key Detected (Model: {IMAGE_EDIT_MODEL})")
        else:
            st.info("ℹ️ No IMAGE_EDIT_API_KEY detected. The local wall recolouring pipeline (Mode 1) is active with full shading, texture, and edge protection.")

    st.markdown("### Architectural Colour Harmony Guidelines")
    st.markdown(
        """
        - **60-30-10 Rule:** 60% dominant wall plane, 30% secondary millwork/trim/accent wall, 10% decorative accent.
        - **Light Reflectance Value (LRV):** Measures the percentage of light a paint reflects. Deep north-facing rooms benefit from LRV > 65% to avoid feeling cave-like.
        - **Undertones:** Never pair warm pinkish beiges with greenish grays unless connected by an intentional complementary harmony.
        - **Camera White Balance Disclaimer:** Digital cameras automatically shift color temperature. Always verify physical swatches in real room lighting before purchasing paint.
        """
    )
