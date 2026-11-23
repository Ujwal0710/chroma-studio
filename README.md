# CHROMA STUDIO AI 🎨
### Modern Next.js Website + FastAPI Backend & Architectural Colour Intelligence

**CHROMA STUDIO AI** is a production-grade, computer-vision and AI-powered interior colour intelligence platform. It features a modern **Next.js (App Router, TypeScript, Tailwind CSS)** web frontend paired with a high-performance **FastAPI** backend that exposes deterministic CIELAB colour science, zero-bleed optical wall segmentation, photorealistic luminance-preserving paint simulation, and 60-30-10 harmonic balancing.

The legacy Streamlit application (`app.py`) is also preserved in full for standalone local prototyping.

---

## ⚡ Quick Start: Running the Application

### 1. Backend (FastAPI on `http://localhost:8000`)
```bash
# From repository root
python -m uvicorn backend.main:app --reload --port 8000
```
- Interactive Swagger documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive Redoc documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Frontend (Next.js on `http://localhost:3000`)
```bash
# Navigate to frontend folder
cd frontend
npm run dev
```
- Open [http://localhost:3000](http://localhost:3000) in your browser.

### 3. Legacy Streamlit App (Optional reference on `http://localhost:8501`)
```bash
python -m streamlit run app.py
```

---

## 🏗️ Architecture & Technology Stack

| Layer | Technologies & Libraries |
| :--- | :--- |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Framer Motion, Lucide Icons |
| **Backend API** | FastAPI, Uvicorn, Starlette, PyJWT, Pydantic v2 schemas |
| **Computer Vision & Colour Science** | OpenCV (cv2), Pillow (PIL), NumPy, SciPy, CIELAB colour spaces, $\Delta E_{2000}$ metrics |
| **Data & Storage** | SQLite, PBKDF2-HMAC-SHA256 password security, constant-time token verification, GDPR data controls |
| **Design System** | Dark-only architectural palette: Obsidian (`#121411`), Smoked Charcoal (`#1B1E19`), Warm Ivory (`#F4F1EA`), Terracotta Amber (`#B85C38`) |

---

## 🔌 API Endpoints Map

All endpoints execute deterministic Python logic (no mock stubs or placeholder buttons):

- `POST /auth/register` — Creates user account with PBKDF2 password hashing. Sets httpOnly JWT cookie.
- `POST /auth/login` — Authenticates user, enforces brute-force protection, issues httpOnly session JWT.
- `POST /auth/logout` — Revokes session cookie.
- `POST /auth/reset-request` — Initiates secure time-limited password recovery.
- `POST /auth/reset-confirm` — Consumes reset token and commits new password hash.
- `GET /auth/me` — Returns current authenticated user and session validity.
- `POST /rooms/analyse` — EXIF-aware sanitization, dominant tone extraction, room typology, and lighting metrics.
- `GET /rooms/sample` — Delivers pre-bundled high-res architectural sample room for 1-click test workflows.
- `POST /rooms/segment` — Zero-bleed photometric edge detection isolating walls from trim and furniture.
- `POST /rooms/recolour` — Luminance-preserving paint simulation (`cielab_perceptual`, `adaptive_luminance`, `architectural_glaze`).
- `POST /palettes/generate` — Computes 4 harmonic design concepts adhering to the 60-30-10 ratio.
- `POST /palettes/swap` — Interactively swaps color roles (Dominant, Secondary, Accent) with lock retention.
- `POST /daylight/simulate` — Simulates Planckian chromatic adaptation across 4 Kelvins (3200K, 5500K, 6800K, 2700K).
- `POST /materials/score` — Evaluates affinity against 9 physical architectural substrates (Oak, Walnut, Linen, Brass, Concrete, etc.).
- `POST /estimator/calculate` — Precision paint volume and packaging optimization (1L, 4L, 10L, 20L) with INR rates.
- `GET /timeline`, `POST /timeline`, `POST /timeline/rollback` — Reversible design milestones with snapshot rollback.
- `POST /memory/favourite`, `POST /memory/reject` — Updates user taste memory and score heuristics.
- `GET /dna` — Computes deterministic Chroma DNA signature swatches and temperature tendencies.
- `GET /plans`, `POST /billing/order`, `POST /billing/verify` — Subscription tier checks and simulated Razorpay payments.
- `GET /account/data`, `DELETE /account/data` — Full GDPR data portability export and permanent erasure.

---

## 🧪 Testing & Verification

Run the complete test suite (90 passing tests covering Computer Vision, API endpoints, Auth, Estimator, and Harmonization):
```bash
python -m pytest -v
```

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
