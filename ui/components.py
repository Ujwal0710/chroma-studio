"""Reusable UI components for AI Interior Colour Palette Suggester."""
import streamlit as st
from typing import List, Dict, Any, Optional
from PIL import Image

from models.schemas import PaletteConcept, RoomAnalysisResult, ExtractedColorAnalysis, ColorSwatch


def render_header() -> None:
    """Render the architectural design header banner."""
    st.markdown(
        """
        <div class="brand-header">
            <h1 class="brand-title">AI Interior Colour Palette Suggester</h1>
            <p class="brand-subtitle">
                Architectural colour science, computer vision extraction, and AI-curated palettes for harmonious interiors.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_dominant_color_strip(extracted: ExtractedColorAnalysis) -> None:
    """Render dominant color palette strip with proportion bars and details."""
    st.markdown("### Extracted Room Dominant Colours")
    st.caption(
        f"K-Means clustering extracted from room photograph | "
        f"Ambient lighting: **{extracted.overall_temperature_tendency.capitalize()}** tendency | "
        f"Average brightness: **{extracted.overall_brightness:.1%}**"
    )

    # HTML Swatch Strip
    segments_html = []
    for sw in extracted.dominant_colors:
        # Text color based on luminance
        lum = sw.luminance if sw.luminance is not None else 0.5
        txt_color = "#30271F" if lum > 0.6 else "#FFFFFF"
        segments_html.append(
            f'<div class="swatch-segment" style="background-color: {sw.hex}; color: {txt_color}; flex: {max(0.4, (sw.percentage or 10.0) / 10.0)};">'
            f'<span>{sw.percentage}%</span>'
            f'<span>{sw.hex}</span>'
            f'</div>'
        )

    strip_html = f'<div class="swatch-strip">{"".join(segments_html)}</div>'
    st.markdown(strip_html, unsafe_allow_html=True)

    # Expanded details in columns
    with st.expander("View Detailed Swatch Analysis & Undertones", expanded=False):
        cols = st.columns(len(extracted.dominant_colors))
        for i, sw in enumerate(extracted.dominant_colors):
            with cols[i]:
                st.markdown(
                    f"""
                    <div style="background-color: {sw.hex}; height: 44px; border-radius: 4px; border: 1px solid #E3D8CB; margin-bottom: 6px;"></div>
                    <div style="font-size: 0.78rem; font-weight: 700; color: #30271F;">{sw.name}</div>
                    <div style="font-size: 0.74rem; color: #786B60;">{sw.hex}</div>
                    <div style="font-size: 0.70rem; color: #786B60;">RGB({sw.rgb[0]},{sw.rgb[1]},{sw.rgb[2]})</div>
                    <div style="font-size: 0.68rem; color: #725640; margin-top: 3px;">{sw.temperature.capitalize()} | {sw.saturation_category}</div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown(
            f'<div class="disclaimer-box">{extracted.analysis_disclaimer}</div>',
            unsafe_allow_html=True
        )


def render_room_analysis_card(analysis: RoomAnalysisResult) -> None:
    """Render room architectural analysis details."""
    provider_badge_color = "#4A6B53" if analysis.is_ai_inferred else "#725640"
    st.markdown(
        f"""
        <div class="custom-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 class="card-title" style="margin: 0; border: none; padding: 0;">Architectural Room Analysis</h3>
                <span style="background-color: {provider_badge_color}; color: #FFFFFF; font-size: 0.75rem; padding: 3px 9px; border-radius: 12px; font-weight: 600;">
                    {analysis.provider_name}
                </span>
            </div>
            <div class="metric-row">
                <div class="metric-pill">Room Type: <strong>{analysis.detected_room_type}</strong></div>
                <div class="metric-pill">Interior Style: <strong>{analysis.detected_style}</strong></div>
                <div class="metric-pill">Lighting: <strong>{analysis.apparent_lighting}</strong></div>
            </div>
            <p style="font-size: 0.9rem; color: #30271F; margin: 8px 0;">
                <strong>Wall Baseline:</strong> {analysis.existing_wall_description}<br>
                <strong>Flooring & Grounding:</strong> {analysis.flooring_description}
            </p>
            <div style="font-size: 0.85rem; color: #786B60; margin-top: 6px;">
                <strong>Architectural Recommendation:</strong> {analysis.recommended_direction}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_palette_swatches_horizontal(palette: PaletteConcept) -> None:
    """Render 4 swatches with role, name, hex, and proportions."""
    cols = st.columns(4)
    swatches_data = [
        ("Primary Wall", palette.primary_wall, palette.proportions.get("Primary Wall", "60%")),
        ("Secondary Wall", palette.secondary_wall, palette.proportions.get("Secondary Wall / Trim", "30%")),
        ("Accent Details", palette.accent, palette.proportions.get("Accent Accents", "10%")),
        ("Trim & Ceiling", palette.trim, "Detail Trim")
    ]

    for col, (role, sw, prop) in zip(cols, swatches_data):
        with col:
            lum = sw.luminance if sw.luminance is not None else 0.5
            txt_color = "#30271F" if lum > 0.6 else "#FFFFFF"
            st.markdown(
                f"""
                <div style="background-color: #FFFCF7; border: 1px solid #E3D8CB; border-radius: 8px; padding: 10px; margin-bottom: 8px;">
                    <div style="background-color: {sw.hex}; height: 60px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); display: flex; align-items: flex-end; justify-content: flex-end; padding: 4px;">
                        <span style="font-size: 0.70rem; font-weight: 700; color: {txt_color};">{prop}</span>
                    </div>
                    <div style="font-size: 0.72rem; font-weight: 700; color: #725640; margin-top: 6px; text-transform: uppercase;">{role}</div>
                    <div style="font-size: 0.82rem; font-weight: 600; color: #30271F; margin-top: 2px;">{sw.name}</div>
                    <div style="font-size: 0.75rem; color: #786B60; font-family: monospace;">{sw.hex}</div>
                    <div style="font-size: 0.70rem; color: #786B60;">RGB({sw.rgb[0]}, {sw.rgb[1]}, {sw.rgb[2]})</div>
                </div>
                """,
                unsafe_allow_html=True
            )
