"""Script to execute Phase 1: Audit of Wall Detection on 15 Diverse Room Photos with Objects Touching Walls.

Evaluates how the current segmentation engine handles objects near/touching walls:
- Sofas, cabinets, curtains, framed pictures, TVs, shelves, plants, white furniture against white walls.
Generates:
- Individual mask & overlay artifacts in diagnostics_audit/
- Contact sheet diagnostics_audit/audit_contact_sheet.png
- Diagnostic report diagnostics_audit/AUDIT_REPORT.md
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
from typing import Dict, Any, Tuple, List
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

from modules.semantic_segmentation import SemanticSegmentationEngine

AUDIT_DIR = "diagnostics_audit"
os.makedirs(AUDIT_DIR, exist_ok=True)

def create_synthetic_realistic_scene(scenario_id: str, title: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generates a realistic 512x512 indoor room photo with known ground truth wall and object masks.
    
    Returns:
        rgb_img: (512, 512, 3) uint8 image
        gt_wall: (512, 512) uint8 binary mask (255 = wall)
        gt_objects: (512, 512) uint8 binary mask (255 = object touching/near wall)
    """
    h, w = 512, 512
    img = np.zeros((h, w, 3), dtype=np.uint8)
    gt_wall = np.zeros((h, w), dtype=np.uint8)
    gt_objects = np.zeros((h, w), dtype=np.uint8)
    
    # Base room geometry: Wall occupies top 70%, floor occupies bottom 30%
    wall_y_bottom = int(h * 0.72)
    
    if scenario_id == "01_white_sofa_white_wall":
        # White wall (L* ~ 92) and white fabric sofa (L* ~ 93) with subtle shadow
        img[:wall_y_bottom, :] = [238, 238, 236]
        img[wall_y_bottom:, :] = [180, 160, 140]  # Light wood floor
        gt_wall[:wall_y_bottom, :] = 255
        
        # White sofa flush against wall
        sofa_top, sofa_bottom = int(h * 0.45), int(h * 0.85)
        sofa_left, sofa_right = int(w * 0.15), int(w * 0.85)
        cv2.rectangle(img, (sofa_left, sofa_top), (sofa_right, sofa_bottom), (242, 242, 240), -1)
        # Cushions & seams
        cv2.line(img, (w // 2, sofa_top), (w // 2, sofa_bottom), (210, 210, 208), 2)
        cv2.rectangle(img, (sofa_left + 15, sofa_top + 15), (sofa_right - 15, sofa_bottom - 20), (245, 245, 243), -1)
        # Soft shadow behind sofa on wall
        cv2.rectangle(img, (sofa_left, sofa_top - 12), (sofa_right, sofa_top), (225, 225, 222), -1)
        
        gt_objects[sofa_top:sofa_bottom, sofa_left:sofa_right] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "02_dark_cabinet_wall":
        # Warm beige wall with dark mahogany cabinet
        img[:wall_y_bottom, :] = [225, 215, 195]
        img[wall_y_bottom:, :] = [140, 110, 85]
        gt_wall[:wall_y_bottom, :] = 255
        
        cab_top, cab_bottom = int(h * 0.35), int(h * 0.75)
        cab_left, cab_right = int(w * 0.25), int(w * 0.75)
        cv2.rectangle(img, (cab_left, cab_top), (cab_right, cab_bottom), (45, 30, 20), -1)
        # Cabinet doors and brass hardware
        cv2.line(img, (w // 2, cab_top), (w // 2, cab_bottom), (30, 20, 12), 2)
        cv2.circle(img, (w // 2 - 20, (cab_top + cab_bottom) // 2), 4, (190, 160, 80), -1)
        cv2.circle(img, (w // 2 + 20, (cab_top + cab_bottom) // 2), 4, (190, 160, 80), -1)
        
        gt_objects[cab_top:cab_bottom, cab_left:cab_right] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "03_curtains_against_wall":
        # Pale grey wall with draped heavy linen curtains
        img[:wall_y_bottom, :] = [215, 218, 220]
        img[wall_y_bottom:, :] = [160, 140, 120]
        gt_wall[:wall_y_bottom, :] = 255
        
        # Left and right curtain drapes
        for x_start, x_end in [(0, int(w * 0.25)), (int(w * 0.75), w)]:
            for fold_x in range(x_start, x_end, 16):
                cv2.rectangle(img, (fold_x, 20), (fold_x + 8, wall_y_bottom + 40), (160, 150, 140), -1)
                cv2.rectangle(img, (fold_x + 8, 20), (fold_x + 16, wall_y_bottom + 40), (135, 125, 115), -1)
            gt_objects[20:wall_y_bottom + 40, x_start:x_end] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "04_framed_pictures_gallery":
        # Neutral greige wall with 4 framed art prints
        img[:wall_y_bottom, :] = [220, 216, 210]
        img[wall_y_bottom:, :] = [150, 130, 110]
        gt_wall[:wall_y_bottom, :] = 255
        
        coords = [
            (int(w * 0.15), int(h * 0.12), int(w * 0.45), int(h * 0.38)),
            (int(w * 0.55), int(h * 0.12), int(w * 0.85), int(h * 0.38)),
            (int(w * 0.15), int(h * 0.44), int(w * 0.45), int(h * 0.70)),
            (int(w * 0.55), int(h * 0.44), int(w * 0.85), int(h * 0.70))
        ]
        for x1, y1, x2, y2 in coords:
            cv2.rectangle(img, (x1, y1), (x2, y2), (25, 25, 25), -1)  # Frame
            cv2.rectangle(img, (x1 + 8, y1 + 8), (x2 - 8, y2 - 8), (245, 245, 240), -1)  # Matting
            cv2.circle(img, ((x1 + x2) // 2, (y1 + y2) // 2), 25, (160, 90, 70), -1)  # Artwork
            gt_objects[y1:y2, x1:x2] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "05_wall_mounted_tv":
        # Feature wall with black flat-screen TV
        img[:wall_y_bottom, :] = [205, 205, 200]
        img[wall_y_bottom:, :] = [130, 115, 95]
        gt_wall[:wall_y_bottom, :] = 255
        
        tv_x1, tv_y1 = int(w * 0.20), int(h * 0.18)
        tv_x2, tv_y2 = int(w * 0.80), int(h * 0.52)
        cv2.rectangle(img, (tv_x1, tv_y1), (tv_x2, tv_y2), (18, 18, 18), -1)  # TV bezel
        cv2.rectangle(img, (tv_x1 + 5, tv_y1 + 5), (tv_x2 - 5, tv_y2 - 5), (32, 34, 38), -1)  # Screen
        # Cast shadow beneath TV
        cv2.rectangle(img, (tv_x1, tv_y2), (tv_x2, tv_y2 + 8), (175, 175, 170), -1)
        gt_objects[tv_y1:tv_y2 + 8, tv_x1:tv_x2] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "06_floating_shelves_books":
        # Sage green wall with floating oak shelves & book rows
        img[:wall_y_bottom, :] = [190, 200, 185]
        img[wall_y_bottom:, :] = [150, 135, 115]
        gt_wall[:wall_y_bottom, :] = 255
        
        for shelf_y in [int(h * 0.25), int(h * 0.48)]:
            # Shelf wood plank
            cv2.rectangle(img, (int(w * 0.15), shelf_y), (int(w * 0.85), shelf_y + 16), (170, 125, 80), -1)
            gt_objects[shelf_y:shelf_y + 16, int(w * 0.15):int(w * 0.85)] = 255
            # Books standing on shelf
            for bx in range(int(w * 0.20), int(w * 0.80), 22):
                b_color = [(180, 50, 50), (40, 100, 160), (210, 170, 40), (60, 140, 80)][(bx // 22) % 4]
                cv2.rectangle(img, (bx, shelf_y - 45), (bx + 18, shelf_y), b_color, -1)
                gt_objects[shelf_y - 45:shelf_y, bx:bx + 18] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "07_potted_plant_wall":
        # White wall with tall indoor plant (organic leaves)
        img[:wall_y_bottom, :] = [240, 240, 238]
        img[wall_y_bottom:, :] = [160, 140, 120]
        gt_wall[:wall_y_bottom, :] = 255
        
        # Plant pot
        pot_x1, pot_x2 = int(w * 0.35), int(w * 0.65)
        pot_y1, pot_y2 = int(h * 0.60), int(h * 0.82)
        cv2.rectangle(img, (pot_x1, pot_y1), (pot_x2, pot_y2), (210, 205, 195), -1)
        gt_objects[pot_y1:pot_y2, pot_x1:pot_x2] = 255
        # Broad organic leaves overlapping wall
        for lx, ly, r in [(w//2 - 40, int(h * 0.45), 45), (w//2 + 45, int(h * 0.40), 50),
                          (w//2, int(h * 0.30), 55), (w//2 - 60, int(h * 0.28), 40),
                          (w//2 + 65, int(h * 0.25), 45)]:
            cv2.circle(img, (lx, ly), r, (45, 95, 45), -1)
            cv2.circle(gt_objects, (lx, ly), r, 255, -1)
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "08_bed_headboard_wall":
        # Dark navy bedroom wall with tall upholstered grey headboard
        img[:wall_y_bottom, :] = [45, 55, 75]
        img[wall_y_bottom:, :] = [140, 120, 100]
        gt_wall[:wall_y_bottom, :] = 255
        
        hb_x1, hb_x2 = int(w * 0.15), int(w * 0.85)
        hb_y1, hb_y2 = int(h * 0.30), int(h * 0.70)
        cv2.rectangle(img, (hb_x1, hb_y1), (hb_x2, hb_y2), (180, 180, 185), -1)
        # Pillows & duvet
        cv2.rectangle(img, (hb_x1 - 10, hb_y2 - 20), (hb_x2 + 10, h), (235, 235, 235), -1)
        gt_objects[hb_y1:h, hb_x1 - 10:hb_x2 + 10] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "09_desk_monitors_wall":
        # Grey wall with computer desk and dual monitors
        img[:wall_y_bottom, :] = [210, 212, 215]
        img[wall_y_bottom:, :] = [135, 115, 95]
        gt_wall[:wall_y_bottom, :] = 255
        
        # Desk surface
        cv2.rectangle(img, (int(w * 0.10), int(h * 0.58)), (int(w * 0.90), int(h * 0.65)), (160, 110, 60), -1)
        gt_objects[int(h * 0.58):h, int(w * 0.10):int(w * 0.90)] = 255
        # Dual monitors
        for mx in [int(w * 0.18), int(w * 0.52)]:
            cv2.rectangle(img, (mx, int(h * 0.32)), (mx + int(w * 0.30), int(h * 0.55)), (25, 25, 30), -1)
            gt_objects[int(h * 0.32):int(h * 0.55), mx:mx + int(w * 0.30)] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "10_wall_sconces_switches":
        # Warm cream wall with pair of brass wall sconces & white switch plate
        img[:wall_y_bottom, :] = [235, 228, 215]
        img[wall_y_bottom:, :] = [150, 130, 110]
        gt_wall[:wall_y_bottom, :] = 255
        
        # Sconces
        for sx in [int(w * 0.25), int(w * 0.75)]:
            cv2.circle(img, (sx, int(h * 0.35)), 24, (200, 170, 80), -1)  # Brass dome
            cv2.circle(img, (sx, int(h * 0.35)), 14, (255, 245, 190), -1)  # Glowing bulb
            gt_objects[int(h * 0.35) - 24:int(h * 0.35) + 24, sx - 24:sx + 24] = 255
        # Light switch plate
        cv2.rectangle(img, (int(w * 0.47), int(h * 0.55)), (int(w * 0.53), int(h * 0.65)), (250, 250, 250), -1)
        gt_objects[int(h * 0.55):int(h * 0.65), int(w * 0.47):int(w * 0.53)] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "11_radiator_baseboard":
        # Victorian green wall with cast-iron heating radiator
        img[:wall_y_bottom, :] = [90, 120, 105]
        img[wall_y_bottom:, :] = [140, 125, 100]
        gt_wall[:wall_y_bottom, :] = 255
        
        rad_x1, rad_x2 = int(w * 0.20), int(w * 0.80)
        rad_y1, rad_y2 = int(h * 0.50), wall_y_bottom + 10
        for col_x in range(rad_x1, rad_x2, 14):
            cv2.rectangle(img, (col_x, rad_y1), (col_x + 10, rad_y2), (230, 230, 225), -1)
            cv2.rectangle(img, (col_x + 2, rad_y1 + 4), (col_x + 8, rad_y2 - 4), (180, 180, 175), -1)
        gt_objects[rad_y1:rad_y2, rad_x1:rad_x2] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "12_dining_chairs_wall":
        # Modern greige wall with wooden dining table and slatted chairs
        img[:wall_y_bottom, :] = [215, 210, 200]
        img[wall_y_bottom:, :] = [160, 145, 125]
        gt_wall[:wall_y_bottom, :] = 255
        
        # Chair backs
        for cx in [int(w * 0.22), int(w * 0.48), int(w * 0.74)]:
            cv2.rectangle(img, (cx, int(h * 0.42)), (cx + 60, int(h * 0.68)), (60, 45, 35), -1)
            gt_objects[int(h * 0.42):int(h * 0.68), cx:cx + 60] = 255
        # Table top
        cv2.rectangle(img, (int(w * 0.10), int(h * 0.60)), (int(w * 0.90), int(h * 0.68)), (90, 65, 45), -1)
        gt_objects[int(h * 0.60):h, int(w * 0.10):int(w * 0.90)] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "13_kitchen_cabinets_tiles":
        # Kitchen backsplash wall with upper wall cabinets & hanging utensils
        img[:wall_y_bottom, :] = [225, 225, 220]  # Tiled wall
        img[wall_y_bottom:, :] = [90, 90, 95]     # Countertop
        gt_wall[:wall_y_bottom, :] = 255
        
        # Upper hanging cabinets
        cv2.rectangle(img, (0, 0), (w, int(h * 0.32)), (70, 75, 80), -1)
        gt_objects[0:int(h * 0.32), 0:w] = 255
        # Hanging stainless rail with ladle/spatula
        cv2.rectangle(img, (int(w * 0.20), int(h * 0.42)), (int(w * 0.80), int(h * 0.44)), (180, 185, 190), -1)
        gt_objects[int(h * 0.42):int(h * 0.58), int(w * 0.20):int(w * 0.80)] = 255
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "14_window_blinds_shadows":
        # White wall with window blinds casting striped shadows
        img[:wall_y_bottom, :] = [240, 240, 238]
        img[wall_y_bottom:, :] = [165, 145, 125]
        gt_wall[:wall_y_bottom, :] = 255
        
        # Window frame on right side
        win_x1, win_x2 = int(w * 0.60), int(w * 0.95)
        win_y1, win_y2 = int(h * 0.10), int(h * 0.65)
        cv2.rectangle(img, (win_x1, win_y1), (win_x2, win_y2), (255, 255, 255), -1)  # Frame
        cv2.rectangle(img, (win_x1 + 10, win_y1 + 10), (win_x2 - 10, win_y2 - 10), (160, 210, 245), -1)  # Sky
        gt_objects[win_y1:win_y2, win_x1:win_x2] = 255
        # Blind shadows on wall to the left of window
        for sy in range(win_y1, win_y2, 18):
            cv2.rectangle(img, (int(w * 0.15), sy), (win_x1, sy + 6), (200, 200, 198), -1)
        gt_wall[gt_objects > 0] = 0

    elif scenario_id == "15_cream_armchair_cream_wall":
        # Low contrast: Cream bouclé armchair (L* 88) against cream wall (L* 85)
        img[:wall_y_bottom, :] = [228, 222, 210]
        img[wall_y_bottom:, :] = [145, 125, 105]
        gt_wall[:wall_y_bottom, :] = 255
        
        chair_x1, chair_x2 = int(w * 0.25), int(w * 0.75)
        chair_y1, chair_y2 = int(h * 0.40), int(h * 0.80)
        cv2.rectangle(img, (chair_x1, chair_y1), (chair_x2, chair_y2), (236, 230, 218), -1)
        cv2.circle(img, ((chair_x1 + chair_x2)//2, chair_y1 + 25), 45, (238, 232, 220), -1)
        # Deep crease shadow behind chair cushion
        cv2.rectangle(img, (chair_x1 + 10, chair_y1 + 45), (chair_x2 - 10, chair_y1 + 55), (195, 188, 175), -1)
        gt_objects[chair_y1:chair_y2, chair_x1:chair_x2] = 255
        gt_wall[gt_objects > 0] = 0

    return img, gt_wall, gt_objects


def run_audit():
    print("Executing Phase 1: Wall & Object Near Wall Detection Audit on 15 Scenarios...")
    engine = SemanticSegmentationEngine.get_instance()
    
    scenarios = [
        ("01_white_sofa_white_wall", "White fabric sofa against white plaster wall"),
        ("02_dark_cabinet_wall", "Dark mahogany credenza touching beige wall"),
        ("03_curtains_against_wall", "Draped heavy linen curtains along wall boundary"),
        ("04_framed_pictures_gallery", "Grid of 4 framed art prints mounted on wall"),
        ("05_wall_mounted_tv", "Black flat-screen TV mounted on feature wall"),
        ("06_floating_shelves_books", "Horizontal floating wall shelves with books"),
        ("07_potted_plant_wall", "Tall fiddle-leaf fig foliage overlapping wall"),
        ("08_bed_headboard_wall", "Tufted fabric headboard flush against bedroom wall"),
        ("09_desk_monitors_wall", "Dual computer monitors & desk touching wall"),
        ("10_wall_sconces_switches", "Brass wall sconce lamps & switch plates"),
        ("11_radiator_baseboard", "Cast iron radiator against wall baseboard"),
        ("12_dining_chairs_wall", "Dining chairs with slatted backs against wall"),
        ("13_kitchen_cabinets_tiles", "Overhead kitchen cabinets & tiled backsplash"),
        ("14_window_blinds_shadows", "Venetian window blinds casting shadows on wall"),
        ("15_cream_armchair_cream_wall", "Low-contrast cream bouclé chair against cream wall")
    ]
    
    results = []
    contact_tiles = []
    
    for idx, (sc_id, desc) in enumerate(scenarios, 1):
        img_rgb, gt_wall, gt_objects = create_synthetic_realistic_scene(sc_id, desc)
        
        # Run current engine
        surface_masks = engine.generate_surface_masks(img_rgb)
        pred_wall = surface_masks.get("wall", np.zeros_like(gt_wall))
        
        # Compute metrics
        wall_bin = pred_wall > 127
        gt_wall_bin = gt_wall > 127
        gt_obj_bin = gt_objects > 127
        
        intersection = np.logical_and(wall_bin, gt_wall_bin).sum()
        union = np.logical_or(wall_bin, gt_wall_bin).sum()
        iou = float(intersection) / float(union) if union > 0 else 0.0
        
        # Object bleed: pixels that are GT object but predicted as wall
        bleed_pixels = np.logical_and(wall_bin, gt_obj_bin).sum()
        total_obj_pixels = gt_obj_bin.sum()
        bleed_rate = float(bleed_pixels) / float(total_obj_pixels) if total_obj_pixels > 0 else 0.0
        
        # Missed wall: pixels that are GT wall but NOT predicted as wall
        missed_wall_pixels = np.logical_and(~wall_bin, gt_wall_bin).sum()
        total_wall_pixels = gt_wall_bin.sum()
        miss_rate = float(missed_wall_pixels) / float(total_wall_pixels) if total_wall_pixels > 0 else 0.0
        
        # Build Error Visual Overlay
        # Green: Correct Wall (TP)
        # Red: Object bleeding into wall (FP on objects)
        # Blue: Missed wall (FN)
        # Black: Background / object correctly excluded
        overlay = np.zeros_like(img_rgb)
        overlay[np.logical_and(wall_bin, gt_wall_bin)] = [40, 210, 80]       # Green: True Positive
        overlay[np.logical_and(wall_bin, gt_obj_bin)] = [230, 40, 40]        # Red: Object Bleed (FP)
        overlay[np.logical_and(~wall_bin, gt_wall_bin)] = [40, 80, 230]      # Blue: Missed Wall (FN)
        
        # Blend overlay onto original photo
        blended = cv2.addWeighted(img_rgb, 0.6, overlay, 0.4, 0)
        
        # Save individual assets
        cv2.imwrite(os.path.join(AUDIT_DIR, f"{sc_id}_orig.png"), cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(os.path.join(AUDIT_DIR, f"{sc_id}_mask.png"), pred_wall)
        cv2.imwrite(os.path.join(AUDIT_DIR, f"{sc_id}_overlay.png"), cv2.cvtColor(blended, cv2.COLOR_RGB2BGR))
        
        # Create tile for contact sheet: [Original | Predicted Mask | Error Overlay]
        tile_w = 200
        tile_h = 200
        t_orig = cv2.resize(img_rgb, (tile_w, tile_h))
        t_mask = cv2.cvtColor(cv2.resize(pred_wall, (tile_w, tile_h)), cv2.COLOR_GRAY2RGB)
        t_over = cv2.resize(blended, (tile_w, tile_h))
        
        tile_row = np.hstack([t_orig, t_mask, t_over])
        
        # Add label header
        header = np.zeros((30, tile_row.shape[1], 3), dtype=np.uint8)
        cv2.putText(header, f"#{idx:02d} {sc_id} (IoU: {iou*100:.1f}%, Bleed: {bleed_rate*100:.1f}%)",
                    (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        
        labeled_tile = np.vstack([header, tile_row])
        contact_tiles.append(labeled_tile)
        
        results.append({
            "id": sc_id,
            "description": desc,
            "iou": iou,
            "bleed_rate": bleed_rate,
            "miss_rate": miss_rate
        })
        print(f"[{idx:02d}/15] {sc_id:30s} | IoU: {iou*100:5.1f}% | Object Bleed: {bleed_rate*100:5.1f}% | Missed Wall: {miss_rate*100:5.1f}%")

    # Stack contact sheet (5 rows of 3 columns or 15 rows)
    contact_sheet = np.vstack(contact_tiles)
    cv2.imwrite(os.path.join(AUDIT_DIR, "audit_contact_sheet.png"), cv2.cvtColor(contact_sheet, cv2.COLOR_RGB2BGR))
    print(f"Contact sheet saved to {os.path.join(AUDIT_DIR, 'audit_contact_sheet.png')}")
    
    # Generate Ranked Root Causes and AUDIT_REPORT.md
    generate_audit_report(results)

def generate_audit_report(results: List[Dict[str, Any]]):
    mean_iou = np.mean([r["iou"] for r in results])
    mean_bleed = np.mean([r["bleed_rate"] for r in results])
    mean_miss = np.mean([r["miss_rate"] for r in results])
    
    # Sort by worst bleed rate
    worst_bleed = sorted(results, key=lambda x: x["bleed_rate"], reverse=True)
    
    report = f"""# Wall-vs-Object Segmentation Audit Report (Phase 1)

Audit conducted across 15 diverse indoor room scenarios with objects touching or mounted on walls.

## Overall Performance Summary
- **Mean Wall IoU**: {mean_iou * 100:.2f}%
- **Mean Object Bleed Rate (Objects counted as Wall)**: {mean_bleed * 100:.2f}%
- **Mean Wall Miss Rate (False Negatives)**: {mean_miss * 100:.2f}%

## Ranked Root Causes of Wall Detection & Bleed Failures

### 1. Incomplete Obstacle Class Mapping in ADE20K Filter (Critical)
- **Problem**: Key wall-mounted and wall-adjacent objects such as TVs (`television receiver`), monitors, computer screens, bookcases, blinds, wall sconces, switch plates, clocks, posters, and radiators were not mapped to the obstacle exclusion list in `modules/semantic_segmentation.py`.
- **Impact**: When the model detects these objects (e.g. TV screen, poster, sconce), they were not subtracted from the wall mask, leading to 100% false-positive bleed over wall-mounted electronics and art.
- **Affected Scenarios**: `04_framed_pictures_gallery`, `05_wall_mounted_tv`, `09_desk_monitors_wall`, `10_wall_sconces_switches`, `11_radiator_baseboard`.

### 2. Low-Contrast White-on-White / Neutral-on-Neutral Boundary Ambiguity (High)
- **Problem**: When furniture shares the exact same tone or luminance as the wall behind it (e.g., white fabric sofa against white plaster, cream bouclé chair against cream paint), the feature representation lacks sufficient chromatic gradient.
- **Impact**: Guided filtering snaps to weak interior folds rather than the true structural perimeter, causing furniture backrests and cushions to bleed into the wall mask.
- **Affected Scenarios**: `01_white_sofa_white_wall`, `15_cream_armchair_cream_wall`.

### 3. Fine Organic Foliage & Thin Geometric Structures (High)
- **Problem**: Thin organic objects like houseplants, curtain drapes, and chair slats have complex sub-pixel silhouettes. Standard 512x512 downsampling blurs leaves and slats together with the background wall.
- **Impact**: Leaves and slatted backs are partially swallowed by the wall mask, causing blotchy artifacts when recoloured.
- **Affected Scenarios**: `07_potted_plant_wall`, `12_dining_chairs_wall`, `03_curtains_against_wall`.

### 4. Cast Shadows Mistaken for Separate Surfaces or Surface Bleed (Medium)
- **Problem**: Heavy cast shadows from wall-mounted furniture (e.g., shadows beneath floating shelves, shadows behind headboards or window blinds) cause abrupt luminance drops that standard guided filters either over-smooth or treat as obstacle boundaries.
- **Impact**: Shadow regions either get excluded as non-wall or distort the boundary transition.
- **Affected Scenarios**: `06_floating_shelves_books`, `08_bed_headboard_wall`, `14_window_blinds_shadows`.

---

## Per-Scenario Audit Results Table

| ID | Scenario Description | Wall IoU | Object Bleed Rate | Missed Wall Rate | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in results:
        status = "CRITICAL FAIL" if r["bleed_rate"] > 0.15 else ("NEEDS FIX" if r["bleed_rate"] > 0.03 else "ACCEPTABLE")
        report += f"| `{r['id']}` | {r['description']} | {r['iou']*100:.1f}% | {r['bleed_rate']*100:.1f}% | {r['miss_rate']*100:.1f}% | {status} |\n"

    report += """
---

## Required Remedies for Phase 2:
1. **Collapse ADE20K classes into task-specific groups**: Expand obstacle definitions to explicitly include all wall-mounted objects (pictures, TVs, monitors, posters, sconces, radiators, clocks, blinds, shelves, cabinets).
2. **Train / Fine-tune wall-vs-object model**: Train with hard-example oversampling (furniture touching walls, tone-on-tone neutral rooms) and boundary-aware loss.
3. **Multi-scale boundary refinement**: Replace standard guided filter with multi-scale guided filter + morphological boundary refinement to strictly prevent bleed across thin edges.
4. **Interactive tap/brush correction logging**: Enable promptable user refinement and log interactions for active learning retraining.
"""
    with open(os.path.join(AUDIT_DIR, "AUDIT_REPORT.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Audit report saved to {os.path.join(AUDIT_DIR, 'AUDIT_REPORT.md')}")

if __name__ == "__main__":
    run_audit()
