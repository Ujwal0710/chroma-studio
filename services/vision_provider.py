"""Vision LLM provider with structured schema validation and resilient local fallback."""
import os
import json
import io
import base64
from typing import Dict, Any, Optional
from PIL import Image

from config.settings import (
    VISION_API_KEY,
    VISION_MODEL,
    VISION_PROVIDER,
    VISION_API_ENDPOINT
)
from models.schemas import RoomAnalysisResult, ExtractedColorAnalysis


VISION_ANALYSIS_PROMPT = """
You are a senior interior designer and architectural colour consultant.
Analyze this room photograph and return a structured JSON response matching this schema:
{
  "detected_room_type": "string (e.g., Living Room, Bedroom, Kitchen, Dining Room, Home Office, Bathroom)",
  "detected_style": "string (e.g., Modern, Scandinavian, Traditional, Minimalist, Contemporary, Industrial, Japandi)",
  "visible_materials": ["list of strings, e.g., 'Oak hardwood flooring', 'Linen sofa', 'Brass hardware', 'Glass coffee table'"],
  "existing_wall_description": "string describing current wall colour and finish",
  "flooring_description": "string describing flooring material and tone",
  "dominant_color_observations": ["list of strings describing key colours noticed"],
  "apparent_lighting": "string describing natural and artificial lighting quality and direction",
  "lighting_temperature": "warm | cool | neutral",
  "brightness_level": "bright | medium | dim",
  "design_strengths": ["list of strings highlighting positive architectural or styling features"],
  "design_challenges": ["list of strings noting challenges like low natural light, competing undertones, etc."],
  "recommended_direction": "string giving specific expert advice on wall colour palettes that elevate this space",
  "confidence_notes": "string detailing any camera white-balance ambiguity or partial visibility constraints"
}

Important:
- Return ONLY valid raw JSON without markdown backticks or commentary.
- Be precise regarding undertones (e.g. pinkish beige, green-gray, yellow-cream) to ensure accurate paint matching.
"""


def encode_image_to_base64_jpeg(img: Image.Image, max_dim: int = 1024, quality: int = 85) -> str:
    """Resize image if needed and encode to base64 JPEG string."""
    buf_img = img.copy()
    if max(buf_img.size) > max_dim:
        buf_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    if buf_img.mode != "RGB":
        buf_img = buf_img.convert("RGB")

    buffer = io.BytesIO()
    buf_img.save(buffer, format="JPEG", quality=quality)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def call_gemini_vision(
    img: Image.Image,
    api_key: str,
    model_name: str = "gemini-1.5-flash",
    timeout_sec: int = 25
) -> Dict[str, Any]:
    """Call Google Gemini Vision API using google-genai or google-generativeai."""
    try:
        # Try google.genai client (new SDK)
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        image_bytes = buffer.getvalue()

        response = client.models.generate_content(
            model=model_name or "gemini-1.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                VISION_ANALYSIS_PROMPT
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        raw_text = response.text.strip()
        return json.loads(raw_text)

    except ImportError:
        # Fallback to google.generativeai (legacy SDK)
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name or "gemini-1.5-flash")

        # Convert image to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        image_parts = [{"mime_type": "image/jpeg", "data": buffer.getvalue()}]

        response = model.generate_content([image_parts[0], VISION_ANALYSIS_PROMPT])
        raw_text = response.text.strip()
        # Clean potential markdown fences
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        return json.loads(raw_text.strip())


def call_openai_compatible_vision(
    img: Image.Image,
    api_key: str,
    model_name: str = "gpt-4o-mini",
    endpoint: str = "https://api.openai.com/v1/chat/completions",
    timeout_sec: int = 25
) -> Dict[str, Any]:
    """Call OpenAI-compatible vision endpoint via requests."""
    import requests

    b64_img = encode_image_to_base64_jpeg(img)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name or "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_ANALYSIS_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_img}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    url = endpoint if endpoint else "https://api.openai.com/v1/chat/completions"
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    return json.loads(content)


def generate_local_rule_based_analysis(
    extracted_analysis: ExtractedColorAnalysis,
    selected_room_type: str = "Automatic Detection",
    selected_style: str = "Automatic Detection"
) -> RoomAnalysisResult:
    """
    Deterministic local fallback analysis based on computer vision color extraction,
    optical luminance, and lighting analysis when external vision API is not configured or fails.
    """
    # Infer room type if set to Automatic
    if selected_room_type == "Automatic Detection":
        inferred_room = "Living Room"  # Standard default interior
    else:
        inferred_room = selected_room_type

    # Infer style
    if selected_style == "Automatic Detection":
        if extracted_analysis.neutral_count >= 4:
            inferred_style = "Scandinavian / Minimalist"
        elif extracted_analysis.warm_count >= 4:
            inferred_style = "Warm Traditional / Contemporary"
        elif extracted_analysis.overall_brightness < 0.35:
            inferred_style = "Modern Industrial"
        else:
            inferred_style = "Modern Contemporary"
    else:
        inferred_style = selected_style

    # Key dominant observations
    top_colors = extracted_analysis.dominant_colors[:4]
    color_obs = [
        f"{c.role}: {c.name} ({c.hex}) - {c.description}"
        for c in top_colors
    ]

    # Existing wall / floor estimates from dominant colors
    light_neutrals = [c for c in extracted_analysis.dominant_colors if c.luminance and c.luminance > 0.55]
    dark_elements = [c for c in extracted_analysis.dominant_colors if c.luminance and c.luminance < 0.35]

    existing_wall = (
        f"Inferred light architectural base matching {light_neutrals[0].name} ({light_neutrals[0].hex})"
        if light_neutrals else f"Subdued base matching {top_colors[0].name} ({top_colors[0].hex})"
    )

    flooring_desc = (
        f"Medium to deep grounding surfaces matching {dark_elements[0].name} ({dark_elements[0].hex})"
        if dark_elements else "Neutral warm underlay with balanced reflectance"
    )

    strengths = [
        f"Established {extracted_analysis.overall_temperature_tendency} tonal baseline across dominant surfaces.",
        f"Harmonious proportion of neutrals ({extracted_analysis.neutral_count} neutral tones detected).",
        "Clear architectural balance between dominant planes and accent features."
    ]

    challenges = [
        "Camera sensor exposure and light reflections can alter subtle wall undertones.",
        "Ensure proposed wall hues maintain sufficient contrast with existing flooring and millwork."
    ]

    recommended = (
        f"Elevate the room by embracing {extracted_analysis.overall_temperature_tendency}-leaning "
        f"wall tones with light-reflectance value (LRV) calibrated to current brightness levels."
    )

    confidence = (
        "Locally synthesized via K-Means colour clustering and ITU-R BT.709 perceptual luminance. "
        "Camera white balance and local shading may influence measured chromaticity."
    )

    return RoomAnalysisResult(
        detected_room_type=inferred_room,
        detected_style=inferred_style,
        visible_materials=["Natural architectural textures", "Neutral fabric upholstery", "Reflective painted planes"],
        existing_wall_description=existing_wall,
        flooring_description=flooring_desc,
        dominant_color_observations=color_obs,
        apparent_lighting=extracted_analysis.lighting_condition_estimate,
        lighting_temperature=extracted_analysis.overall_temperature_tendency,
        brightness_level="bright" if extracted_analysis.overall_brightness > 0.6 else ("dim" if extracted_analysis.overall_brightness < 0.32 else "medium"),
        design_strengths=strengths,
        design_challenges=challenges,
        recommended_direction=recommended,
        confidence_notes=confidence,
        is_ai_inferred=False,
        provider_name="Local Computer Vision Fallback"
    )


def perform_room_analysis(
    img: Image.Image,
    extracted_analysis: ExtractedColorAnalysis,
    selected_room_type: str = "Automatic Detection",
    selected_style: str = "Automatic Detection",
    override_api_key: Optional[str] = None
) -> RoomAnalysisResult:
    """
    Perform semantic room analysis.
    Uses Vision LLM if configured; otherwise seamlessly falls back to local rule-based analysis.
    """
    api_key = (override_api_key or VISION_API_KEY).strip()

    if not api_key:
        return generate_local_rule_based_analysis(
            extracted_analysis=extracted_analysis,
            selected_room_type=selected_room_type,
            selected_style=selected_style
        )

    # Attempt Vision API call
    try:
        if VISION_PROVIDER == "openai_compatible":
            raw_result = call_openai_compatible_vision(
                img=img,
                api_key=api_key,
                model_name=VISION_MODEL,
                endpoint=VISION_API_ENDPOINT
            )
        else:
            # Default to Gemini
            raw_result = call_gemini_vision(
                img=img,
                api_key=api_key,
                model_name=VISION_MODEL
            )

        # Validate with RoomAnalysisResult schema
        result = RoomAnalysisResult(
            detected_room_type=raw_result.get("detected_room_type") if selected_room_type == "Automatic Detection" else selected_room_type,
            detected_style=raw_result.get("detected_style") if selected_style == "Automatic Detection" else selected_style,
            visible_materials=raw_result.get("visible_materials", []),
            existing_wall_description=raw_result.get("existing_wall_description", "Standard neutral interior wall"),
            flooring_description=raw_result.get("flooring_description", "Hardwood or neutral flooring"),
            dominant_color_observations=raw_result.get("dominant_color_observations", []),
            apparent_lighting=raw_result.get("apparent_lighting", "Balanced ambient lighting"),
            lighting_temperature=raw_result.get("lighting_temperature", "neutral"),
            brightness_level=raw_result.get("brightness_level", "medium"),
            design_strengths=raw_result.get("design_strengths", []),
            design_challenges=raw_result.get("design_challenges", []),
            recommended_direction=raw_result.get("recommended_direction", "Harmonize with existing flooring and trim"),
            confidence_notes=raw_result.get("confidence_notes", "Analysis verified through vision-capable model."),
            is_ai_inferred=True,
            provider_name=f"Vision Model ({VISION_PROVIDER.capitalize()} - {VISION_MODEL})"
        )
        return result

    except Exception as e:
        # Fallback gracefully and document the error without crashing
        fallback = generate_local_rule_based_analysis(
            extracted_analysis=extracted_analysis,
            selected_room_type=selected_room_type,
            selected_style=selected_style
        )
        fallback.confidence_notes = (
            f"Vision API request failed ({type(e).__name__}: {str(e)}). "
            f"Safely fell back to deterministic local CV analysis."
        )
        return fallback
