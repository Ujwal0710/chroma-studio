# Implementation Plan - AI Interior Colour Palette Suggester

## 1. Project Context
- Environment: Standalone Streamlit Python application (workspace initially empty).
- Python 3.14 with NumPy, Pillow, Scikit-learn, SciPy, Pydantic, Requests, Pytest.
- Design tokens:
  - Background: `#F5F0E8`
  - Surface: `#FFFCF7`
  - Primary text: `#30271F`
  - Secondary text: `#786B60`
  - Primary accent: `#725640`
  - Secondary accent: `#B98468`
  - Subtle border: `#E3D8CB`

## 2. Architecture & Modules
- `config/settings.py`: Configuration, environment variables, design tokens, default parameters.
- `models/schemas.py`: Pydantic models for ColorSwatch, Palette, RoomAnalysisResult, PreferenceSettings, SavedPaletteRecord.
- `modules/image_validation.py`: MIME type, file extension, magic bytes, dimensions, aspect ratio, orientation fix (EXIF), size limits, sanitization.
- `modules/image_processing.py`: Resizing, RGB/HSV/LAB conversions, luminance, color temperature estimation, brightness calculation.
- `modules/colour_extraction.py`: K-means clustering with scikit-learn, filtering background/noise pixels, calculating proportions, naming colors, classifying neutral/warm/cool/saturated/muted.
- `modules/colour_theory.py`: Harmony calculations (Complementary, Analogous, Monochromatic, Neutral & Accent), color distance (CIEDE2000 / Euclidean in Lab), temperature calculation.
- `modules/palette_engine.py`: Deterministic palette generator creating 4 core concepts:
  1. Warm & Inviting
  2. Cool & Calming
  3. Modern Neutral
  4. Bold Accent / Contemporary Contrast
  Each with primary wall, secondary wall/supporting, accent, trim/ceiling, HEX, RGB, proportions, design rationale, atmosphere, furniture compatibility. Ranking algorithm based on preferences, contrast, harmony, duplicate removal.
- `services/vision_provider.py`: Vision LLM provider (Google Gemini via `google-genai` / `google-generativeai`, and OpenAI/OpenRouter compatible endpoints via httpx/requests) with resilient local rule-based fallback when keys are absent or API fails.
- `services/image_editing_provider.py`: AI-enhanced preview integration boundary (supporting image-to-image / inpainting / generative preview) with clear status feedback and offline local fallback.
- `modules/room_analysis.py`: Orchestrates semantic room analysis, combines vision model insights (when available) with computer-vision extracted room traits, room type detection, style detection.
- `modules/wall_segmentation.py`: Robust wall segmentation combining color clustering, luminance thresholds, edge detection, and region masking, with manual tolerance / threshold controls.
- `modules/room_visualization.py`: Mode 1 luminance-preserving wall recolouring (preserving shading, textures, edges, windows, furniture) + Side-by-Side & interactive comparison slider + image download.
- `modules/preferences.py`: Interactive user preference definitions (room type, style, temperature, lightness, colorfulness, atmosphere, accent intensity, preferred/avoid colors, furniture constraints, budget).
- `modules/storage.py`: SQLite persistence for palettes, metadata, search/filtering, deletion, and preference saving.
- `modules/export_service.py`: JSON export, CSV export, PNG swatch sheet generator (Pillow), text/markdown report generator.
- `ui/styles.py` & `ui/components.py`: Custom CSS implementing the warm ivory/espresso/terracotta design system, palette cards, swatch visualizers, comparison slider, interactive widgets.
- `app.py`: Main Streamlit entrypoint orchestrating the 11-step user journey.
- `tests/`: Comprehensive pytest suite covering all 15 test requirements.
