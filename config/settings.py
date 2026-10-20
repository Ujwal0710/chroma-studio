"""Application configuration, constants, and subscription definitions."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Product Branding (Configurable)
APP_NAME = os.environ.get("APP_NAME", "CHROMA STUDIO AI")
APP_TAGLINE = os.environ.get("APP_TAGLINE", "Intelligent Architectural Colour & Interior Design Workspace")

# Database
DB_PATH = os.environ.get("DATABASE_PATH", str(DATA_DIR / "palettes.db"))

# Upload constraints
MAX_IMAGE_SIZE_MB = int(os.environ.get("MAX_IMAGE_SIZE_MB", "15"))
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}
PROCESSING_MAX_DIMENSION = 1200  # Resize for analysis & segmentation to keep memory/CPU fast

# External API Configuration
VISION_API_KEY = os.environ.get("VISION_API_KEY", "")
VISION_MODEL = os.environ.get("VISION_MODEL", "gemini-1.5-flash")
VISION_PROVIDER = os.environ.get("VISION_PROVIDER", "gemini")  # 'gemini' or 'openai_compatible'
VISION_API_ENDPOINT = os.environ.get("VISION_API_ENDPOINT", "")

IMAGE_EDIT_API_KEY = os.environ.get("IMAGE_EDIT_API_KEY", "")
IMAGE_EDIT_MODEL = os.environ.get("IMAGE_EDIT_MODEL", "dall-e-3")
IMAGE_EDIT_PROVIDER = os.environ.get("IMAGE_EDIT_PROVIDER", "openai")

# Razorpay / Payment Configuration
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_samplekeyid123")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "rzp_test_samplesecret456")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "rzp_webhook_secret_test")
PAYMENT_CURRENCY = "INR"

# Security & Session Settings
AUTH_SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "chroma_studio_super_secret_dev_key_2026")
SESSION_COOKIE_NAME = "chroma_studio_session"
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# Subscription Plans (INR Pricing & Configurable Limits)
SUBSCRIPTION_PLANS = {
    "free": {
        "id": "free",
        "name": "Free Starter",
        "monthly_price_inr": 0,
        "annual_price_inr": 0,
        "monthly_analyses_limit": 3,
        "ai_preview_limit": 0,
        "max_saved_palettes": 5,
        "features": [
            "Up to 3 new room analyses / month",
            "4 Architectural colour concepts",
            "Standard HEX, RGB & LRV values",
            "Mode 1 Local wall recolouring",
            "Up to 5 saved palette slots",
            "Standard JSON & CSV exports"
        ],
        "badge": "Standard"
    },
    "plus": {
        "id": "plus",
        "name": "Plus Creator",
        "monthly_price_inr": 299,
        "annual_price_inr": 2870,  # ~20% savings
        "monthly_analyses_limit": 30,
        "ai_preview_limit": 5,
        "max_saved_palettes": 50,
        "features": [
            "Up to 30 room analyses / month",
            "Preference-driven harmony engine",
            "Chroma Memory & Chroma DNA profiling",
            "Daylight Simulator (4 lighting moods)",
            "Colour Harmony Explorer & Swapping",
            "Smart Paint Quantity Estimator",
            "50 saved designs & Design Timeline",
            "High-resolution PNG swatch sheets"
        ],
        "badge": "Popular"
    },
    "pro": {
        "id": "pro",
        "name": "Pro Designer",
        "monthly_price_inr": 699,
        "annual_price_inr": 6710,  # ~20% savings
        "monthly_analyses_limit": 100,
        "ai_preview_limit": 25,
        "max_saved_palettes": 250,
        "features": [
            "Up to 100 room analyses / month",
            "Semantic multi-region wall & trim editing",
            "Material-aware ranking (9 materials)",
            "AI-Enhanced Generative Room Renders",
            "Comprehensive Consultation Reports (TXT/JSON/CSV)",
            "Unlimited project version rollback",
            "Priority local CV & model queue",
            "Dedicated architectural design suite"
        ],
        "badge": "Studio Grade"
    }
}

# UI Design Tokens
LIGHT_THEME_TOKENS = {
    "background": "#F5F0E8",
    "surface": "#FFFCF7",
    "primary_text": "#30271F",
    "secondary_text": "#786B60",
    "primary_accent": "#725640",
    "secondary_accent": "#B98468",
    "subtle_border": "#E3D8CB",
    "success": "#4A6B53",
    "warning": "#C47C3B",
    "danger": "#A43E3E"
}

DARK_THEME_TOKENS = {
    "background": "#171916",
    "surface": "#222520",
    "primary_text": "#F5F0E8",
    "secondary_text": "#B8B5AC",
    "primary_accent": "#A9BFA2",
    "secondary_accent": "#C98F70",
    "subtle_border": "#363B33",
    "success": "#6A9B75",
    "warning": "#E09756",
    "danger": "#C45B5B"
}

DESIGN_TOKENS = LIGHT_THEME_TOKENS

# Supported Room Types & Styles
ROOM_TYPES = [
    "Automatic Detection",
    "Living Room",
    "Bedroom",
    "Dining Room",
    "Kitchen",
    "Home Office",
    "Bathroom",
    "Entryway / Hallway",
    "Other Interior"
]

INTERIOR_STYLES = [
    "Automatic Detection",
    "Modern",
    "Minimalist",
    "Scandinavian",
    "Traditional",
    "Contemporary",
    "Industrial",
    "Bohemian",
    "Mid-Century Modern",
    "Farmhouse",
    "Japandi",
    "Coastal"
]

