"""Palettes router: 4 architectural concepts, 60-30-10 distribution, Delta-E 2000, and single-colour swap."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status, Depends

from models.schemas import (
    PaletteConcept,
    ExtractedColorAnalysis,
    RoomAnalysisResult,
    PreferenceSettings,
    ColorSwatch
)
from modules.palette_engine import generate_recommended_palettes, build_swatch
from modules.colour_swap import swap_palette_color
from modules.chroma_memory import evaluate_chroma_memory_influence
from modules.material_palettes import evaluate_material_compatibility
from backend.auth import get_current_user_optional

router = APIRouter(prefix="/palettes", tags=["Palettes & Harmonies"])


class GeneratePalettesRequest(BaseModel):
    extracted: Optional[ExtractedColorAnalysis] = None
    dominant_tones: Optional[ExtractedColorAnalysis] = None
    room_analysis: Optional[RoomAnalysisResult] = None
    preferences: Optional[PreferenceSettings] = None
    selected_materials: Optional[List[str]] = None
    primary_hex: Optional[str] = None
    room_type: Optional[str] = None
    interior_style: Optional[str] = None


class SwapColorRequest(BaseModel):
    palette: PaletteConcept
    target_role: Optional[str] = None  # 'primary_wall', 'secondary_wall', 'accent', 'trim'
    new_hex: Optional[str] = None
    from_role: Optional[str] = None
    to_role: Optional[str] = None


@router.post("/generate", response_model=List[PaletteConcept])
def generate_palettes(
    req: GeneratePalettesRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Generate 4 distinct interior design concepts adhering to the 60-30-10 rule and CIEDE2000 harmony."""
    user_id = current_user["id"] if current_user else "guest_user"

    extracted_obj = req.extracted or req.dominant_tones
    if not extracted_obj and req.primary_hex:
        h = req.primary_hex.lstrip("#")
        try:
            rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
            sw = build_swatch(rgb, "Primary Seed (60%)")
            extracted_obj = ExtractedColorAnalysis(
                dominant_colors=[sw],
                overall_brightness=0.6,
                overall_temperature_tendency="warm",
                mean_saturation=0.3,
                neutral_count=0,
                warm_count=1,
                cool_count=0,
                lighting_condition_estimate="Neutral Balanced Daylight"
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid primary_hex format. Use #RRGGBB."
            )

    if not extracted_obj:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'extracted' or 'dominant_tones' (or valid 'primary_hex') is required to generate harmonic palettes."
        )

    prefs = req.preferences or PreferenceSettings()
    if req.room_type:
        prefs.room_type = req.room_type
    if req.interior_style:
        prefs.interior_style = req.interior_style

    palettes = generate_recommended_palettes(
        extracted=extracted_obj,
        room_analysis=req.room_analysis,
        preferences=prefs
    )

    # Adjust heuristic scores using Chroma Memory and selected material compatibility
    materials = req.selected_materials or ["Oak Wood", "Natural Linen"]
    for p in palettes:
        mem_delta, _ = evaluate_chroma_memory_influence(user_id, p)
        mat_delta, _ = evaluate_material_compatibility(materials, p)
        p.heuristic_score = round(min(98.0, max(50.0, p.heuristic_score + mem_delta + mat_delta)), 1)

    return palettes


@router.post("/swap", response_model=PaletteConcept)
def swap_color(req: SwapColorRequest):
    """Swap a single color swatch or interchange two roles in an active palette while locking anchor roles."""
    # Case 1: Role-to-role swap
    if req.from_role and req.to_role:
        from_key = req.from_role.lower().replace(" ", "_")
        to_key = req.to_role.lower().replace(" ", "_")
        pal_dict = req.palette.model_dump()
        if from_key in pal_dict and to_key in pal_dict:
            sw_from = pal_dict[from_key]
            sw_to = pal_dict[to_key]
            pal_dict[from_key] = sw_to
            pal_dict[to_key] = sw_from
            pal_dict["name"] = f"{req.palette.name} (Role Swapped)"
            pal_dict["colors"] = [pal_dict["primary_wall"], pal_dict["secondary_wall"], pal_dict["accent"], pal_dict["trim"]]
            return PaletteConcept(**pal_dict)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role keys '{req.from_role}' / '{req.to_role}'."
        )

    # Case 2: Direct color replacement for a target role
    if not req.target_role or not req.new_hex:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either ('target_role' and 'new_hex') or ('from_role' and 'to_role') must be provided."
        )

    valid_roles = ["primary_wall", "secondary_wall", "accent", "trim", "primary", "secondary"]
    role_key = req.target_role.lower()
    if not any(role_key in r for r in valid_roles):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target_role '{req.target_role}'. Must be one of: primary_wall, secondary_wall, accent, trim."
        )

    try:
        updated = swap_palette_color(req.palette, req.target_role, req.new_hex)
        return updated
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to swap color: {str(e)}")
