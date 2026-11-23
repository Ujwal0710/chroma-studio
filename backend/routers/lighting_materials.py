"""Lighting & Materials router: Daylight simulation across Kelvin conditions and 9 architectural materials."""
import io
import base64
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

from models.schemas import PaletteConcept, ColorSwatch
from modules.image_validation import validate_image_bytes
from modules.palette_engine import build_swatch
from modules.daylight_simulator import simulate_daylight_lighting, LIGHTING_CONDITIONS
from modules.material_palettes import evaluate_material_compatibility, MATERIAL_PROFILES, ALL_MATERIALS

router = APIRouter(tags=["Daylight & Materials"])

PRESET_TO_CONDITION = {
    "morning_3200k": "Warm Morning Light",
    "noon_5500k": "Neutral Daylight",
    "overcast_6800k": "Cool Overcast Daylight",
    "evening_2700k": "Warm Evening Light",
    "warm morning light": "Warm Morning Light",
    "neutral daylight": "Neutral Daylight",
    "cool overcast daylight": "Cool Overcast Daylight",
    "warm evening light": "Warm Evening Light"
}


class MaterialScoreRequest(BaseModel):
    palette: Optional[PaletteConcept] = None
    primary_hex: Optional[str] = None
    materials: Optional[List[str]] = None


@router.get("/daylight/conditions")
def get_daylight_conditions():
    """Return available daylight simulation presets with physical Kelvin temperatures."""
    return LIGHTING_CONDITIONS


@router.post("/daylight/simulate")
async def simulate_daylight(
    file: UploadFile = File(...),
    condition_name: Optional[str] = Form(None),
    preset: Optional[str] = Form(None),
    intensity: float = Form(0.85)
):
    """Simulate spectral illumination shift (Morning 3200K, Noon 5500K, Overcast 6800K, Evening 2700K)."""
    raw_key = (condition_name or preset or "Neutral Daylight").strip()
    target_condition = PRESET_TO_CONDITION.get(raw_key.lower(), raw_key)

    if target_condition not in LIGHTING_CONDITIONS:
        valid_conditions = list(LIGHTING_CONDITIONS.keys()) + list(PRESET_TO_CONDITION.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid lighting condition '{raw_key}'. Choose from: {valid_conditions}"
        )

    try:
        raw_bytes = await file.read()
        _, proc_pil, _ = validate_image_bytes(raw_bytes)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    sim_img = simulate_daylight_lighting(
        image=proc_pil,
        condition_name=target_condition,
        intensity=intensity
    )

    buf = io.BytesIO()
    sim_img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "status": "success",
        "condition": target_condition,
        "details": LIGHTING_CONDITIONS[target_condition],
        "simulated_image": f"data:image/jpeg;base64,{b64}"
    }


@router.get("/materials/all")
def get_all_materials():
    """Return catalogue of all 9 architectural materials with undertones and design guidelines."""
    return {
        "materials": ALL_MATERIALS,
        "profiles": MATERIAL_PROFILES
    }


@router.post("/materials/score")
def score_materials_compatibility(req: MaterialScoreRequest):
    """Score palette compatibility against selected architectural materials (woods, marbles, metals, linens)."""
    materials_list = req.materials or ALL_MATERIALS

    pal = req.palette
    if not pal:
        h = (req.primary_hex or "#B85C38").lstrip("#")
        try:
            rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            rgb = (184, 92, 56)
        sw_prim = build_swatch(rgb, "Primary Wall (60%)")
        sw_sec = build_swatch((214, 197, 179), "Secondary Wall (30%)")
        sw_acc = build_swatch((48, 39, 31), "Accent (10%)")
        sw_trim = build_swatch((247, 243, 238), "Trim")
        pal = PaletteConcept(
            id="temp-palette",
            name="Active Concept",
            concept_category="Architectural",
            harmony_type="Harmonious",
            description="Active working palette for substrate evaluation",
            atmosphere="Balanced",
            primary_wall=sw_prim,
            secondary_wall=sw_sec,
            accent=sw_acc,
            trim=sw_trim,
            design_rationale="Material compatibility seed evaluation",
            furniture_flooring_compatibility="Versatile architectural match"
        )

    score_delta, insights = evaluate_material_compatibility(materials_list, pal)

    material_details = []
    scores = []
    for mat in materials_list:
        if mat in MATERIAL_PROFILES:
            prof = MATERIAL_PROFILES[mat]
            # Calculate individual material affinity
            mat_delta, mat_insights = evaluate_material_compatibility([mat], pal)
            base_score = max(40, min(98, round(78 + mat_delta * 4)))
            status_label = "Harmonious" if base_score >= 80 else "Balanced" if base_score >= 65 else "Clashing"
            note = mat_insights[0] if mat_insights else prof["design_advice"]

            scores.append({
                "name": mat,
                "category": "Architectural Substrate",
                "score": base_score,
                "status": status_label,
                "delta_e": round(abs(mat_delta), 1),
                "notes": note,
                "suggested_texture": prof["undertone"]
            })

            material_details.append({
                "material": mat,
                "undertone": prof["undertone"],
                "design_advice": prof["design_advice"],
                "harmonious_hues": prof["harmonious_hues"],
                "clashing_hues": prof["clashing_hues"]
            })

    return {
        "status": "success",
        "palette_primary_hex": pal.primary_wall.hex,
        "score_delta": score_delta,
        "scores": scores,
        "insights": insights,
        "selected_material_details": material_details,
        "summary": f"Compatibility calculated across {len(materials_list)} architectural substrates."
    }
