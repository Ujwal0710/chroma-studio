"""Reusable UI components for Chroma Studio AI Editorial & 3D Architectural Design aesthetic."""
import streamlit as st
from typing import List, Dict, Any, Optional

try:
    from config.settings import SUBSCRIPTION_PLANS, APP_NAME
except ImportError:
    import config.settings as _settings
    SUBSCRIPTION_PLANS = getattr(_settings, "SUBSCRIPTION_PLANS", {})
    APP_NAME = "CHROMA STUDIO AI"

from models.schemas import PaletteConcept, RoomAnalysisResult, ExtractedColorAnalysis
from modules.room_3d import render_interactive_3d_room


def render_header(
    user: Optional[Dict[str, Any]] = None,
    subscription: Optional[Dict[str, Any]] = None,
    usage: Optional[Dict[str, Any]] = None,
    active_workspace: str = "Studio"
) -> None:
    """Render the top architectural navigation bar embodying the unified Chroma Studio AI design system."""
    plan_name = subscription.get("plan_details", {}).get("name", "Free Atelier") if subscription else "Free Atelier"
    user_label = user.get("full_name", "Guest Designer") if user else "Guest Designer"
    user_email = user.get("email", "Local CV Mode") if user else "Local Session (Offline CV)"

    # Plan badge style
    badge_cls = "plan-free"
    if "Plus" in plan_name:
        badge_cls = "plan-plus"
    elif "Pro" in plan_name:
        badge_cls = "plan-pro"

    c_logo, c_account = st.columns([3, 1.8], vertical_alignment="center")
    with c_logo:
        st.markdown(
            """
            <div style="display:flex; align-items:baseline; gap:12px; padding:6px 0;">
                <span style="font-family:'Playfair Display', Georgia, serif; font-size:1.65rem; font-weight:800; color:#F4F1EA; letter-spacing:0.04em;">
                    CHROMA <span style="color:#B85C38;">STUDIO</span> AI
                </span>
                <span style="font-size:0.70rem; font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#8C827A; border-left:1px solid rgba(255,255,255,0.14); padding-left:10px;">
                    Architectural Intelligence
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c_account:
        with st.popover(f"👤 {user_label} • {plan_name}", use_container_width=True):
            st.markdown(f"**{user_label}**")
            st.caption(f"Account: `{user_email}`")
            st.markdown(f"Tier: <span class='plan-badge {badge_cls}'>{plan_name}</span>", unsafe_allow_html=True)
            st.markdown("---")
            if user:
                if st.button("🚪 Sign Out", key="header_sign_out_popover_btn", use_container_width=True):
                    st.session_state.current_user = None
                    st.rerun()
            else:
                st.caption("Guest session: All local computer vision algorithms and offline models active.")


# Alias for backward compatibility
def render_roomie_navigation(active_tab: str = "palettes", user: Optional[Dict[str, Any]] = None, saved_count: int = 0) -> None:
    render_header(user=user)


def render_dominant_color_strip(extracted: ExtractedColorAnalysis) -> None:
    """Render dominant color palette strip in tactile 3D architectural styling."""
    st.markdown(
        """
        <div style="margin-top: 14px; margin-bottom: 8px;">
            <div style="font-size: 0.76rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-secondary);">
                Extracted Room Tones • Perceptual K-Means
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3D HTML Swatch Strip
    segments_html = []
    for sw in extracted.dominant_colors:
        lum = sw.luminance if sw.luminance is not None else 0.5
        txt_color = "#171916" if lum > 0.6 else "#FFFFFF"
        segments_html.append(
            f'<div class="swatch-segment" style="background-color: {sw.hex}; color: {txt_color}; flex: {max(0.4, (sw.percentage or 10.0) / 10.0)};">'
            f'<span style="font-weight: 800; font-size: 0.74rem;">{sw.percentage}%</span>'
            f'<span style="font-family: monospace; font-size: 0.70rem;">{sw.hex.upper()}</span>'
            f'</div>'
        )

    strip_html = f'<div class="swatch-strip-3d">{"".join(segments_html)}</div>'
    st.markdown(strip_html, unsafe_allow_html=True)

    with st.expander("🔍 View Detailed Swatch Coordinates & Optical Metrics", expanded=False):
        cols = st.columns(len(extracted.dominant_colors))
        for i, sw in enumerate(extracted.dominant_colors):
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="swatch-chip-3d" style="background-color: {sw.hex}; height: 46px; margin-bottom: 8px;"></div>
                    <div style="font-size: 0.80rem; font-weight: 700; color: var(--text-primary);">{sw.name}</div>
                    <div style="font-size: 0.74rem; color: var(--accent-primary); font-family: 'Space Grotesk', monospace; font-weight: 600;">{sw.hex.upper()}</div>
                    <div style="font-size: 0.70rem; color: var(--text-muted);">RGB({sw.rgb[0]},{sw.rgb[1]},{sw.rgb[2]})</div>
                    <div style="font-size: 0.68rem; color: var(--text-secondary); margin-top: 4px;">{sw.temperature} • {sw.saturation_category}</div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown(
            f'<div class="disclaimer-box">{extracted.analysis_disclaimer}</div>',
            unsafe_allow_html=True
        )


def render_room_analysis_card(analysis: RoomAnalysisResult) -> None:
    """Render room architectural analysis details in clean editorial card with 3D depth."""
    st.markdown(
        f"""
        <div class="custom-card card-3d">
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px;">
                <h3 class="card-title">Architectural Room Analysis</h3>
                <span class="score-badge">Engine: {analysis.provider_name}</span>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;">
                <div class="metric-pill">Typology: <strong>{analysis.detected_room_type}</strong></div>
                <div class="metric-pill">Style: <strong>{analysis.detected_style}</strong></div>
                <div class="metric-pill">Lighting: <strong>{analysis.apparent_lighting}</strong></div>
            </div>
            <p style="font-size: 0.90rem; color: var(--text-secondary); line-height: 1.6; margin: 8px 0;">
                <strong style="color: var(--text-primary);">Wall Plane Base:</strong> {analysis.existing_wall_description}<br>
                <strong style="color: var(--text-primary);">Flooring Surface:</strong> {analysis.flooring_description}
            </p>
            <div style="font-size: 0.86rem; color: var(--text-secondary); margin-top: 10px; line-height: 1.5; padding-top: 10px; border-top: 1px solid var(--border-subtle);">
                <strong style="color: var(--accent-primary);">Harmonization Recommendation:</strong> {analysis.recommended_direction}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_palette_swatches_horizontal(palette: PaletteConcept) -> None:
    """Render 4 tactile 3D physical swatches with role, name, hex, and proportions."""
    cols = st.columns(4)
    swatches_data = [
        ("Primary Wall", palette.primary_wall, palette.proportions.get("Primary Wall", "60%")),
        ("Secondary Surface", palette.secondary_wall, palette.proportions.get("Secondary Wall / Trim", "30%")),
        ("Accent Details", palette.accent, palette.proportions.get("Accent Details", "10%")),
        ("Trim & Molding", palette.trim, "Detail Anchor")
    ]

    for col, (role, sw, prop) in zip(cols, swatches_data):
        with col:
            lum = sw.luminance if sw.luminance is not None else 0.5
            txt_color = "#171916" if lum > 0.6 else "#FFFFFF"
            st.markdown(
                f"""
                <div class="custom-card card-3d" style="padding: 14px; margin-bottom: 10px;">
                    <div class="swatch-chip-3d" style="background-color: {sw.hex}; height: 72px; display: flex; align-items: flex-end; justify-content: flex-end; padding: 8px; margin-bottom: 10px;">
                        <span style="font-size: 0.72rem; font-weight: 800; color: {txt_color}; background: rgba(0,0,0,0.18); padding: 2px 6px; border-radius: 4px;">{prop}</span>
                    </div>
                    <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">{role}</div>
                    <div style="font-size: 0.90rem; font-weight: 700; color: var(--text-primary); margin-top: 2px;">{sw.name}</div>
                    <div style="font-size: 0.78rem; color: var(--accent-primary); font-family: 'Space Grotesk', monospace; font-weight: 600;">{sw.hex.upper()}</div>
                    <div style="font-size: 0.72rem; color: var(--text-muted);">RGB({sw.rgb[0]}, {sw.rgb[1]}, {sw.rgb[2]})</div>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_explainability_card(palette: PaletteConcept, memory_notes: Optional[List[str]] = None, material_notes: Optional[List[str]] = None) -> None:
    """Render transparent confidence, rationale, and explainability breakdown."""
    st.markdown(
        f"""
        <div class="custom-card card-3d" style="margin-top: 12px;">
            <div style="font-size: 0.76rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent-secondary); margin-bottom: 6px;">
                Palette Rationale &amp; Material Harmony
            </div>
            <div style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6;">
                <strong style="color: var(--text-primary);">Design Rationale:</strong> {palette.design_rationale}<br>
                <strong style="color: var(--text-primary);">Material Harmony:</strong> {palette.furniture_flooring_compatibility}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if memory_notes or material_notes:
        with st.expander("🧠 View Personalization & Material Influence Rationale"):
            if memory_notes:
                st.markdown("**Chroma Memory Signals:**")
                for n in memory_notes:
                    st.caption(f"• {n}")
            if material_notes:
                st.markdown("**Material Synergy Evaluations:**")
                for m in material_notes:
                    st.caption(f"• {m}")


def render_privacy_shield_banner() -> None:
    """Render the AI Privacy Shield hero banner detailing zero data retention & local execution."""
    st.markdown(
        """
        <div class="privacy-shield-hero card-3d">
            <div style="display: flex; align-items: flex-start; gap: 20px;">
                <div class="privacy-badge-icon">🛡️</div>
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                        <h3 style="margin: 0; font-family: 'Playfair Display', Georgia, serif; color: var(--text-primary);">
                            AI Privacy Shield Active
                        </h3>
                        <span class="score-badge" style="background-color: #E8ECE9; color: #3B5E43; font-weight: 700;">
                            Zero External Frame Retention
                        </span>
                    </div>
                    <p style="font-size: 0.90rem; color: var(--text-secondary); line-height: 1.6; margin: 4px 0 12px 0;">
                        All live camera streaming, room element segmentation, and color scanning execute <strong>strictly locally</strong> in-memory.
                        Camera video frames are never transmitted to third parties, never used for AI model training, and never stored on disk without your explicit click on Snapshot.
                    </p>
                    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                        <div class="metric-pill">🔒 <strong>Local CV Engine:</strong> Bilateral &amp; K-Means In-Memory</div>
                        <div class="metric-pill">🗑️ <strong>Ephemeral Stream:</strong> Discarded on turn</div>
                        <div class="metric-pill">🇪🇺 <strong>GDPR Compliant:</strong> Cascading Account Deletion</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_paint_brand_match_card(match: Dict[str, Any]) -> None:
    """Render a matched Indian paint brand shade card with Delta E metric and confidence."""
    st.markdown(
        f"""
        <div class="custom-card card-3d" style="padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; gap: 14px; align-items: center;">
                <div class="swatch-chip-3d" style="width: 56px; height: 56px; background-color: {match['hex']}; flex-shrink: 0;"></div>
                <div style="flex: 1;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <strong style="font-size: 0.98rem; color: var(--text-primary);">{match['brand']} — {match['shade_name']}</strong>
                        <span class="score-badge" style="color: var(--accent-primary);">Match: {match['match_confidence']}%</span>
                    </div>
                    <div style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 2px;">
                        Code: <code>{match['shade_code']}</code> • Finish: <strong>{match['finish']}</strong> • 
                        Est: <strong>₹{match['cost_per_liter_inr']:.0f}/L</strong>
                    </div>
                    <div style="font-size: 0.76rem; color: var(--text-muted); margin-top: 4px;">
                        CIELAB ΔE: <strong>{match['delta_e']}</strong> • {match['sub_brand']}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_3d_room_preview_card(
    palette: PaletteConcept,
    room_type: str = "Living Room",
    theme: str = "light",
    height: int = 580
) -> None:
    """Render the Three.js interactive 3D room canvas inside an architectural card."""
    render_interactive_3d_room(
        primary_wall_hex=palette.primary_wall.hex,
        secondary_wall_hex=palette.secondary_wall.hex,
        accent_hex=palette.accent.hex,
        trim_hex=palette.trim.hex,
        room_type=room_type,
        theme=theme,
        height=height
    )
