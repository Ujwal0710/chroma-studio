"""Reusable UI components for CHROMA STUDIO AI."""
import streamlit as st
from typing import List, Dict, Any, Optional
from PIL import Image

from config.settings import APP_NAME, APP_TAGLINE, SUBSCRIPTION_PLANS
from models.schemas import PaletteConcept, RoomAnalysisResult, ExtractedColorAnalysis, ColorSwatch


def render_header(user: Optional[Dict[str, Any]] = None, subscription: Optional[Dict[str, Any]] = None, usage: Optional[Dict[str, Any]] = None) -> None:
    """Render the architectural design header banner with user and subscription status."""
    plan_name = "Free Plan"
    plan_badge_class = "plan-free"
    usage_info = ""
    
    if subscription:
        plan_id = subscription.get("plan_id", "free")
        plan_name = SUBSCRIPTION_PLANS.get(plan_id, {}).get("name", "Free Plan")
        plan_badge_class = f"plan-{plan_id}"
        
        if usage:
            limit = SUBSCRIPTION_PLANS.get(plan_id, {}).get("monthly_analyses_limit", 3)
            used = usage.get("analyses_used", 0)
            usage_info = f" • Analyses: {used}/{limit}"
    
    user_status_html = ""
    if user:
        user_status_html = f"""
        <div style="text-align: right;">
            <div style="font-size: 0.88rem; font-weight: 600; color: var(--text-primary);">{user.get('full_name', 'Designer')}</div>
            <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 3px;">
                <span class="plan-badge {plan_badge_class}">{plan_name}</span>{usage_info}
            </div>
        </div>
        """
    else:
        user_status_html = """
        <div style="text-align: right;">
            <span class="plan-badge plan-free">Guest Session</span>
        </div>
        """

    st.markdown(
        f"""
        <div class="brand-header">
            <div>
                <h1 class="brand-title">{APP_NAME}</h1>
                <p class="brand-subtitle">{APP_TAGLINE}</p>
            </div>
            {user_status_html}
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

    with st.expander("View Detailed Swatch Analysis & Undertones", expanded=False):
        cols = st.columns(len(extracted.dominant_colors))
        for i, sw in enumerate(extracted.dominant_colors):
            with cols[i]:
                st.markdown(
                    f"""
                    <div style="background-color: {sw.hex}; height: 44px; border-radius: 4px; border: 1px solid var(--border-subtle); margin-bottom: 6px;"></div>
                    <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-primary);">{sw.name}</div>
                    <div style="font-size: 0.74rem; color: var(--text-secondary);">{sw.hex}</div>
                    <div style="font-size: 0.70rem; color: var(--text-secondary);">RGB({sw.rgb[0]},{sw.rgb[1]},{sw.rgb[2]})</div>
                    <div style="font-size: 0.68rem; color: var(--accent-primary); margin-top: 3px;">{sw.temperature.capitalize()} | {sw.saturation_category}</div>
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
            <p style="font-size: 0.9rem; color: var(--text-primary); margin: 8px 0;">
                <strong>Wall Baseline:</strong> {analysis.existing_wall_description}<br>
                <strong>Flooring & Grounding:</strong> {analysis.flooring_description}
            </p>
            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 6px;">
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
        ("Accent Details", palette.accent, palette.proportions.get("Accent Details", "10%")),
        ("Trim & Details", palette.trim, "Detail Trim")
    ]

    for col, (role, sw, prop) in zip(cols, swatches_data):
        with col:
            lum = sw.luminance if sw.luminance is not None else 0.5
            txt_color = "#30271F" if lum > 0.6 else "#FFFFFF"
            st.markdown(
                f"""
                <div style="background-color: var(--surface); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 10px; margin-bottom: 8px;">
                    <div style="background-color: {sw.hex}; height: 60px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); display: flex; align-items: flex-end; justify-content: flex-end; padding: 4px;">
                        <span style="font-size: 0.70rem; font-weight: 700; color: {txt_color};">{prop}</span>
                    </div>
                    <div style="font-size: 0.72rem; font-weight: 700; color: var(--accent-primary); margin-top: 6px; text-transform: uppercase;">{role}</div>
                    <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-primary); margin-top: 2px;">{sw.name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary); font-family: monospace;">{sw.hex}</div>
                    <div style="font-size: 0.70rem; color: var(--text-secondary);">RGB({sw.rgb[0]}, {sw.rgb[1]}, {sw.rgb[2]})</div>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_explainability_card(palette: PaletteConcept, memory_notes: Optional[List[str]] = None, material_notes: Optional[List[str]] = None) -> None:
    """Render transparent confidence, rationale, and explainability breakdown."""
    st.markdown(
        f"""
        <div class="custom-card" style="margin-top: 8px;">
            <h4 style="margin: 0 0 8px 0; font-size: 1.0rem; color: var(--accent-primary);">
                🔍 Palette Explainability & Confidence Metrics
            </h4>
            <div style="font-size: 0.85rem; color: var(--text-primary); line-height: 1.5;">
                <strong>Why this was recommended:</strong> {palette.design_rationale}<br>
                <strong>Furniture & Material Harmony:</strong> {palette.furniture_flooring_compatibility}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if memory_notes or material_notes:
        with st.expander("View Personalization & Material Influence Rationale"):
            if memory_notes:
                st.markdown("**Chroma Memory Signals:**")
                for n in memory_notes:
                    st.caption(f"• {n}")
            if material_notes:
                st.markdown("**Material Synergy Evaluations:**")
                for m in material_notes:
                    st.caption(f"• {m}")
