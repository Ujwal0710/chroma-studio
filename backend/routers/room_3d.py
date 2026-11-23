"""FastAPI Router for 3D Room Experience (Mode A Depth, Mode B Room-Box, Mode C Multi-Photo)."""
import io
import base64
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Response
from PIL import Image
import numpy as np

from modules.image_validation import validate_image_bytes
from modules.room_3d_engine import Room3DEngine

router = APIRouter(prefix="/3d", tags=["3D Room Experience"])


class RoomBoxRequest(BaseModel):
    wall_color: str = "#3B82F6"
    ceiling_color: str = "#F8FAFC"
    floor_color: str = "#A07855"
    room_width_m: float = 4.5
    room_depth_m: float = 5.0
    room_height_m: float = 2.8


class MultiScanRequest(BaseModel):
    photos_count: int = 15
    project_name: str = "Residential Multi-View Scan"


@router.post("/depth-mesh")
async def generate_depth_mesh(
    file: Optional[UploadFile] = File(None),
    image_data: Optional[str] = Form(None),
    target_hex: Optional[str] = Form(None),
    resolution: int = Form(60)
):
    """Mode A: Reconstruct 3D textured depth mesh from single room photograph."""
    proc_pil = None
    if file:
        try:
            raw = await file.read()
            _, proc_pil, _ = validate_image_bytes(raw)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif image_data:
        try:
            raw = base64.b64decode(image_data.split(",", 1)[-1])
            _, proc_pil, _ = validate_image_bytes(raw)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file or image_data required.")

    rgb = np.array(proc_pil)
    engine = Room3DEngine.get_instance()
    mesh = engine.generate_depth_mesh(rgb, target_hex=target_hex, mesh_resolution=resolution)

    return {
        "status": "success",
        "mesh": mesh
    }


@router.post("/room-box")
async def estimate_room_box_layout(
    file: Optional[UploadFile] = File(None),
    image_data: Optional[str] = Form(None),
    wall_color: str = Form("#3B82F6"),
    ceiling_color: str = Form("#F8FAFC"),
    floor_color: str = Form("#A07855"),
    room_width_m: float = Form(4.5),
    room_depth_m: float = Form(5.0),
    room_height_m: float = Form(2.8)
):
    """Mode B: Estimate 3D perspective room-box layout with adjustable wall dimensions."""
    proc_pil = None
    if file:
        try:
            raw = await file.read()
            _, proc_pil, _ = validate_image_bytes(raw)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif image_data:
        try:
            raw = base64.b64decode(image_data.split(",", 1)[-1])
            _, proc_pil, _ = validate_image_bytes(raw)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        # Default fallback test canvas
        proc_pil = Image.new("RGB", (600, 450), (220, 215, 205))

    rgb = np.array(proc_pil)
    engine = Room3DEngine.get_instance()
    box_data = engine.estimate_room_box(
        rgb,
        wall_color=wall_color,
        ceiling_color=ceiling_color,
        floor_color=floor_color,
        room_width_m=room_width_m,
        room_depth_m=room_depth_m,
        room_height_m=room_height_m
    )

    return {
        "status": "success",
        "box": box_data
    }


@router.post("/reconstruct-multi")
def start_multi_photo_scan(req: MultiScanRequest):
    """Mode C: Initiate multi-photo background Structure-from-Motion photogrammetry reconstruction."""
    engine = Room3DEngine.get_instance()
    job_id = engine.start_multi_photo_scan(photos_count=req.photos_count, project_name=req.project_name)
    return {
        "status": "success",
        "job_id": job_id,
        "message": f"Multi-photo photogrammetry task queued for {req.photos_count} photographs."
    }


@router.get("/job/{job_id}")
def get_3d_job_status(job_id: str):
    """Check asynchronous multi-photo 3D reconstruction progress and download link."""
    engine = Room3DEngine.get_instance()
    status_data = engine.get_job_status(job_id)
    if not status_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"3D job '{job_id}' not found.")
    return {"status": "success", "job": status_data}


@router.get("/export/glb")
def export_glb():
    """Export 3D architectural room model as standard binary glTF 2.0 (.glb)."""
    engine = Room3DEngine.get_instance()
    # Generate representative box model for export
    dummy_img = np.full((300, 400, 3), 220, dtype=np.uint8)
    mesh = engine.generate_depth_mesh(dummy_img, mesh_resolution=30)
    glb_bytes = engine.export_mesh_to_glb(mesh["vertices"], mesh["indices"], mesh["uvs"])

    return Response(
        content=glb_bytes,
        media_type="model/gltf-binary",
        headers={"Content-Disposition": "attachment; filename=chroma_studio_room.glb"}
    )
