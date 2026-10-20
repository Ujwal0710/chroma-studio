"""AI image generation and editing provider for enhanced room previews."""
import os
import io
import base64
from typing import Dict, Any, Optional, Tuple
from PIL import Image

from config.settings import (
    IMAGE_EDIT_API_KEY,
    IMAGE_EDIT_MODEL,
    IMAGE_EDIT_PROVIDER,
    IMAGE_EDIT_API_ENDPOINT
)
from models.schemas import PaletteConcept


def mask_api_key(api_key: str) -> str:
    """Safely mask an API key for UI/logs, never printing or exposing the raw secret."""
    key = (api_key or "").strip()
    if not key:
        return ""
    if len(key) <= 8:
        return "********"
    return f"{key[:4]}...{key[-4:]}"


def get_image_editing_status(override_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve structured diagnostic status for image editing configuration.
    Validates detection of credentials without exposing raw secret values.
    """
    api_key = (override_api_key if override_api_key is not None else IMAGE_EDIT_API_KEY).strip()
    is_configured = bool(api_key)
    provider_name = IMAGE_EDIT_PROVIDER.lower()
    model_name = IMAGE_EDIT_MODEL or "dall-e-3"

    if is_configured:
        mode2_status = f"Ready (Generative AI Render via {IMAGE_EDIT_PROVIDER.upper()} {model_name})"
        message = (
            f"AI Generative Preview is configured and ready via {IMAGE_EDIT_PROVIDER.upper()} "
            f"({model_name}). Key detected: [{mask_api_key(api_key)}]."
        )
    else:
        mode2_status = "Unavailable (Requires IMAGE_EDIT_API_KEY or OPENAI_API_KEY in .env)"
        message = (
            "AI Image Editing API key not detected in .env. "
            "Mode 1 local wall recolouring is active with 100% full luminance preservation."
        )

    return {
        "is_configured": is_configured,
        "provider": IMAGE_EDIT_PROVIDER,
        "model": model_name,
        "endpoint": IMAGE_EDIT_API_ENDPOINT,
        "masked_key": mask_api_key(api_key) if is_configured else None,
        "mode1_status": "Active (Local Luminance-Preserving Wall Recolouring, 100% Offline & Unmetered)",
        "mode2_status": mode2_status,
        "message": message
    }


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
    api_key = (override_api_key if override_api_key is not None else IMAGE_EDIT_API_KEY).strip()
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

            url = IMAGE_EDIT_API_ENDPOINT or "https://api.openai.com/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            model_name = IMAGE_EDIT_MODEL or "dall-e-3"
            # OpenAI DALL-E 3 supports 1024x1024, DALL-E 2 supports 1024x1024, 512x512, 256x256
            payload = {
                "model": model_name,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "response_format": "b64_json"
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            # Handle both b64_json and direct url responses
            img_data = data.get("data", [{}])[0]
            if "b64_json" in img_data:
                b64_str = img_data["b64_json"]
                gen_img = Image.open(io.BytesIO(base64.b64decode(b64_str))).convert("RGB")
            elif "url" in img_data:
                img_url = img_data["url"]
                img_resp = requests.get(img_url, timeout=30)
                img_resp.raise_for_status()
                gen_img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
            else:
                return None, {
                    "success": False,
                    "status": "error",
                    "message": "AI provider response did not contain image data."
                }

            return gen_img, {
                "success": True,
                "status": "generated",
                "provider": f"OpenAI ({model_name})",
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
