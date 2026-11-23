"""Rooms router: physical image upload, optical color extraction, SegFormer semantic wall segmentation, and recolouring."""
import io
import base64
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Body
from PIL import Image
import numpy as np
import cv2

from modules.image_validation import validate_image_bytes, ImageValidationError
from modules.colour_extraction import extract_dominant_colors
from modules.room_analysis import analyze_room_photograph
from modules.wall_segmentation import generate_wall_mask
from modules.room_visualization import apply_luminance_preserving_recolour, create_mask_overlay_preview
from modules.semantic_segmentation import (
    SemanticSegmentationEngine,
    recolour_surface_lab,
    recolour_multi_surface,
    fast_guided_filter,
    evaluate_mask_quality
)
from modules.subscription_service import check_entitlement, record_usage_metric
from backend.auth import get_current_user_optional

router = APIRouter(prefix="/rooms", tags=["Rooms & Computer Vision"])


def pil_to_base64_jpeg(img: Image.Image, quality: int = 85) -> str:
    """Encode PIL image to base64 JPEG data URL."""
    buf = io.BytesIO()
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(buf, format="JPEG", quality=quality)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def pil_to_base64_png(img: Image.Image) -> str:
    """Encode PIL image to base64 PNG data URL."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def base64_to_cv2(b64_str: str) -> np.ndarray:
    """Decode base64 image string to OpenCV BGR array."""
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    raw = base64.b64decode(b64_str)
    nparr = np.frombuffer(raw, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


@router.post("/analyse")
async def analyse_room(
    file: UploadFile = File(...),
    room_type: str = Form("Automatic Detection"),
    interior_style: str = Form("Automatic Detection"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Analyse uploaded room photograph: extract dominant tones, perceptual lighting, and spatial characteristics."""
    user_id = current_user["id"] if current_user else "guest_user"

    allowed, limit_msg, _ = check_entitlement(user_id, "room_analysis")
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Entitlement Limit: {limit_msg}")

    try:
        raw_bytes = await file.read()
        orig_pil, proc_pil, metadata = validate_image_bytes(raw_bytes, filename=file.filename or "room.jpg")
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to decode image: {str(e)}")

    extracted = extract_dominant_colors(proc_pil, num_colors=7)
    analysis = analyze_room_photograph(
        proc_pil,
        extracted_analysis=extracted,
        selected_room_type=room_type,
        selected_style=interior_style
    )

    record_usage_metric(user_id, "analysis")

    return {
        "status": "success",
        "metadata": metadata,
        "image_preview": pil_to_base64_jpeg(proc_pil),
        "dominant_tones": extracted,
        "room_analysis": analysis
    }


class RefineMaskRequest(BaseModel):
    mask_b64: str
    x: int
    y: int
    action: str = "add"  # 'add' or 'remove'
    brush_radius: int = 18
    guide_image_b64: Optional[str] = None


@router.post("/segment")
async def segment_room_wall(
    file: Optional[UploadFile] = File(None),
    image_data: Optional[str] = Form(None),
    sensitivity: float = Form(0.55),
    edge_protection: float = Form(0.65),
    upper_bias: float = Form(0.70)
):
    """Compute architectural surface masks (walls, ceiling, floor, furniture) using SegFormer ADE20K."""
    proc_pil = None
    if file:
        try:
            raw_bytes = await file.read()
            _, proc_pil, _ = validate_image_bytes(raw_bytes)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif image_data:
        try:
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
            raw_bytes = base64.b64decode(image_data)
            _, proc_pil, _ = validate_image_bytes(raw_bytes)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file or image_data must be provided.")

    rgb_arr = np.array(proc_pil)
    engine = SemanticSegmentationEngine.get_instance()

    if engine.is_available:
        surface_masks = engine.generate_surface_masks(rgb_arr)
        wall_mask = surface_masks.get("wall", np.zeros(rgb_arr.shape[:2], dtype=np.uint8))
        total_px = rgb_arr.shape[0] * rgb_arr.shape[1]
        wall_coverage = round((np.count_nonzero(wall_mask) / float(total_px)) * 100.0, 1)

        gray_guide = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2GRAY)
        quality_gate = evaluate_mask_quality(wall_mask, gray_guide)

        mask_meta = {
            "wall_coverage_percent": float(quality_gate["wall_coverage_percent"]),
            "segmentation_confidence": quality_gate["segmentation_confidence"],
            "edge_sharpness_score": quality_gate["edge_sharpness_score"],
            "connected_components_count": quality_gate["connected_components_count"],
            "warnings": quality_gate["warnings"],
            "invites_manual_correction": quality_gate["invites_manual_correction"],
            "model": "SegFormer ADE20K Neural Model",
            "classes_detected": list(surface_masks.keys())
        }

        # Encode separate surface masks
        encoded_masks = {}
        for s_name, s_mask in surface_masks.items():
            encoded_masks[s_name] = pil_to_base64_png(Image.fromarray(s_mask))
    else:
        # Fallback to bilateral/Sobel multi-cue mask
        wall_mask, mask_meta = generate_wall_mask(
            proc_pil,
            sensitivity=sensitivity,
            upper_bias=upper_bias,
            edge_protection=edge_protection
        )
        encoded_masks = {"wall": pil_to_base64_png(Image.fromarray(wall_mask))}

    mask_img = Image.fromarray(wall_mask)
    overlay_img = create_mask_overlay_preview(proc_pil, wall_mask)

    return {
        "status": "success",
        "metadata": mask_meta,
        "mask_png": pil_to_base64_png(mask_img),
        "mask_only": pil_to_base64_png(mask_img),
        "masks": encoded_masks,
        "overlay_preview": pil_to_base64_jpeg(overlay_img),
        "mask_overlay": pil_to_base64_jpeg(overlay_img)
    }


@router.post("/recolour")
async def recolour_room(
    file: Optional[UploadFile] = File(None),
    image_data: Optional[str] = Form(None),
    target_hex: str = Form("#B85C38"),
    intensity: float = Form(0.85),
    surface: str = Form("wall"),
    wall_hex: Optional[str] = Form(None),
    ceiling_hex: Optional[str] = Form(None),
    trim_hex: Optional[str] = Form(None),
    accent_hex: Optional[str] = Form(None),
    compensate_lighting: bool = Form(True),
    sensitivity: float = Form(0.55),
    edge_protection: float = Form(0.65),
    upper_bias: float = Form(0.70)
):
    """Apply zero-bleed luminance-preserving LAB color replacement to detected surfaces."""
    proc_pil = None
    if file:
        try:
            raw_bytes = await file.read()
            _, proc_pil, _ = validate_image_bytes(raw_bytes)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif image_data:
        try:
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
            raw_bytes = base64.b64decode(image_data)
            _, proc_pil, _ = validate_image_bytes(raw_bytes)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file or image_data must be provided.")

    rgb_arr = np.array(proc_pil)
    engine = SemanticSegmentationEngine.get_instance()

    if engine.is_available:
        surface_masks = engine.generate_surface_masks(rgb_arr)
        
        # Check if multi-surface configuration is provided
        if any([wall_hex, ceiling_hex, trim_hex, accent_hex]):
            surface_colors = {}
            if wall_hex: surface_colors["wall"] = wall_hex
            if ceiling_hex: surface_colors["ceiling"] = ceiling_hex
            if trim_hex: surface_colors["trim"] = trim_hex
            if accent_hex: surface_colors["accent_wall"] = accent_hex
            
            recoloured_rgb = recolour_multi_surface(
                rgb_arr,
                surface_masks=surface_masks,
                surface_colors=surface_colors,
                surface_intensities={"wall": intensity, "ceiling": intensity, "trim": intensity, "accent_wall": intensity},
                compensate_lighting=compensate_lighting
            )
            mask_meta = {"engine": "SegFormer ADE20K", "mode": "multi_surface", "surfaces": list(surface_colors.keys())}
        else:
            target_mask = surface_masks.get(surface, surface_masks.get("wall", np.zeros(rgb_arr.shape[:2], dtype=np.uint8)))
            recoloured_rgb = recolour_surface_lab(
                rgb_arr,
                target_mask,
                target_hex=target_hex,
                intensity=intensity,
                compensate_lighting=compensate_lighting
            )
            mask_meta = {"engine": "SegFormer ADE20K", "surface": surface, "intensity": intensity}
        
        recoloured_pil = Image.fromarray(recoloured_rgb)
        mask_meta = {"engine": "SegFormer ADE20K", "surface": surface, "intensity": intensity}
    else:
        h = target_hex.lstrip("#")
        try:
            target_rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            target_rgb = (184, 92, 56)

        wall_mask, mask_meta = generate_wall_mask(
            proc_pil,
            sensitivity=sensitivity,
            upper_bias=upper_bias,
            edge_protection=edge_protection
        )
        recoloured_pil = apply_luminance_preserving_recolour(
            proc_pil,
            wall_mask,
            target_rgb,
            intensity=intensity,
            strategy="cielab_perceptual"
        )

    h_clean = target_hex.lstrip("#")
    try:
        rgb_tuple = (int(h_clean[0:2], 16), int(h_clean[2:4], 16), int(h_clean[4:6], 16))
    except Exception:
        rgb_tuple = (184, 92, 56)

    b64_result = pil_to_base64_jpeg(recoloured_pil)
    return {
        "status": "success",
        "recoloured_image": b64_result,
        "preview_image": b64_result,
        "image_preview": b64_result,
        "target_color": {
            "hex": target_hex,
            "rgb": rgb_tuple
        },
        "mask_metadata": mask_meta
    }


@router.post("/mask/refine")
def refine_surface_mask(req: RefineMaskRequest):
    """Apply interactive tap or brush correction to add/remove wall areas with guided edge snapping."""
    engine = SemanticSegmentationEngine.get_instance()
    try:
        mask_raw = base64.b64decode(req.mask_b64.split(",", 1)[-1])
        mask_arr = cv2.imdecode(np.frombuffer(mask_raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid mask_b64: {str(e)}")

    guide_arr = None
    if req.guide_image_b64:
        try:
            guide_raw = base64.b64decode(req.guide_image_b64.split(",", 1)[-1])
            guide_arr = cv2.imdecode(np.frombuffer(guide_raw, np.uint8), cv2.IMREAD_COLOR)
        except Exception:
            guide_arr = None

    updated_mask = engine.apply_manual_correction(
        mask_arr,
        x=req.x,
        y=req.y,
        action=req.action,
        brush_radius=req.brush_radius,
        guide_image=guide_arr
    )

    mask_pil = Image.fromarray(updated_mask)
    return {
        "status": "success",
        "mask_png": pil_to_base64_png(mask_pil),
        "mask_only": pil_to_base64_png(mask_pil)
    }


class LiveSegmentRequest(BaseModel):
    image_base64: str
    target_hex: str = "#B85C38"
    intensity: float = 0.85
    sensitivity: float = 0.50


@router.post("/live-segment")
def live_segment_frame(req: LiveSegmentRequest):
    """Real-time downscaled frame segmentation & recolour for Live Camera scanner (3-8 FPS)."""
    try:
        raw = base64.b64decode(req.image_base64.split(",", 1)[-1])
        nparr = np.frombuffer(raw, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Failed to decode image buffer")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid frame: {str(e)}")

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    engine = SemanticSegmentationEngine.get_instance()

    # Generate surface masks at camera downscaled resolution
    masks = engine.generate_surface_masks(rgb)
    wall_mask = masks.get("wall", np.zeros(rgb.shape[:2], dtype=np.uint8))

    # Fast luminance-preserving recolour
    recoloured = recolour_surface_lab(rgb, wall_mask, req.target_hex, intensity=req.intensity, compensate_lighting=False)

    # Encode recoloured frame and wall mask
    recoloured_bgr = cv2.cvtColor(recoloured, cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode(".jpg", recoloured_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    b64_res = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")

    _, mask_buf = cv2.imencode(".png", wall_mask)
    b64_mask = "data:image/png;base64," + base64.b64encode(mask_buf).decode("utf-8")

    total_pixels = wall_mask.size
    wall_pixels = int(np.count_nonzero(wall_mask > 127))

    return {
        "status": "success",
        "recoloured_frame": b64_res,
        "mask_png": b64_mask,
        "wall_coverage": round((wall_pixels / max(1, total_pixels)) * 100.0, 1)
    }

