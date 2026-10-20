"""CSS styles and Design System tokens for CHROMA STUDIO AI."""
from typing import Dict, Any
from config.settings import LIGHT_THEME_TOKENS, DARK_THEME_TOKENS, APP_NAME, APP_TAGLINE


def get_theme_css(theme: str = "light") -> str:
    """Generate dynamic CSS injected into Streamlit supporting light and dark themes."""
    tokens = DARK_THEME_TOKENS if theme == "dark" else LIGHT_THEME_TOKENS
    is_dark = (theme == "dark")
    
    card_bg = tokens["surface"]
    main_bg = tokens["background"]
    text_primary = tokens["primary_text"]
    text_secondary = tokens["secondary_text"]
    accent_primary = tokens["primary_accent"]
    accent_secondary = tokens["secondary_accent"]
    border_subtle = tokens["subtle_border"]
    
    return f"""
<style>
/* ----------------------------------------------------
   CHROMA STUDIO AI: EDITORIAL DESIGN SYSTEM
   Theme: {theme.upper()}
---------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&display=swap');

:root {{
    --bg-main: {main_bg};
    --surface: {card_bg};
    --text-primary: {text_primary};
    --text-secondary: {text_secondary};
    --accent-primary: {accent_primary};
    --accent-secondary: {accent_secondary};
    --border-subtle: {border_subtle};
    --shadow-soft: {'0 4px 20px rgba(0, 0, 0, 0.35)' if is_dark else '0 4px 20px rgba(48, 39, 31, 0.05)'};
    --shadow-hover: {'0 8px 30px rgba(0, 0, 0, 0.5)' if is_dark else '0 8px 28px rgba(48, 39, 31, 0.12)'};
}}

/* Overall page background */
.stApp {{
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

/* Custom Header banner */
.brand-header {{
    background: {'linear-gradient(135deg, #222520 0%, #171916 100%)' if is_dark else 'linear-gradient(135deg, #FFFCF7 0%, #F5F0E8 100%)'};
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-soft);
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.3s ease;
}}

.brand-title {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.15rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 4px 0;
    letter-spacing: -0.5px;
}}

.brand-subtitle {{
    font-size: 0.96rem;
    color: var(--text-secondary);
    margin: 0;
    font-weight: 400;
}}

/* Cards with smooth hover elevation */
.custom-card {{
    background-color: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: var(--shadow-soft);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}}

.custom-card:hover {{
    box-shadow: var(--shadow-hover);
    border-color: var(--accent-secondary);
}}

.card-title {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-top: 0;
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 8px;
}}

/* Palette Card */
.palette-card {{
    background-color: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-soft);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}}

.palette-card:hover {{
    transform: translateY(-2px);
    border-color: var(--accent-secondary);
    box-shadow: var(--shadow-hover);
}}

.palette-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}}

.palette-title {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}}

.score-badge {{
    background-color: {'#2A2E27' if is_dark else '#F0E8DD'};
    color: var(--accent-primary);
    font-weight: 600;
    font-size: 0.85rem;
    padding: 4px 12px;
    border-radius: 20px;
    border: 1px solid var(--border-subtle);
}}

/* Color strip and animated swatches */
.swatch-strip {{
    display: flex;
    border-radius: 8px;
    overflow: hidden;
    height: 74px;
    margin-bottom: 14px;
    border: 1px solid var(--border-subtle);
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}}

.swatch-segment {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #FFFFFF;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7);
    transition: flex 0.25s cubic-bezier(0.16, 1, 0.3, 1), filter 0.2s ease;
    cursor: default;
}}

.swatch-segment:hover {{
    flex: 1.45;
    filter: brightness(1.08);
}}

/* Individual Swatch Box */
.swatch-box {{
    display: inline-block;
    width: 24px;
    height: 24px;
    border-radius: 4px;
    border: 1px solid rgba(0, 0, 0, 0.15);
    vertical-align: middle;
    margin-right: 8px;
}}

/* Metric pills */
.metric-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 14px;
}}

.metric-pill {{
    background: {'#1D201C' if is_dark else '#F7F3EC'};
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.82rem;
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
}}

.metric-pill strong {{
    color: var(--text-primary);
}}

/* Plan Badge */
.plan-badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.plan-free {{ background: {'#2A2E27' if is_dark else '#E8E3D8'}; color: var(--text-secondary); }}
.plan-plus {{ background: {'#3E3224' if is_dark else '#FBEBD9'}; color: var(--accent-secondary); }}
.plan-pro {{ background: {'#362B21' if is_dark else '#EADCCF'}; color: var(--accent-primary); }}

/* Primary & Action Buttons */
.stButton>button {{
    background-color: var(--accent-primary) !important;
    color: {'#171916' if is_dark else '#FFFFFF'} !important;
    border: 1px solid var(--accent-primary) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 8px 18px !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}

.stButton>button:hover {{
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}}

/* Secondary Action / Outline Buttons */
.secondary-btn>button {{
    background-color: transparent !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
}}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {{
    background-color: var(--surface);
    border-radius: 8px;
    padding: 4px;
    border: 1px solid var(--border-subtle);
}}

.stTabs [data-baseweb="tab"] {{
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
}}

.stTabs [aria-selected="true"] {{
    color: var(--accent-primary) !important;
    font-weight: 700 !important;
    background-color: var(--bg-main) !important;
    border-radius: 6px !important;
}}

/* Disclaimers & Notes */
.disclaimer-box {{
    background-color: {'#1D201C' if is_dark else '#F7F3EC'};
    border-left: 3px solid var(--accent-secondary);
    padding: 10px 14px;
    font-size: 0.83rem;
    color: var(--text-secondary);
    margin-top: 10px;
    margin-bottom: 16px;
    border-radius: 0 6px 6px 0;
}}

/* Subtle pulse animation for analysis */
@keyframes subtle-pulse {{
    0% {{ opacity: 0.95; }}
    50% {{ opacity: 0.65; }}
    100% {{ opacity: 0.95; }}
}}
.loading-skeleton {{
    background: linear-gradient(90deg, var(--surface) 25%, var(--border-subtle) 50%, var(--surface) 75%);
    background-size: 200% 100%;
    animation: subtle-pulse 1.8s infinite;
    border-radius: 8px;
    height: 120px;
    margin-bottom: 16px;
}}
</style>
"""


MAIN_CSS = get_theme_css("light")
