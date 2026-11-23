# CHROMA STUDIO AI — UI/UX REDESIGN LOG

**Date:** 2026-11-22  
**Design Lead:** Senior UI/UX Designer & Frontend Architect  
**Design Language:** Editorial Architectural Minimalist  
**Status:** Complete & Integrated across all 21 Application Workspaces  

---

## 1. Design Vision & Philosophy

CHROMA STUDIO AI bridges high-performance computer vision with the tactile elegance of high-end architectural publications (such as *Architectural Digest*, *Kinfolk*, and *El Croquis*).

Rather than generic software SaaS aesthetics (e.g., standard Bootstrap blues or dark neon cyberpunk gradients), the interface uses:
- **Warm limestone and natural ivory canvases** that evoke physical plaster, linen, and travertine.
- **Editorial typography** pairing classical serif headlines with ultra-clean modernist geometric sans-serif text.
- **Subtle hairline dividers and architectural grid layouts** instead of heavy drop-shadows and loud borders.
- **Strict tonal legibility** with AAA contrast compliance for architectural color evaluation.

---

## 2. Centralized Design Token System (`ui/styles.py`)

All visual styling is governed by CSS variables dynamically injected according to the active theme mode (`light` vs. `dark`):

### Light Mode (Warm Ivory & Alabaster)
```css
:root {
  --bg-app: #F5F0E8;            /* Warm French Ivory */
  --surface: #FFFCF7;           /* Matte Alabaster Ceramic */
  --surface-raised: #FFFFFF;    /* Pure White for Elevated Cards */
  --text-primary: #171916;      /* Deep Obsidian Charcoal */
  --text-secondary: #575953;    /* Muted Slate / Wet Sand */
  --text-muted: #878882;        /* Ash Greige */
  --accent-primary: #B85C38;    /* Sandalwood Terracotta */
  --accent-secondary: #725640;  /* Aged Walnut */
  --accent-olive: #3B5E43;      /* Tuscan Sage / Olive */
  --border-subtle: #E6E0D5;     /* Raw Canvas Line */
  --border-focus: #B85C38;      /* Terracotta Accent */
  --shadow-sm: 0 1px 3px rgba(32, 28, 24, 0.04);
  --shadow-md: 0 4px 14px rgba(32, 28, 24, 0.07);
}
```

### Dark Mode (Obsidian Gallery & Smoked Charcoal)
```css
:root {
  --bg-app: #121411;            /* Deep Obsidian */
  --surface: #1B1E19;           /* Smoked Granite */
  --surface-raised: #232720;    /* Elevated Charcoal */
  --text-primary: #F4F1EA;      /* Crisp Warm Alabaster */
  --text-secondary: #B0AEA5;    /* Muted Limestone */
  --text-muted: #72736C;        /* Dark Mineral */
  --accent-primary: #D47B57;    /* Luminous Terracotta */
  --accent-secondary: #A68668;  /* Light Oak */
  --accent-olive: #5B8565;      /* Forest Sage */
  --border-subtle: #2D332A;     /* Subtle Mineral Border */
  --border-focus: #D47B57;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.25);
  --shadow-md: 0 4px 14px rgba(0, 0, 0, 0.35);
}
```

### Typography Hierarchy
- **Serif Display (Headers, Titles):** `'Playfair Display', Georgia, serif`
  - Evokes heritage architectural print and bespoke gallery catalogs.
- **Body & Controls:** `'Plus Jakarta Sans', system-ui, sans-serif`
  - Ultra-high legibility at small sizes, optimal kerning, clean geometric structure.
- **Monospace Coordinates & Codes:** `'Space Grotesk', 'SF Mono', monospace`
  - High precision for HEX values, CIELAB triplets, ΔE distances, and millimeter measurements.

---

## 3. Component Architecture (`ui/components.py`)

### 1. Editorial Header (`render_header`)
- **Brand Title:** `CHROMA STUDIO AI` with subtle uppercase tracking.
- **Active Subscription Badge:** Shows real-time tier (Free, Plus, Pro) and billing period.
- **Usage Metrics Pill:** Displays quota consumption (Analyses remaining, AI Previews used).
- **Session Indicators:** Identifies authenticated user or Guest Session.

### 2. Dominant Tone Strip (`render_dominant_color_strip`)
- Horizontal multi-band strip displaying extracted room tones with percentage bars.
- Clicking any swatch updates the active target tone across other workspaces.

### 3. Room Analysis Card (`render_room_analysis_card`)
- Clean breakdown of detected architectural style (e.g., Japandi, Mid-Century Modern, Minimalist), room typology, and prevailing natural lighting.
- Explains color-space metrics (perceptual luminance, color temperature).

### 4. 60-30-10 Palette Swatch Cards (`render_palette_swatches_horizontal`)
- Proportional color distribution breakdown:
  - **60% Primary Wall:** Dominant wall tone with HEX, RGB, and CIELAB coordinates.
  - **30% Secondary Surface:** Supporting feature wall, millwork, or cabinetry.
  - **10% Accent:** High-contrast focal point, door accents, or architectural niches.
  - **Trim & Ceiling:** Off-white or tinted alabaster neutral anchor.

### 5. Indian Paint Brand Matcher Card (`render_paint_brand_match_card`)
- Side-by-side swatch rendering matching target color against physical shade cards (Asian Paints, Berger, Nerolac, Dulux India).
- Shows exact commercial shade name, manufacturer shade code, finish (Royale Matt, Silk Glamor, Velvet Touch), approximate retail price in ₹ INR per litre, and exact CIELAB ΔE distance.

### 6. AI Privacy Shield Banner (`render_privacy_shield_banner`)
- Editorial alert banner establishing user data sovereignty:
  - 🛡️ Zero external frame retention.
  - 🔒 Local in-memory computer vision execution.
  - 🇪🇺 GDPR-compliant user data bundle export & cascading account deletion.

---

## 4. Workspace Redesign Overview (21 Views)

1. **🏛️ Showcase / Landing:** Architectural hero presentation detailing the 3-step pipeline (Computer Vision, Harmony Engine, Zero-Bleed Recolouring).
2. **🎨 Studio & Analysis:** Interactive analysis workspace with collapsible specification drawer, 4 design concepts, 60-30-10 distribution, and dual-mode wall recolouring.
3. **📹 Live Camera Studio:** Continuous WebRTC video stream (`streamlit-webrtc`) with real-time room element bounding boxes and snapshot capture.
4. **🖼️ Visualization Studio:** Zero-bleed perceptual wall recolouring with 3 luminance retention algorithms (CIELAB Perceptual, HSL Luminance Preserving, Photometric Normalization) and side-by-side / split-slider comparison.
5. **🎯 Live Colour Scanner:** Viewfinder reticle optical sampler with neighborhood noise averaging, dominant cluster extraction, and personal Chroma Library persistence.
6. **🏷️ Paint Brand Matcher:** Physical shade card matcher covering Asian Paints, Berger Paints, Kansai Nerolac, and Dulux India with INR pricing and verified ΔE metrics.
7. **📐 Furniture & Room Planner:** Spatial layout tool checking room density (≤35%), primary walkway corridors (≥90cm), and door swing arcs.
8. **🛒 Renovation Shopping:** Bill of Materials (BOM) generator with categorized coatings, primer, tools, and lighting with INR budgeting and Markdown checklist export.
9. **🛠️ Home Maintenance:** Wall surface health diagnostics (hairline cracks, dampness, peeling, scuffs), architectural treatment protocols, and condition comparison generator.
10. **💬 Chroma AI Assistant:** Context-aware interior design advisor drawing from active room analysis, palette, and materials; 100% offline knowledge graph with optional LLM integration.
11. **🧪 Experimental AI Lab:** Advanced simulations including 4 diurnal daylight shifts (3200K morning to 2700K dusk), 9 architectural material synergies, color swapping, and multi-plane semantic walls.
12. **🌈 Harmony Explorer:** 360° chromatic relationships (Complementary, Analogous, Triadic, Neutral Greige) and monochromatic depth (3 airy tints, 3 deep shades).
13. **🧬 Chroma Memory & DNA:** Preference learning system tracking liked and rejected colors, computing personalized design DNA.
14. **⏳ Design Timeline:** Immutable version snapshots with rollback capabilities and visual diffing.
15. **📁 Saved Palettes & Exports:** Multi-format export center supporting JSON, CSV, PNG Swatch Sheets, Text, Markdown, and PDF architectural specifications.
16. **💳 Subscription & Billing:** Transparent INR pricing (Free, Plus @ ₹1,499/mo, Pro @ ₹3,999/mo) with Razorpay sandbox integration, HMAC signature verification, and quota tracking.
17. **🛡️ AI Privacy Shield:** Dedicated transparency dashboard detailing in-memory video stream handling, local CV algorithms, and GDPR data export.
18. **👤 Profile & Preferences:** User customization, display name, preferred design styles, and visual defaults.
19. **🔐 Account & Security:** PBKDF2 password hashing, rate-limited login, password reset tokens, and cascading account deletion.
20. **🔑 Sign In / Sign Up:** Clean authentication forms with live validation.
21. **❓ Architectural Guide:** In-depth documentation on color science, CIELAB metrics, and interior application rules.

---

## 5. Performance & Streamlit Optimization

- **Zero-Flicker Execution:** View caching (`@st.cache_data`) for dominant color extraction, room analysis, and wall segmentation prevents duplicate heavy OpenCV/SciPy computations when navigating between views.
- **Modular Layouts:** Multi-column grids (`st.columns`) with responsive proportions ensure clean rendering on desktop, laptop, and tablet displays.
- **Resource Cleanup:** Temporary frame buffers are automatically cleared in memory to ensure low memory footprints during continuous webcam streaming.
