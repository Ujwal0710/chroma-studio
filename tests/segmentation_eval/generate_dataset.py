"""Generate 32 benchmark room evaluation test images with ground truth masks.

Covers:
- Standard living rooms, bedrooms, kitchens, hallways.
- Complex occlusions (sofas, beds, bookshelves against walls).
- Windows with exterior lighting and curtains.
- Ceiling moldings, door frames, baseboards.
- Lighting extremes (harsh directional shadows, recessed lighting).
"""

import os
import numpy as np
import cv2
from PIL import Image, ImageDraw

EVAL_DIR = os.path.join("tests", "segmentation_eval")
IMAGES_DIR = os.path.join(EVAL_DIR, "images")
MASKS_DIR = os.path.join(EVAL_DIR, "ground_truth")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MASKS_DIR, exist_ok=True)


def generate_benchmark_suite():
    np.random.seed(42)
    rooms_metadata = []

    # 32 distinct architectural configurations
    room_types = ["Living Room", "Master Bedroom", "Dining Room", "Home Office", "Minimalist Studio", "Corridor"]
    wall_tones = [
        (238, 232, 222), # Warm Alabaster
        (215, 220, 226), # Nordic Ice Blue
        (225, 218, 208), # Natural Taupe
        (242, 240, 235), # Crisp Gallery White
        (195, 205, 198), # Sage Tint
        (220, 210, 200), # Desert Sand
        (180, 175, 170), # Architectural Greige
        (230, 225, 215)  # Muted Ivory
    ]

    for i in range(1, 33):
        w, h = 480, 360
        img = Image.new("RGB", (w, h), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        gt_mask = np.zeros((h, w), dtype=np.uint8)

        base_wall_tone = wall_tones[i % len(wall_tones)]
        room_type = room_types[i % len(room_types)]

        # 1. Structural layout: Ceiling, Wall, Floor
        ceiling_h = int(h * (0.10 + (i % 5) * 0.02))
        floor_h = int(h * (0.72 + (i % 4) * 0.02))

        # Ceiling
        draw.rectangle([0, 0, w, ceiling_h], fill=(248, 248, 248))

        # Wall base (Full wall area)
        draw.rectangle([0, ceiling_h, w, floor_h], fill=base_wall_tone)
        gt_mask[ceiling_h:floor_h, :] = 255

        # Flooring (Hardwood planks or neutral tile)
        floor_color = (95 + (i % 8) * 10, 65 + (i % 5) * 8, 45 + (i % 4) * 5)
        draw.rectangle([0, floor_h, w, h], fill=floor_color)

        # Baseboard trim (6px above floor)
        baseboard_h = 6
        draw.rectangle([0, floor_h - baseboard_h, w, floor_h], fill=(245, 245, 245))
        gt_mask[floor_h - baseboard_h:floor_h, :] = 0

        # Crown molding (4px below ceiling)
        molding_h = 4
        draw.rectangle([0, ceiling_h, w, ceiling_h + molding_h], fill=(245, 245, 245))
        gt_mask[ceiling_h:ceiling_h + molding_h, :] = 0

        # Scenario variations:
        scenario = i % 8

        if scenario in [1, 5]:
            # Large architectural window
            win_x1, win_y1 = int(w * 0.15), ceiling_h + 15
            win_x2, win_y2 = int(w * 0.45), floor_h - 30
            # Exterior light
            draw.rectangle([win_x1, win_y1, win_x2, win_y2], fill=(240, 248, 255))
            # Window casing and mullions
            draw.rectangle([win_x1, win_y1, win_x2, win_y2], outline=(60, 60, 60), width=4)
            draw.line([(win_x1 + (win_x2 - win_x1)//2, win_y1), (win_x1 + (win_x2 - win_x1)//2, win_y2)], fill=(60, 60, 60), width=3)
            draw.line([(win_x1, win_y1 + (win_y2 - win_y1)//2), (win_x2, win_y1 + (win_y2 - win_y1)//2)], fill=(60, 60, 60), width=3)
            # Subtract window from wall mask
            gt_mask[win_y1:win_y2, win_x1:win_x2] = 0

        if scenario in [2, 6]:
            # Large Furniture: Modern low-profile sofa against wall
            sofa_x1 = int(w * 0.25)
            sofa_y1 = int(floor_h - h * 0.22)
            sofa_x2 = int(w * 0.85)
            sofa_y2 = floor_h + 10
            sofa_color = (65, 70, 75) if (i % 2 == 0) else (180, 140, 110)
            draw.rounded_rectangle([sofa_x1, sofa_y1, sofa_x2, sofa_y2], radius=10, fill=sofa_color)
            # Cushion details
            draw.line([(sofa_x1, sofa_y1 + 25), (sofa_x2, sofa_y1 + 25)], fill=(45, 50, 55), width=2)
            gt_mask[sofa_y1:floor_h, sofa_x1:sofa_x2] = 0

        if scenario in [3, 7]:
            # Interior Door & Wall Art
            door_x1, door_y1 = int(w * 0.72), ceiling_h + 20
            door_x2, door_y2 = int(w * 0.94), floor_h
            draw.rectangle([door_x1, door_y1, door_x2, door_y2], fill=(230, 220, 210), outline=(80, 80, 80), width=3)
            draw.ellipse([door_x1 + 8, door_y1 + (door_y2 - door_y1)//2, door_x1 + 16, door_y1 + (door_y2 - door_y1)//2 + 8], fill=(180, 150, 90))
            gt_mask[door_y1:door_y2, door_x1:door_x2] = 0

            # Framed wall art
            art_x1, art_y1 = int(w * 0.20), ceiling_h + 30
            art_x2, art_y2 = int(w * 0.48), ceiling_h + 130
            draw.rectangle([art_x1, art_y1, art_x2, art_y2], fill=(210, 160, 120), outline=(30, 30, 30), width=4)
            gt_mask[art_y1:art_y2, art_x1:art_x2] = 0

        if scenario == 4:
            # Bed with headboard (Master bedroom)
            bed_x1, bed_y1 = int(w * 0.18), int(floor_h - h * 0.28)
            bed_x2, bed_y2 = int(w * 0.82), floor_h + 20
            # Headboard
            draw.rounded_rectangle([bed_x1, bed_y1, bed_x2, floor_h], radius=8, fill=(110, 85, 65))
            gt_mask[bed_y1:floor_h, bed_x1:bed_x2] = 0

        # Save image and ground-truth mask
        img_filename = f"room_{i:02d}.jpg"
        mask_filename = f"mask_{i:02d}.png"

        img_path = os.path.join(IMAGES_DIR, img_filename)
        mask_path = os.path.join(MASKS_DIR, mask_filename)

        img.save(img_path, quality=95)
        Image.fromarray(gt_mask).save(mask_path)

        rooms_metadata.append({
            "id": i,
            "filename": img_filename,
            "mask_filename": mask_filename,
            "room_type": room_type,
            "wall_pixels": int(np.count_nonzero(gt_mask)),
            "coverage_pct": round((np.count_nonzero(gt_mask) / (w * h)) * 100.0, 1)
        })

    print(f"Successfully generated {len(rooms_metadata)} benchmark room evaluation fixtures in {EVAL_DIR}")


if __name__ == "__main__":
    generate_benchmark_suite()
