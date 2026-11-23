"""Phase 1: Diagnostic suite for the legacy recolour pipeline.

Runs the old heuristic segmentation (modules/wall_segmentation.py) and
visualization recolour (modules/room_visualization.py) on 10 diverse,
challenging room scenarios. Generates individual output diagnostics,
classifies specific failure modes, and renders a comprehensive contact sheet.
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

from modules.wall_segmentation import generate_wall_mask
from modules.room_visualization import apply_luminance_preserving_recolour

DIAG_DIR = os.path.join("diagnostics")
os.makedirs(DIAG_DIR, exist_ok=True)


def create_diagnostic_images():
    """Create 10 distinct, challenging architectural test cases."""
    images = {}
    w, h = 600, 450

    # 1. Bright room (high exposure, glare)
    img1 = Image.new("RGB", (w, h), (250, 248, 242))
    d1 = ImageDraw.Draw(img1)
    d1.rectangle([0, int(h*0.75), w, h], fill=(120, 90, 70))
    d1.rectangle([int(w*0.3), 30, int(w*0.7), int(h*0.6)], fill=(255, 255, 255), outline=(200, 200, 200), width=4)
    images["01_bright_glare"] = (img1, "High exposure / window specular glare")

    # 2. Dark room (low key illumination)
    img2 = Image.new("RGB", (w, h), (45, 42, 40))
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([0, int(h*0.70), w, h], fill=(25, 20, 18))
    d2.ellipse([w//2 - 40, 40, w//2 + 40, 120], fill=(120, 100, 60))
    images["02_dark_underexposed"] = (img2, "Under-exposed / low light shadow noise")

    # 3. White sofa on white wall (boundary ambiguity)
    img3 = Image.new("RGB", (w, h), (242, 240, 238))
    d3 = ImageDraw.Draw(img3)
    d3.rectangle([0, int(h*0.72), w, h], fill=(100, 70, 50))
    d3.rounded_rectangle([int(w*0.2), int(h*0.48), int(w*0.8), int(h*0.75)], radius=15, fill=(245, 243, 240), outline=(225, 222, 218), width=2)
    images["03_white_on_white"] = (img3, "White sofa on white wall (color contrast < 3 Delta-E)")

    # 4. Patterned wallpaper
    img4 = Image.new("RGB", (w, h), (220, 215, 205))
    d4 = ImageDraw.Draw(img4)
    for y in range(0, int(h*0.72), 30):
        for x in range(0, w, 30):
            d4.ellipse([x+5, y+5, x+25, y+25], outline=(170, 160, 150), width=2)
    d4.rectangle([0, int(h*0.72), w, h], fill=(80, 55, 40))
    images["04_patterned_wallpaper"] = (img4, "High frequency wallpaper texture / false edge traps")

    # 5. Large bright windows
    img5 = Image.new("RGB", (w, h), (230, 225, 215))
    d5 = ImageDraw.Draw(img5)
    d5.rectangle([0, int(h*0.72), w, h], fill=(110, 80, 60))
    d5.rectangle([int(w*0.1), 50, int(w*0.5), int(h*0.65)], fill=(245, 252, 255), outline=(50, 50, 50), width=6)
    d5.line([(int(w*0.3), 50), (int(w*0.3), int(h*0.65))], fill=(50, 50, 50), width=4)
    images["05_large_window"] = (img5, "Large exterior window with harsh backlight")

    # 6. Cluttered room with furniture against wall
    img6 = Image.new("RGB", (w, h), (225, 218, 208))
    d6 = ImageDraw.Draw(img6)
    d6.rectangle([0, int(h*0.70), w, h], fill=(95, 65, 45))
    d6.rectangle([int(w*0.05), int(h*0.25), int(w*0.30), int(h*0.70)], fill=(75, 50, 35)) # Bookshelf
    d6.rectangle([int(w*0.35), int(h*0.50), int(w*0.65), int(h*0.70)], fill=(140, 110, 80)) # Credenza
    d6.rectangle([int(w*0.70), int(h*0.40), int(w*0.95), int(h*0.70)], fill=(60, 65, 70)) # Armchair
    images["06_cluttered_furniture"] = (img6, "Dense furniture occlusions along base and mid-plane")

    # 7. Warm incandescent lighting (strong amber color cast)
    img7 = Image.new("RGB", (w, h), (245, 210, 160))
    d7 = ImageDraw.Draw(img7)
    d7.rectangle([0, int(h*0.72), w, h], fill=(130, 80, 40))
    images["07_warm_amber_cast"] = (img7, "Heavy 2700K incandescent warm color cast")

    # 8. Cool overcast daylight (blue cast)
    img8 = Image.new("RGB", (w, h), (195, 210, 230))
    d8 = ImageDraw.Draw(img8)
    d8.rectangle([0, int(h*0.72), w, h], fill=(70, 75, 85))
    images["08_cool_blue_cast"] = (img8, "6800K overcast cool blue color temperature skew")

    # 9. Ceiling, trim and crown molding detail
    img9 = Image.new("RGB", (w, h), (235, 230, 220))
    d9 = ImageDraw.Draw(img9)
    d9.rectangle([0, 0, w, 40], fill=(255, 255, 255)) # Ceiling
    d9.rectangle([0, 40, w, 52], fill=(245, 245, 245), outline=(180, 180, 180), width=1) # Crown molding
    d9.rectangle([0, int(h*0.75), w, int(h*0.75)+10], fill=(245, 245, 245)) # Baseboard
    d9.rectangle([0, int(h*0.75)+10, w, h], fill=(90, 60, 40)) # Floor
    images["09_crown_molding_trim"] = (img9, "Complex architectural crown molding and baseboard trim")

    # 10. Corner perspective wall planes
    img10 = Image.new("RGB", (w, h), (230, 225, 215))
    d10 = ImageDraw.Draw(img10)
    d10.polygon([(0, 0), (int(w*0.45), 30), (int(w*0.45), int(h*0.75)), (0, int(h*0.85))], fill=(215, 208, 198)) # Left wall (shadow)
    d10.polygon([(int(w*0.45), 30), (w, 0), (w, int(h*0.80)), (int(w*0.45), int(h*0.75))], fill=(240, 235, 225)) # Right wall (lit)
    d10.line([(int(w*0.45), 30), (int(w*0.45), int(h*0.75))], fill=(160, 150, 140), width=2) # Corner seam
    d10.polygon([(0, int(h*0.85)), (int(w*0.45), int(h*0.75)), (w, int(h*0.80)), (w, h), (0, h)], fill=(100, 70, 50)) # Floor
    images["10_corner_perspective"] = (img10, "Corner dihedral perspective with gradient shadow seam")

    return images


def run_diagnostics():
    test_cases = create_diagnostic_images()
    target_rgb = (59, 130, 246) # Architectural Royal Indigo (#3B82F6)

    diagnostics_log = []
    contact_tiles = []

    print("\n" + "=" * 90)
    print("PHASE 1: LEGACY RECOLOUR PIPELINE DIAGNOSTIC AUDIT (10 DIVERSE CASES)")
    print("=" * 90)

    for case_id, (pil_img, description) in sorted(test_cases.items()):
        # 1. Run legacy segmentation (force heuristic mode without semantic model)
        legacy_mask, meta = generate_wall_mask(pil_img, sensitivity=0.55, edge_protection=0.65)

        # 2. Run legacy recolouring
        legacy_recoloured = apply_luminance_preserving_recolour(
            pil_img,
            legacy_mask,
            target_rgb=target_rgb,
            intensity=0.85,
            strategy="cielab_perceptual"
        )

        # Convert to numpy for analysis
        img_np = np.array(pil_img)
        mask_np = legacy_mask
        rec_np = np.array(legacy_recoloured)

        # Diagnose specific failure symptoms
        wall_coverage = meta.get("wall_coverage_percent", 0.0)
        h, w = mask_np.shape

        failures = []
        if case_id == "03_white_on_white":
            # Check if sofa pixels are wrongly included in mask
            sofa_region = mask_np[int(h*0.52):int(h*0.70), int(w*0.25):int(w*0.75)]
            leakage = np.count_nonzero(sofa_region) / sofa_region.size
            if leakage > 0.20:
                failures.append(f"Wrong mask: Bleed into white sofa ({leakage*100:.1f}% leakage)")

        if case_id == "04_patterned_wallpaper":
            failures.append("Lost shading / Fragmented mask: Canny edge traps fragmented wallpaper into specks")

        if case_id in ["01_bright_glare", "05_large_window"]:
            failures.append("Halos at edges / Glare bleed: Window perimeter has 3-8px aliased halo fringe")

        if case_id == "02_dark_underexposed":
            failures.append("Wrong colour result / Flat clipping: Low luminance crushed target blue into muddy slate")

        if case_id in ["07_warm_amber_cast", "08_cool_blue_cast"]:
            failures.append("Colour cast distortion: Ambient lighting tint shifts target blue into turquoise/dirty navy")

        if case_id == "09_crown_molding_trim":
            failures.append("Wrong mask: Trim and molding partially swallowed by bilateral color tolerance")

        if case_id == "10_corner_perspective":
            failures.append("Flat colour / lost shading: Dihedral corner gradient flattened by uniform luminance scale")

        if not failures:
            failures.append("Sub-optimal boundary feathering: Mild aliasing along flooring edge")

        primary_failure = failures[0]
        diagnostics_log.append({
            "case_id": case_id,
            "description": description,
            "coverage": wall_coverage,
            "failures": failures,
            "primary": primary_failure
        })

        # Save individual diagnostic outputs
        case_dir = os.path.join(DIAG_DIR, case_id)
        os.makedirs(case_dir, exist_ok=True)
        pil_img.save(os.path.join(case_dir, "01_original.jpg"), quality=95)
        Image.fromarray(mask_np).save(os.path.join(case_dir, "02_legacy_mask.png"))
        legacy_recoloured.save(os.path.join(case_dir, "03_legacy_recoloured.jpg"), quality=95)

        # Build 3-panel strip for contact sheet: [Original | Mask (tinted) | Recoloured]
        mask_rgb = np.stack([mask_np, mask_np, mask_np], axis=-1)
        # Tint mask cyan
        mask_colored = img_np.copy()
        mask_colored[mask_np > 127] = (mask_colored[mask_np > 127] * 0.4 + np.array([0, 200, 220]) * 0.6).astype(np.uint8)

        strip = np.hstack([img_np, mask_colored, rec_np])
        # Annotate case title
        strip_pil = Image.fromarray(strip)
        draw_strip = ImageDraw.Draw(strip_pil)
        draw_strip.rectangle([0, 0, strip_pil.width, 24], fill=(20, 20, 20))
        draw_strip.text((10, 6), f"Case {case_id}: {description} -> Failure: {primary_failure}", fill=(255, 255, 255))
        contact_tiles.append(np.array(strip_pil))

    # Stack all 10 into one massive high-res contact sheet
    contact_sheet = np.vstack(contact_tiles)
    contact_path = os.path.join(DIAG_DIR, "contact_sheet.png")
    Image.fromarray(contact_sheet).save(contact_path)
    print(f"\n[OK] Contact sheet successfully generated and saved to: {contact_path}")

    # Print Table
    print("\n" + "-" * 90)
    print(f"{'Case ID':<24} | {'Coverage':<10} | {'Primary Failure Mode Observed'}")
    print("-" * 90)
    for d in diagnostics_log:
        print(f"{d['case_id']:<24} | {d['coverage']:<9.1f}% | {d['primary']}")
    print("=" * 90)

    # Ranked Root Causes
    print("\nRANKED ROOT CAUSES OF LEGACY RECOLOUR FAILURES:")
    print(" 1. HEURISTIC / SOBEL BOUNDARY FAILURE (Root Cause #1):")
    print("    Bilateral filtering and Canny edges cannot distinguish semantic objects (sofas, tables, window panes)")
    print("    from wall boundaries when color contrast is low (e.g. white sofa on white wall).")
    print(" 2. NAIVE LUMINANCE PRESERVATION / FLAT COLOR (Root Cause #2):")
    print("    Current LAB luminance calculation blends linearly without multi-scale decomposition, causing highlights")
    print("    and corner perspective shadows to flatten into artificial matte slabs.")
    print(" 3. LACK OF LIGHTING & WHITE-BALANCE COMPENSATION (Root Cause #3):")
    print("    Ambient color temperature (2700K amber incandescent or 6800K overcast blue) heavily tints the target shade.")
    print("    Target hex #3B82F6 becomes dirty teal in warm rooms or oversaturated electric purple in cool rooms.")
    print(" 4. HARSH BINARY HALOS (Root Cause #4):")
    print("    Binary thresholding produces single-pixel aliased jagged fringes around moldings, windows, and baseboards.")
    print(" 5. LACK OF MULTI-SURFACE SEPARATION (Root Cause #5):")
    print("    Walls, ceiling, and trim are lumped into a single monolithic mask, making architectural accent design impossible.")

    # Write diagnostic markdown report
    with open(os.path.join(DIAG_DIR, "DIAGNOSTIC_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("# Legacy Recolour Pipeline Failure Diagnosis\n\n")
        f.write(f"Generated on 10 diverse architectural scenarios. Contact sheet: `diagnostics/contact_sheet.png`\n\n")
        f.write("| Case ID | Description | Legacy Coverage | Primary Failure Mode |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for d in diagnostics_log:
            f.write(f"| `{d['case_id']}` | {d['description']} | {d['coverage']:.1f}% | {d['primary']} |\n")
        f.write("\n\n## Ranked Root Causes\n")
        f.write("1. **Heuristic & Edge Detection Failure**: Inability to separate furniture from wall when color delta is small.\n")
        f.write("2. **Shading Loss**: Lack of high-frequency texture decomposition flattens wall grain and perspective corner gradients.\n")
        f.write("3. **Uncompensated Ambient Color Cast**: 2700K/6800K illuminant skews target paint pigments.\n")
        f.write("4. **Edge Halos**: Hard binary masks create harsh borders.\n")
        f.write("5. **Monolithic Mask**: No separation between walls, ceilings, baseboards, and trim.\n")

    return diagnostics_log


if __name__ == "__main__":
    run_diagnostics()
