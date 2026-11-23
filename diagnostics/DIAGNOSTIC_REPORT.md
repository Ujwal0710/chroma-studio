# Legacy Recolour Pipeline Failure Diagnosis

Generated on 10 diverse architectural scenarios. Contact sheet: `diagnostics/contact_sheet.png`

| Case ID | Description | Legacy Coverage | Primary Failure Mode |
| :--- | :--- | :--- | :--- |
| `01_bright_glare` | High exposure / window specular glare | 0.0% | Halos at edges / Glare bleed: Window perimeter has 3-8px aliased halo fringe |
| `02_dark_underexposed` | Under-exposed / low light shadow noise | 1.7% | Wrong colour result / Flat clipping: Low luminance crushed target blue into muddy slate |
| `03_white_on_white` | White sofa on white wall (color contrast < 3 Delta-E) | 72.7% | Wrong mask: Bleed into white sofa (100.0% leakage) |
| `04_patterned_wallpaper` | High frequency wallpaper texture / false edge traps | 67.8% | Lost shading / Fragmented mask: Canny edge traps fragmented wallpaper into specks |
| `05_large_window` | Large exterior window with harsh backlight | 45.1% | Halos at edges / Glare bleed: Window perimeter has 3-8px aliased halo fringe |
| `06_cluttered_furniture` | Dense furniture occlusions along base and mid-plane | 63.8% | Sub-optimal boundary feathering: Mild aliasing along flooring edge |
| `07_warm_amber_cast` | Heavy 2700K incandescent warm color cast | 71.6% | Colour cast distortion: Ambient lighting tint shifts target blue into turquoise/dirty navy |
| `08_cool_blue_cast` | 6800K overcast cool blue color temperature skew | 71.6% | Colour cast distortion: Ambient lighting tint shifts target blue into turquoise/dirty navy |
| `09_crown_molding_trim` | Complex architectural crown molding and baseboard trim | 61.3% | Wrong mask: Trim and molding partially swallowed by bilateral color tolerance |
| `10_corner_perspective` | Corner dihedral perspective with gradient shadow seam | 73.6% | Flat colour / lost shading: Dihedral corner gradient flattened by uniform luminance scale |


## Ranked Root Causes
1. **Heuristic & Edge Detection Failure**: Inability to separate furniture from wall when color delta is small.
2. **Shading Loss**: Lack of high-frequency texture decomposition flattens wall grain and perspective corner gradients.
3. **Uncompensated Ambient Color Cast**: 2700K/6800K illuminant skews target paint pigments.
4. **Edge Halos**: Hard binary masks create harsh borders.
5. **Monolithic Mask**: No separation between walls, ceilings, baseboards, and trim.
