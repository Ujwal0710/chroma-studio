# Wall-vs-Object Segmentation Audit Report (Phase 1)

Audit conducted across 15 diverse indoor room scenarios with objects touching or mounted on walls.

## Overall Performance Summary
- **Mean Wall IoU**: 38.53%
- **Mean Object Bleed Rate (Objects counted as Wall)**: 29.30%
- **Mean Wall Miss Rate (False Negatives)**: 41.04%

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
| `01_white_sofa_white_wall` | White fabric sofa against white plaster wall | 65.9% | 30.1% | 0.0% | CRITICAL FAIL |
| `02_dark_cabinet_wall` | Dark mahogany credenza touching beige wall | 67.0% | 10.1% | 4.9% | NEEDS FIX |
| `03_curtains_against_wall` | Draped heavy linen curtains along wall boundary | 0.1% | 92.9% | 99.8% | CRITICAL FAIL |
| `04_framed_pictures_gallery` | Grid of 4 framed art prints mounted on wall | 55.7% | 0.0% | 8.9% | ACCEPTABLE |
| `05_wall_mounted_tv` | Black flat-screen TV mounted on feature wall | 63.5% | 3.6% | 0.3% | NEEDS FIX |
| `06_floating_shelves_books` | Horizontal floating wall shelves with books | 62.6% | 24.0% | 4.1% | CRITICAL FAIL |
| `07_potted_plant_wall` | Tall fiddle-leaf fig foliage overlapping wall | 61.1% | 62.2% | 0.3% | CRITICAL FAIL |
| `08_bed_headboard_wall` | Tufted fabric headboard flush against bedroom wall | 0.0% | 0.0% | 100.0% | ACCEPTABLE |
| `09_desk_monitors_wall` | Dual computer monitors & desk touching wall | 53.5% | 71.7% | 1.2% | CRITICAL FAIL |
| `10_wall_sconces_switches` | Brass wall sconce lamps & switch plates | 72.5% | 38.2% | 0.0% | CRITICAL FAIL |
| `11_radiator_baseboard` | Cast iron radiator against wall baseboard | 0.0% | 0.0% | 100.0% | ACCEPTABLE |
| `12_dining_chairs_wall` | Dining chairs with slatted backs against wall | 0.0% | 1.1% | 100.0% | ACCEPTABLE |
| `13_kitchen_cabinets_tiles` | Overhead kitchen cabinets & tiled backsplash | 34.0% | 7.0% | 61.4% | NEEDS FIX |
| `14_window_blinds_shadows` | Venetian window blinds casting shadows on wall | 34.3% | 9.6% | 46.2% | NEEDS FIX |
| `15_cream_armchair_cream_wall` | Low-contrast cream bouclé chair against cream wall | 7.7% | 88.9% | 88.5% | CRITICAL FAIL |

---

## Required Remedies for Phase 2:
1. **Collapse ADE20K classes into task-specific groups**: Expand obstacle definitions to explicitly include all wall-mounted objects (pictures, TVs, monitors, posters, sconces, radiators, clocks, blinds, shelves, cabinets).
2. **Train / Fine-tune wall-vs-object model**: Train with hard-example oversampling (furniture touching walls, tone-on-tone neutral rooms) and boundary-aware loss.
3. **Multi-scale boundary refinement**: Replace standard guided filter with multi-scale guided filter + morphological boundary refinement to strictly prevent bleed across thin edges.
4. **Interactive tap/brush correction logging**: Enable promptable user refinement and log interactions for active learning retraining.
