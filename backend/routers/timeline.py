"""Design Timeline router: Version snapshots, project history, and rollback."""
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status, Depends

from models.schemas import PaletteConcept, ColorSwatch
from modules.design_timeline import save_timeline_version, list_project_timeline, get_timeline_version
from modules.palette_engine import build_swatch
from config.settings import DB_PATH
from backend.auth import get_current_user_optional

router = APIRouter(prefix="/timeline", tags=["Design Timeline"])


class SaveTimelineRequest(BaseModel):
    project_id: str = "proj_default"
    palette: Optional[PaletteConcept] = None
    palette_data: Optional[Dict[str, Any]] = None
    label: str = "Concept Iteration"
    notes: Optional[str] = ""
    thumbnail_data: Optional[str] = ""


class RollbackRequest(BaseModel):
    project_id: str = "proj_default"
    version_id: str


@router.get("")
def get_timeline(
    project_id: str = "proj_default",
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Retrieve full chronological snapshot history for the active design project."""
    user_id = current_user["id"] if current_user else "guest_user"
    timeline = list_project_timeline(user_id=user_id, project_id=project_id, db_path=DB_PATH)
    return {"status": "success", "project_id": project_id, "versions": timeline}


@router.post("")
def create_snapshot(
    req: SaveTimelineRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Save an immutable project state snapshot into the design timeline."""
    user_id = current_user["id"] if current_user else "guest_user"

    pal = req.palette
    if not pal and req.palette_data:
        try:
            pal = PaletteConcept(**req.palette_data)
        except Exception:
            # Fallback to creating a representative palette concept
            sel_tone = req.palette_data.get("selected_tone", "#B85C38")
            h = sel_tone.lstrip("#")
            try:
                rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
            except Exception:
                rgb = (184, 92, 56)
            sw_prim = build_swatch(rgb, "Selected Surface (60%)")
            sw_sec = build_swatch((214, 197, 179), "Secondary Wall (30%)")
            sw_acc = build_swatch((48, 39, 31), "Accent (10%)")
            sw_trim = build_swatch((247, 243, 238), "Trim")
            pal = PaletteConcept(
                id=f"snap_{req.label.lower().replace(' ', '_')}",
                name=req.label,
                concept_category="Design Snapshot",
                harmony_type="Architectural Milestone",
                description=req.notes or "Saved design milestone state",
                atmosphere="Customized",
                primary_wall=sw_prim,
                secondary_wall=sw_sec,
                accent=sw_acc,
                trim=sw_trim,
                design_rationale="User-captured version milestone",
                furniture_flooring_compatibility="Compatible with existing interior substrates"
            )

    if not pal:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either 'palette' or 'palette_data' must be supplied."
        )

    v_id = save_timeline_version(
        user_id=user_id,
        project_id=req.project_id,
        palette=pal,
        label=req.label,
        notes=req.notes or "",
        thumbnail_data=req.thumbnail_data or "",
        db_path=DB_PATH
    )
    return {"status": "success", "version_id": v_id, "message": f"Snapshot '{req.label}' saved."}


@router.post("/rollback")
def rollback_to_version(
    req: RollbackRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Roll back active design space to a specified prior timeline snapshot."""
    user_id = current_user["id"] if current_user else "guest_user"
    version = get_timeline_version(version_id=req.version_id, user_id=user_id, db_path=DB_PATH)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timeline version '{req.version_id}' not found for user."
        )

    return {
        "status": "success",
        "message": f"Restored snapshot: {version.get('label')}",
        "version": version,
        "palette": version.get("palette_data")
    }
