# CHROMA STUDIO AI 🎨
### Futuristic Premium Edition — Intelligent Architectural Colour & Interior Design Workspace

**CHROMA STUDIO AI** is an architectural-grade, computer-vision and AI-powered interior colour intelligence system. The application transforms uploaded room photographs into personalized colour concepts, visual simulations, and actionable design specifications while enforcing the 60-30-10 interior rule and perceptual color science.

---

## 🏛️ Distinctive Premium Features

1. **Chroma Memory (Adaptive Personalization Engine):**
   - Automatically learns user style tendencies based on favorited palettes and rejected tones.
   - Adjusts subsequent recommendation rankings using an inspectable score modifier.
   - History can be viewed and cleared at any time.

2. **Chroma DNA (Personal Design Signature):**
   - Deterministic design signature derivation reflecting dominant color families, contrast tendencies, temperature bias, and material affinities.
   - Renders a 4-swatch signature strip that can be applied to new room spaces.

3. **Design Timeline (Visual Versioning & Rollback):**
   - Saves immutable design iteration snapshots with version numbers, timestamps, notes, and thumbnails.
   - Revisit historical project states without losing iteration progress.

4. **Colour Harmony Explorer:**
   - 360° chromatic relationships: Complementary (+180°), Analogous (-30°, +30°), Triadic (+120°, +240°), Monochromatic tints and shades, and Neutral Supporting Greiges.
   - Exact CIELAB perceptual distance calculations ($\Delta E$).

5. **Daylight Simulator:**
   - Visual simulation of 4 diurnal lighting conditions: *Warm Morning Light* (3200K), *Neutral Daylight* (5500K), *Cool Overcast Daylight* (6800K), and *Warm Evening Light* (2700K).
   - Preserves luminance distribution while shifting spectral color balance.

6. **Material-Aware Palettes Engine:**
   - Evaluates compatibility against 9 architectural materials: *Oak Wood, Walnut Wood, Carrara Marble, Cast Concrete, Natural Stone, Brushed Brass, Black Matte Metal, Natural Linen, and Velvet*.
   - Explains undertone synergies and potential clashes.

7. **Colour Swap Playground:**
   - Interactively swap any single slot (e.g. Accent or Primary Wall) while keeping other anchors locked.
   - Updates palettes and preview renderings instantly.

8. **Smart Paint Quantity Estimator:**
   - Calculates net wall surface from room length, width, and wall height.
   - Deducts standard doorways (1.89 m²) and window openings (1.44 m²).
   - Computes required litres (with 10% safety margin), recommends packaging can breakdown (10L, 4L, 1L), and estimates cost at user-supplied INR rates.

9. **Semantic Wall Editing:**
   - Multi-plane region isolation: *Main Wall, Accent Wall, Ceiling / Upper Crown, and All Wall Surfaces*.
   - Targeted recolouring preserves ambient room lighting and shadows.

---

## 🔒 Security & Authentication Architecture

- **Salted PBKDF2-HMAC-SHA256 Password Hashing:** 100,000 iterations with cryptographically random salts.
- **Brute-Force Rate Limiting:** Automatic temporary lockout after 5 consecutive failed login attempts within 15 minutes.
- **Secure Password Reset:** Single-use, time-limited HMAC reset tokens.
- **Multi-Tenant Data Segregation:** All saved palettes, project timeline entries, profiles, and usage records enforce user ownership.
- **Privacy & GDPR Compliance:** One-click personal data archive download (JSON) and permanent cascading account deletion.

---

## 💳 Indian Rupee (INR) Subscriptions & Entitlements

Configurable tier structures with server-side backend enforcement:

| Tier | Monthly (INR) | Annual (INR) | Monthly Analyses | AI Previews | Max Saved Palettes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Free Starter** | ₹0 | ₹0 | 3 | 0 | 5 |
| **Plus Creator** | ₹299 | ₹2,870 *(save ~20%)* | 30 | 5 | 50 |
| **Pro Designer** | ₹699 | ₹6,710 *(save ~20%)* | 100 | 25 | 250 |

- **Razorpay Integration:** Cryptographic HMAC-SHA256 payment signature verification (`order_id|payment_id`).
- **Idempotent Webhook Processing:** Verifies `X-Razorpay-Signature` and prevents duplicate event execution using the `payment_events` table.
- **Verified Sandbox Mode:** Includes cryptographic test simulation allowing local end-to-end checkout verification without live keys.

---

## 🎨 Editorial Design System Tokens

The user interface supports both **Light** and **Dark** themes with typography set in *Plus Jakarta Sans* and *Playfair Display*:

- **Light Mode:**
  - Background: `#F5F0E8` (Warm Ivory)
  - Surface: `#FFFCF7` (Cream Alabaster)
  - Primary Text: `#30271F` (Espresso)
  - Accent: `#725640` (Rich Umber)
  - Secondary Accent: `#B98468` (Warm Sienna)
- **Dark Mode:**
  - Background: `#171916` (Deep Obsidian)
  - Surface: `#222520` (Architectural Charcoal)
  - Primary Text: `#F5F0E8` (Warm White)
  - Accent: `#A9BFA2` (Muted Botanical Sage)
  - Secondary Accent: `#C98F70` (Muted Terracotta)

---

## 🧪 Automated Test Suite (46 Tests Passing)

Run all unit tests using pytest:
```bash
python -m pytest tests/ -v
```

All 46 automated tests run deterministically with synthetic test fixtures and zero external network calls:
- `test_auth_security.py`: Password hashing, validation, signup, login, rate-limiting, token resets (4 tests)
- `test_colour_extraction.py`: Dominant color extraction, luminance, and naming (4 tests)
- `test_distinctive_features.py`: Chroma Memory, Chroma DNA, Timeline, Harmony Explorer, Daylight, Materials, Swapping, Paint Estimator, Semantic Wall (9 tests)
- `test_image_validation.py`: Formats, sizes, corrupted file handling (5 tests)
- `test_palette_engine.py`: 4 concepts, user preferences, deduplication (3 tests)
- `test_preferences.py`: Avoid colors, accent saturation (2 tests)
- `test_profile_and_privacy.py`: Profile CRUD, data export, cascading deletion (2 tests)
- `test_resilience_and_fallbacks.py`: Zero-cost standalone resilience, API fallbacks (4 tests)
- `test_storage.py`: SQLite persistence, exports (4 tests)
- `test_subscription_and_billing.py`: Plan limits, Razorpay HMAC signatures, idempotent webhooks, sandbox (5 tests)
- `test_visualization.py`: Wall segmentation, luminance-preserving recolouring, comparisons (4 tests)

---

## 🚀 Running the Application

Launch the Streamlit interface:
```bash
python -m streamlit run app.py
```
Open your browser at:
`http://localhost:8501`
