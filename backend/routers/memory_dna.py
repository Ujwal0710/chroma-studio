"""Memory & DNA router: Personal design taste memory and inspectable Chroma DNA profile."""
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends

from models.schemas import PaletteConcept, ChromaDNA
from modules.chroma_memory import record_favorite_palette, record_rejected_palette, get_chroma_memory, clear_chroma_memory
from modules.chroma_dna import generate_chroma_dna
from config.settings import DB_PATH
from backend.auth import get_current_user_optional

router = APIRouter(tags=["Chroma Memory & DNA"])


class PaletteFeedbackRequest(BaseModel):
    palette: PaletteConcept
    style: Optional[str] = ""


@router.post("/memory/favourite")
def favourite_palette(
    req: PaletteFeedbackRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Register user favorite palette to elevate preferred tones in future recommendations."""
    user_id = current_user["id"] if current_user else "guest_user"
    record_favorite_palette(user_id=user_id, palette=req.palette, style=req.style or "", db_path=DB_PATH)
    mem = get_chroma_memory(user_id=user_id, db_path=DB_PATH)
    return {"status": "success", "message": f"Added '{req.palette.name}' to favorites.", "memory": mem}


@router.post("/memory/reject")
def reject_palette(
    req: PaletteFeedbackRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Register dismissed palette to suppress clashing tones and undertones."""
    user_id = current_user["id"] if current_user else "guest_user"
    record_rejected_palette(user_id=user_id, palette=req.palette, db_path=DB_PATH)
    mem = get_chroma_memory(user_id=user_id, db_path=DB_PATH)
    return {"status": "success", "message": f"Recorded dismissed tones from '{req.palette.name}'.", "memory": mem}


@router.get("/memory")
def get_memory_profile(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Retrieve full transparent record of stored color and atmosphere preferences."""
    user_id = current_user["id"] if current_user else "guest_user"
    mem = get_chroma_memory(user_id=user_id, db_path=DB_PATH)
    return {"status": "success", "memory": mem}


@router.delete("/memory")
def reset_memory_profile(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Clear all recorded color preferences and reset taste memory to neutral."""
    user_id = current_user["id"] if current_user else "guest_user"
    clear_chroma_memory(user_id=user_id, db_path=DB_PATH)
    return {"status": "success", "message": "Chroma memory cleared."}


@router.get("/dna", response_model=ChromaDNA)
def get_chroma_dna_profile(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Generate inspectable personal Chroma DNA signature with primary, secondary, and accent affinities."""
    user_id = current_user["id"] if current_user else "guest_user"
    return generate_chroma_dna(user_id=user_id, db_path=DB_PATH)
