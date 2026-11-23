"""Account & Governance router: GDPR user data export, profile updates, and cascading account deletion."""
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Response, Depends

from modules.storage import (
    get_user_profile,
    update_user_profile,
    export_user_data_bundle,
    delete_user_account_cascade,
    DB_PATH
)
from backend.auth import require_authenticated_user

router = APIRouter(prefix="/account", tags=["Account & Data Governance"])


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    palette_preference_style: Optional[str] = None
    theme: Optional[str] = "dark"
    budget_tier: Optional[str] = "Mid-range"


@router.get("/profile")
def get_profile(current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Retrieve personal account details and stored design preferences."""
    profile = get_user_profile(user_id=current_user["id"], db_path=DB_PATH)
    return {"status": "success", "profile": profile}


@router.put("/profile")
def update_profile(req: UpdateProfileRequest, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """Update profile and design taste preferences."""
    update_user_profile(
        user_id=current_user["id"],
        full_name=req.full_name or current_user.get("full_name", ""),
        palette_preference_style=req.palette_preference_style or "",
        theme=req.theme or "dark",
        budget_tier=req.budget_tier or "Mid-range",
        db_path=DB_PATH
    )
    updated = get_user_profile(user_id=current_user["id"], db_path=DB_PATH)
    return {"status": "success", "message": "Profile updated successfully.", "profile": updated}


@router.get("/data")
def export_user_data(current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """GDPR Compliance: Export complete structured archive of all user palettes, timeline snapshots, and preferences."""
    bundle = export_user_data_bundle(user_id=current_user["id"], db_path=DB_PATH)
    return {
        "status": "success",
        "user_id": current_user["id"],
        "export_bundle": bundle
    }


@router.delete("/data")
def delete_user_account(response: Response, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    """GDPR Right to be Forgotten: Permanently delete user account and cascade delete all associated records."""
    delete_user_account_cascade(user_id=current_user["id"], db_path=DB_PATH)
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {
        "status": "success",
        "message": "User account and all associated architectural project records have been permanently erased."
    }
