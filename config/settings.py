"""Application configuration and constants."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

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

# UI Design Tokens
DESIGN_TOKENS = {
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
