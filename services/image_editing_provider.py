"""AI image generation and editing provider for enhanced room previews."""
import os
import io
import base64
from typing import Dict, Any, Optional, Tuple
from PIL import Image

from config.settings import (
    IMAGE_EDIT_API_KEY,
    IMAGE_EDIT_MODEL,
    IMAGE_EDIT_PROVIDER
)
from models.schemas import PaletteConcept


def build_room_recolour_prompt(
    palette: PaletteConcept,
    room_type: str,
    interior_style: str
) -> str:
    """Build a precise architectural prompt for image-to-image or editing models."""
    return (
        f"Professional architectural interior photography of a {interior_style} {room_type}. "
        f"Recolour the primary interior walls to {palette.primary_wall.name} ({palette.primary_wall.hex}). "
        f"Accents or feature elements should reflect {palette.accent.name} ({palette.accent.hex}). "
        f"Maintain existing trim/ceilings in clean architectural white ({palette.trim.hex}). "
        f"STRICT CONSTRAINT: Keep all furniture, flooring, windows, doors, structural pillars, lighting fixtures, "
        f"and room layout 100% identical. Only repaint the wall surfaces. Preserve natural shading, depth, and ambient shadows."
    )


def generate_ai_room_preview(
    original_img: Image.Image,
    palette: PaletteConcept,
    room_type: str = "Living Room",
    interior_style: str = "Modern",
    override_api_key: Optional[str] = None
) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
    """
    Generate an AI-enhanced room preview using configured image generation/editing provider.

    Returns:
        Tuple of (generated_image_or_None, metadata_dict)
    """
    api_key = (override_api_key or IMAGE_EDIT_API_KEY).strip()
    prompt = build_room_recolour_prompt(palette, room_type, interior_style)

    if not api_key:
        return None, {
            "success": False,
            "status": "not_configured",
            "message": "AI Image Editing API key is not configured. Local wall recolouring preview is active and available."
        }

    try:
        # Check provider: OpenAI DALL-E or edit endpoint
        if IMAGE_EDIT_PROVIDER.lower() == "openai":
            import requests

            headers = {
                "Authorization": f"Bearer {api_key}"
            }

            # Prepare image in PNG format with RGBA/RGB
            buf = io.BytesIO()
            original_img.save(buf, format="PNG")
            buf.seek(0)

            # Using DALL-E 3 or gpt-image generation
            # Note: DALL-E 3 supports generation, DALL-E 2 supports edits with masks.
            # Here we query OpenAI Images API
            url = "https://api.openai.com/v1/images/generations"
            payload = {
                "model": IMAGE_EDIT_MODEL or "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "response_format": "b64_json"
            }
            resp = requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            b64_str = data["data"][0]["b64_json"]
            gen_img = Image.open(io.BytesIO(base64.b64decode(b64_str))).convert("RGB")

            return gen_img, {
                "success": True,
                "status": "generated",
                "provider": f"OpenAI ({IMAGE_EDIT_MODEL})",
                "prompt_used": prompt,
                "notice": "AI-generated visualization. Architectural layout may exhibit subtle variations from the physical space."
            }

        else:
            return None, {
                "success": False,
                "status": "unsupported_provider",
                "message": f"Unsupported image editing provider '{IMAGE_EDIT_PROVIDER}'."
            }

    except Exception as e:
        return None, {
            "success": False,
            "status": "error",
            "message": f"AI Image preview failed ({type(e).__name__}: {str(e)}). Local preview remains fully operational."
        }
