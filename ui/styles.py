"""Chroma Studio AI Unified Editorial Design System & Styling Engine (Dark-Only).

Visual Identity:
- Deep Obsidian & Smoked Charcoal surfaces (#121411 / #1B1E19 / #222520)
- Warm Ivory typography (#F4F1EA / #B0AEA5) with WCAG AA compliance
- Warm Terracotta & Amber accents (#B85C38 / #A68668)
- Editorial Typography: Playfair Display + Plus Jakarta Sans + Space Grotesk
- Full elimination of sidebar, centered 1200px max-width layout
"""

CHROMA_DARK_TOKENS = {
    "background": "#121411",        # Deep Obsidian Canvas
    "surface": "#1B1E19",           # Architectural Charcoal Panel
    "surface_subtle": "#242822",    # Smoked Granite Layer
    "surface_raised": "#2D322B",    # Elevated Surface
    "primary_text": "#F4F1EA",      # Warm Ivory (AAA Contrast ~14.5:1)
    "secondary_text": "#B0AEA5",    # Warm Taupe Sand (AA Contrast ~6.8:1)
    "muted_text": "#828076",        # Ash Mineral
    "primary_accent": "#B85C38",    # Warm Terracotta Amber
    "secondary_accent": "#A68668",  # Aged Oak
    "botanical_sage": "#5B8565",    # Forest Sage
    "subtle_border": "#2E332B",     # Muted Obsidian Border
    "hairline": "rgba(244, 241, 234, 0.08)",
    "success": "#5B8565",
    "warning": "#D49359",
    "danger": "#C45B5B",
    "badge_bg": "#242822"
}

# Backwards compatibility aliases
CHROMA_LIGHT_TOKENS = CHROMA_DARK_TOKENS
ROOMIE_LIGHT_TOKENS = CHROMA_DARK_TOKENS
ROOMIE_DARK_TOKENS = CHROMA_DARK_TOKENS
LIGHT_THEME_TOKENS = CHROMA_DARK_TOKENS
DARK_THEME_TOKENS = CHROMA_DARK_TOKENS
DESIGN_TOKENS = CHROMA_DARK_TOKENS


def get_theme_css(theme: str = "dark") -> str:
    """Generate dynamic CSS injected into Streamlit embodying the dark-only editorial design system."""
    tokens = CHROMA_DARK_TOKENS

    return f"""
<style>
/* --------------------------------------------------------------------------
   CHROMA STUDIO AI — DARK-ONLY ARCHITECTURAL DESIGN SYSTEM (1200px Centered)
-------------------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {{
    --bg-main: {tokens["background"]};
    --surface: {tokens["surface"]};
    --surface-subtle: {tokens["surface_subtle"]};
    --surface-raised: {tokens["surface_raised"]};
    --text-primary: {tokens["primary_text"]};
    --text-secondary: {tokens["secondary_text"]};
    --text-muted: {tokens["muted_text"]};
    --accent-primary: {tokens["primary_accent"]};
    --accent-secondary: {tokens["secondary_accent"]};
    --border-subtle: {tokens["subtle_border"]};
    --hairline: {tokens["hairline"]};
    --badge-bg: {tokens["badge_bg"]};
    --radius-container: 20px;
    --radius-card: 14px;
    --radius-btn: 8px;
    --radius-pill: 999px;
    --shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.25);
    --shadow-hover: 0 12px 30px rgba(0, 0, 0, 0.40);
}}

/* Phase 1: Permanently hide left sidebar and all collapse triggers */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
section[data-testid="stSidebar"] {{
    display: none !important;
    width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    visibility: hidden !important;
}}

/* Centered Main Area — Max Width 1200px */
.block-container {{
    max-width: 1200px !important;
    padding-top: 1.2rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    margin-left: auto !important;
    margin-right: auto !important;
}}

/* Base Canvas */
.stApp {{
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    letter-spacing: -0.01em;
}}

/* Typography Hierarchy */
h1, h2, h3 {{
    font-family: 'Playfair Display', Georgia, serif !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}}

h4, h5, h6 {{
    font-family: 'Space Grotesk', 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}}

p, span, label, li {{
    color: var(--text-primary);
}}

/* Top Architectural Header */
.chroma-top-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 24px;
    background: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-card);
    margin-bottom: 20px;
    box-shadow: var(--shadow-soft);
}}

.chroma-brand {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: baseline;
    gap: 8px;
}}

.chroma-brand span {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.70rem;
    font-weight: 800;
    color: var(--accent-primary);
    text-transform: uppercase;
    letter-spacing: 0.14em;
}}

.chroma-header-meta {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

/* Reusable Architectural Card & 3D Interactive Elevation */
.custom-card, .card-3d {{
    background-color: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-card);
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.28);
    transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.28s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.28s ease;
    position: relative;
    overflow: hidden;
}}

.custom-card::before, .card-3d::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, rgba(244,241,234,0) 0%, rgba(244,241,234,0.18) 50%, rgba(244,241,234,0) 100%);
    pointer-events: none;
}}

.custom-card:hover, .card-3d:hover {{
    transform: translateY(-3px) perspective(1000px) rotateX(1.2deg);
    box-shadow: 0 14px 34px rgba(0, 0, 0, 0.45);
    border-color: rgba(184, 92, 56, 0.45);
}}

/* Tactile 3D Physical Swatch Chip */
.swatch-chip-3d {{
    border-radius: 10px;
    box-shadow: 0 6px 14px rgba(0, 0, 0, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.25), inset 0 -2px 3px rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
}}

.swatch-chip-3d:hover {{
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.45), inset 0 1px 2px rgba(255, 255, 255, 0.35);
}}

/* 3D Volumetric 60-30-10 Swatch Strip */
.swatch-strip, .swatch-strip-3d {{
    display: flex;
    border-radius: 12px;
    overflow: hidden;
    height: 60px;
    margin-bottom: 16px;
    border: 1px solid var(--border-subtle);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.30);
}}

.swatch-segment {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 6px 12px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    transition: flex 0.25s ease, filter 0.2s ease;
    position: relative;
}}

.swatch-segment:hover {{
    filter: brightness(1.1);
}}

.swatch-segment::after {{
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    width: 1px;
    height: 100%;
    background: rgba(0, 0, 0, 0.25);
}}

/* Badges & Metric Pills */
.score-badge {{
    background-color: var(--badge-bg);
    color: var(--text-primary);
    font-weight: 600;
    font-size: 0.80rem;
    padding: 4px 12px;
    border-radius: var(--radius-pill);
    border: 1px solid var(--border-subtle);
    font-family: 'Space Grotesk', monospace;
}}

.metric-pill {{
    background: var(--surface-subtle);
    padding: 6px 14px;
    border-radius: var(--radius-pill);
    font-size: 0.80rem;
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
    display: inline-flex;
    align-items: center;
    gap: 6px;
}}

.metric-pill strong {{
    color: var(--text-primary);
    font-weight: 700;
}}

/* Plan Badges */
.plan-badge {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: var(--radius-pill);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}

.plan-free {{ background: #242E26; color: #78B085; border: 1px solid #3B5E43; }}
.plan-plus {{ background: #352820; color: #DDA384; border: 1px solid #B85C38; }}
.plan-pro {{ background: #2E2822; color: #E0C09E; border: 1px solid #A68668; }}

/* 3D Elevated Buttons */
.stButton>button {{
    background-color: var(--accent-primary) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--accent-primary) !important;
    border-radius: var(--radius-btn) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.02em !important;
    padding: 10px 22px !important;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
}}

.stButton>button:hover {{
    background-color: #D47B57 !important;
    border-color: #D47B57 !important;
    color: #FFFFFF !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(184, 92, 56, 0.40) !important;
}}

.stButton>button:active {{
    transform: translateY(1px) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
}}

/* Secondary / Outline Buttons */
.stButton>button[kind="secondary"] {{
    background-color: var(--surface-subtle) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
}}

.stButton>button[kind="secondary"]:hover {{
    border-color: var(--accent-primary) !important;
    background-color: var(--surface-raised) !important;
}}

/* Pure Dark Mode Surfaces for Native Streamlit Widgets (No light surfaces anywhere) */
.stSelectbox>div>div, 
.stTextInput>div>div, 
.stNumberInput>div>div, 
.stTextArea>div>div, 
.stDateInput>div>div {{
    background-color: var(--surface) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-subtle) !important;
    border-radius: 8px !important;
}}

/* Expanders */
.streamlit-expanderHeader, 
details>summary {{
    background-color: var(--surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}

.streamlit-expanderContent, 
details[open]>div {{
    background-color: var(--surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-top: none !important;
    border-bottom-left-radius: 10px !important;
    border-bottom-right-radius: 10px !important;
}}

/* Streamlit Tabs Navigation */
.stTabs [data-baseweb="tab-list"] {{
    background-color: var(--surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-card) !important;
    padding: 6px 12px !important;
    gap: 8px !important;
    margin-bottom: 24px !important;
}}

.stTabs [data-baseweb="tab"] {{
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 10px 16px !important;
    border: none !important;
    border-radius: 8px !important;
    background: transparent !important;
    transition: all 0.18s ease !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
    color: var(--text-primary) !important;
    background: var(--surface-subtle) !important;
}}

.stTabs [aria-selected="true"] {{
    color: #FFFFFF !important;
    font-weight: 700 !important;
    background: var(--accent-primary) !important;
    border-bottom: none !important;
    box-shadow: 0 4px 12px rgba(184, 92, 56, 0.35) !important;
}}

/* File Uploader */
[data-testid="stFileUploadDropzone"] {{
    background-color: var(--surface) !important;
    border: 2px dashed var(--border-subtle) !important;
    border-radius: var(--radius-card) !important;
    padding: 24px !important;
}}

[data-testid="stFileUploadDropzone"]:hover {{
    border-color: var(--accent-primary) !important;
    background-color: var(--surface-subtle) !important;
}}

/* Sliders */
.stSlider [data-baseweb="slider"] {{
    color: var(--accent-primary) !important;
}}

/* Hairline Divider */
.chroma-hairline {{
    height: 1px;
    background-color: var(--border-subtle);
    margin: 24px 0;
    width: 100%;
}}

/* AI Privacy Shield Card */
.privacy-shield-hero {{
    background: linear-gradient(135deg, var(--surface) 0%, var(--surface-subtle) 100%);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-card);
    padding: 26px;
    margin-bottom: 22px;
}}

.privacy-badge-icon {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background-color: var(--surface-raised);
    border: 1px solid var(--border-subtle);
    font-size: 1.4rem;
    margin-bottom: 12px;
}}

/* Clean Disclaimer Box */
.disclaimer-box {{
    background-color: var(--surface-subtle);
    border-left: 3px solid var(--accent-primary);
    padding: 12px 16px;
    font-size: 0.82rem;
    color: var(--text-secondary);
    border-radius: 4px;
    margin-top: 14px;
    margin-bottom: 16px;
}}
</style>
"""

MAIN_CSS = get_theme_css("dark")
