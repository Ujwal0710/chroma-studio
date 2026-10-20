# AI Interior Colour Palette Suggester 🎨

An architectural-grade, computer-vision and AI-powered interior colour recommendation system. The application analyzes uploaded photographs of physical rooms, extracts dominant tones using K-Means clustering and ITU-R BT.709 perceptual luminance, evaluates spatial and lighting conditions, generates four distinct colour harmony concepts using colour theory, and simulates new wall paint via luminance-preserving recolouring and generative AI models.

---

## 🏛️ Key Capabilities

- **Module A — Image Validation & Orientation:**
  - Supports JPG, JPEG, PNG, and WEBP uploads up to 15MB.
  - Automatically corrects EXIF camera orientation tags.
  - Validates magic bytes, dimensions, and aspect ratio.
  - Resizes images for efficient CV processing while preserving original display fidelity.

- **Module B — Computer Vision & Colour Extraction:**
  - Extracts representative dominant colours and spatial proportions using MiniBatch K-Means clustering.
  - Filters out camera specular blowout (#FFFFFF) and sensor shadow noise (#000000).
  - Evaluates perceptual luminance, saturation categories, and correlated colour temperature tendencies.
  - Maps colours to an architectural interior design naming dictionary (e.g., *Desert Sand*, *Warm Linen*, *Muted Sage*, *Architectural Charcoal*).

- **Module C — AI Room Analysis & Local Fallback:**
  - Connects to Vision LLMs (Google Gemini 1.5 Flash via `google-genai` / `google-generativeai` or OpenAI-compatible vision models).
  - Extracts structured observations: room type, design style, visible materials, wall/floor base descriptions, lighting qualities, and design challenges.
  - **100% Functional Local Fallback:** When API credentials are absent or fail, the system falls back to a deterministic computer-vision inference engine without crashing.

- **Module D & E — Colour Theory & Preference-Driven Recommendation Engine:**
  - Generates 4 distinct concepts:
    1. **Warm & Inviting** (Analogous / Monochromatic warm tones)
    2. **Cool & Calming** (Monochromatic / Complementary cool tones)
    3. **Modern Neutral** (Architectural Greige & Travertine with curated accent)
    4. **Bold Accent / Contemporary Contrast** (Complementary / Triadic focal point)
  - Enforces the **60-30-10** interior design rule: Primary Wall (60%), Secondary Wall / Trim (30%), Accent Details (10%).
  - Provides interactive controls: Room Type, Design Style, Warm/Cool Temperature, Lightness (Airy vs Deep/Moody), Saturation, Desired Atmosphere, Accent Intensity, Preferred Colours, and Colours to Avoid.
  - Eliminates duplicate or near-duplicate palettes using CIELAB Delta-E distance metrics ($ΔE \ge 6.0$).
  - Evaluates palettes with a transparent heuristic match score (55% to 98%).

- **Module F — Room Colour Visualization:**
  - **Mode 1 (Local Wall Recolouring):** Intelligent wall segmentation combining Sobel edge detection, vertical priors, and color homogeneity region growing. Recolours walls using luminance-scaled blending to preserve ambient shadows, lighting gradients, and wall textures.
  - **Mode 1 Comparison Modes:** Side-by-side comparison, interactive split divider slider, full room view, and wall mask overlay inspection.
  - **Mode 2 (AI-Enhanced Generative Preview):** Connects to image-editing models (e.g. OpenAI DALL-E) to produce architectural renders while preserving room layout.

- **Module G & H — Persistence & Export Consultation Suite:**
  - Persistent SQLite database (`data/palettes.db`) for saving palettes, notes, and custom names.
  - Search, retrieve, and delete historical palette records.
  - Portable exports:
    - **JSON:** Complete machine-readable metadata and colour values.
    - **CSV:** Tabular hex, RGB, role, and proportion breakdown.
    - **PNG Swatch Sheet:** High-resolution architectural presentation card.
    - **TXT Consultation Report:** Formatted design summary with furniture compatibility guidelines.

---

## 🎨 Design System Tokens

The user interface follows an architectural design aesthetic:
- **Background:** `#F5F0E8` (Warm Ivory)
- **Surface:** `#FFFCF7` (Cream Alabaster)
- **Primary Text:** `#30271F` (Espresso)
- **Secondary Text:** `#786B60` (Muted Sand Taupe)
- **Primary Accent:** `#725640` (Rich Terracotta Umber)
- **Secondary Accent:** `#B98468` (Warm Sienna)
- **Subtle Border:** `#E3D8CB` (Soft Travertine)

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Pip

### 1. Clone or Open Workspace
```bash
cd f:\module
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```

Configure your API keys if you wish to enable cloud vision and generative features:
```env
# Vision Model (Google Gemini or OpenAI)
VISION_PROVIDER=gemini
VISION_API_KEY=your_gemini_api_key_here
VISION_MODEL=gemini-1.5-flash

# Image Editing / Preview Model
IMAGE_EDIT_PROVIDER=openai
IMAGE_EDIT_API_KEY=your_openai_api_key_here
IMAGE_EDIT_MODEL=dall-e-3
```
> **Note:** Paid API keys are **not required** for core operation. All image processing, dominant color extraction, room analysis, palette generation, local wall recolouring, and exports run entirely offline with local fallbacks.

---

## 🏃 Running the Application

Launch the Streamlit web interface:
```bash
python -m streamlit run app.py
```
Open your browser at:
`http://localhost:8501`

---

## 🧪 Running the Automated Test Suite

Run all automated unit tests using pytest:
```bash
python -m pytest tests/ -v
```
All 26 unit tests run deterministically with synthetic test images and zero external network calls:
- Image decoding and validation
- Corrupted/oversized image rejection
- Dominant colour extraction from known colour patches
- RGB/HEX and perceptual luminance conversions
- 4-concept palette generation and required schema fields
- User preference responsiveness
- CIELAB duplicate palette elimination
- Luminance-preserving wall recolouring and outside-mask pixel preservation
- SQLite save, retrieve, search, and delete
- JSON, CSV, Swatch Sheet PNG, and TXT report exports
- Missing API credentials handling and provider failure recovery
- Zero-cost standalone execution

---

## 📐 Project Structure

```
f:\module\
├── app.py                      # Main Streamlit application orchestrating the 11-step journey
├── requirements.txt            # Project dependencies
├── README.md                   # Complete architectural documentation
├── IMPLEMENTATION_PLAN.md      # Implementation blueprint
├── .env.example                # Example environment variable template
├── .gitignore                  # Git ignore rules
├── config/
│   ├── __init__.py
│   └── settings.py             # Global constants, paths, design tokens, room types
├── models/
│   ├── __init__.py
│   └── schemas.py              # Pydantic schemas (ColorSwatch, PaletteConcept, RoomAnalysis)
├── modules/
│   ├── __init__.py
│   ├── image_upload.py         # Image upload processing
│   ├── image_validation.py     # File validation, MIME/magic bytes, EXIF orientation
│   ├── image_processing.py     # NumPy/OpenCV conversions, RGB/HSV/Lab, luminance, temperature
│   ├── colour_extraction.py    # K-Means clustering, noise rejection, interior naming
│   ├── colour_theory.py        # Harmonies (Analogous, Mono, Comp, Neutral), Delta-E distance
│   ├── palette_engine.py       # Deterministic 4-concept palette generator & heuristic ranking
│   ├── wall_segmentation.py    # Gradient edge detection, vertical prior, homogeneity mask
│   ├── room_visualization.py   # Luminance-preserving recolouring, side-by-side, split slider
│   ├── room_analysis.py        # Room analysis orchestrator
│   ├── ai_preview.py           # Generative preview wrapper
│   ├── preferences.py          # User preference definitions and presets
│   ├── storage.py              # SQLite database persistence and querying
│   └── export_service.py       # JSON, CSV, PNG Swatch sheet, and TXT report generators
├── services/
│   ├── __init__.py
│   ├── vision_provider.py      # Google Gemini / OpenAI vision provider with local fallback
│   └── image_editing_provider.py # Generative preview provider with offline fallback
├── ui/
│   ├── __init__.py
│   ├── styles.py               # Custom design system CSS
│   └── components.py           # Reusable Streamlit UI components
├── data/
│   └── .gitkeep                # SQLite storage directory
└── tests/
    ├── __init__.py
    ├── test_image_validation.py
    ├── test_colour_extraction.py
    ├── test_palette_engine.py
    ├── test_preferences.py
    ├── test_visualization.py
    ├── test_storage.py
    └── test_resilience_and_fallbacks.py
```

---

## 🔍 Known Limitations & Optical Realities

1. **Camera Sensor White Balance:** Digital cameras automatically shift color temperature depending on indoor incandescent vs outdoor daylight. Extracted colours reflect observed pixel values rather than physical paint pigments.
2. **Wall Segmentation Accuracy:** Complex scenes with intricate millwork, open shelving, or wallpaper patterns may require adjusting the *Sensitivity* and *Edge Protection* sliders in Mode 1.
3. **AI-Enhanced Preview Fidelity:** Generative image editing models (Mode 2) may occasionally alter small background decorative items while changing wall colours. Mode 1 is recommended for exact architectural layout preservation.
