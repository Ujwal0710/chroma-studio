"""CSS styles and Design System tokens for AI Interior Colour Palette Suggester."""

MAIN_CSS = """
<style>
/* ----------------------------------------------------
   DESIGN SYSTEM: WARM IVORY & ARCHITECTURAL ESPRESSO
---------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&display=swap');

:root {
    --bg-main: #F5F0E8;
    --surface: #FFFCF7;
    --text-primary: #30271F;
    --text-secondary: #786B60;
    --accent-primary: #725640;
    --accent-secondary: #B98468;
    --border-subtle: #E3D8CB;
    --shadow-soft: 0 4px 20px rgba(48, 39, 31, 0.05);
}

/* Overall page background */
.stApp {
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Custom Header banner */
.brand-header {
    background: linear-gradient(135deg, #FFFCF7 0%, #F5F0E8 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 28px;
    box-shadow: var(--shadow-soft);
}

.brand-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 6px 0;
    letter-spacing: -0.5px;
}

.brand-subtitle {
    font-size: 1.0rem;
    color: var(--text-secondary);
    margin: 0;
    font-weight: 400;
}

/* Cards */
.custom-card {
    background-color: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: var(--shadow-soft);
}

.card-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-top: 0;
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 8px;
}

/* Palette Card */
.palette-card {
    background-color: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-soft);
    transition: all 0.2s ease-in-out;
}

.palette-card:hover {
    border-color: var(--accent-secondary);
    box-shadow: 0 6px 24px rgba(48, 39, 31, 0.09);
}

.palette-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}

.palette-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}

.score-badge {
    background-color: #F0E8DD;
    color: var(--accent-primary);
    font-weight: 600;
    font-size: 0.85rem;
    padding: 4px 10px;
    border-radius: 20px;
    border: 1px solid var(--border-subtle);
}

/* Color strip and swatches */
.swatch-strip {
    display: flex;
    border-radius: 8px;
    overflow: hidden;
    height: 72px;
    margin-bottom: 14px;
    border: 1px solid var(--border-subtle);
}

.swatch-segment {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #FFFFFF;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
    transition: flex 0.2s ease;
}

.swatch-segment:hover {
    flex: 1.4;
}

/* Individual Swatch Box */
.swatch-box {
    display: inline-block;
    width: 24px;
    height: 24px;
    border-radius: 4px;
    border: 1px solid rgba(0, 0, 0, 0.15);
    vertical-align: middle;
    margin-right: 8px;
}

/* Metrics and details */
.metric-row {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
}

.metric-pill {
    background: #F7F3EC;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.82rem;
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
}

.metric-pill strong {
    color: var(--text-primary);
}

/* Buttons */
.stButton>button {
    background-color: var(--accent-primary) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--accent-primary) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 8px 18px !important;
    transition: background-color 0.2s ease !important;
}

.stButton>button:hover {
    background-color: #5C4331 !important;
    border-color: #5C4331 !important;
}

/* Streamlit Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--surface);
    border-radius: 8px;
    padding: 4px;
    border: 1px solid var(--border-subtle);
}

.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
}

.stTabs [aria-selected="true"] {
    color: var(--accent-primary) !important;
    font-weight: 700 !important;
    background-color: #F5F0E8 !important;
    border-radius: 6px !important;
}

/* Inputs, Selectboxes, Sliders */
.stSelectbox, .stTextInput, .stMultiSelect {
    color: var(--text-primary) !important;
}

/* Disclaimer text */
.disclaimer-box {
    background-color: #F7F3EC;
    border-left: 3px solid var(--accent-secondary);
    padding: 10px 14px;
    font-size: 0.83rem;
    color: var(--text-secondary);
    margin-top: 10px;
    margin-bottom: 16px;
    border-radius: 0 6px 6px 0;
}
</style>
"""
