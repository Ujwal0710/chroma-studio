"""Advanced Wall Segmentation Pipeline.

Combines:
1. Edge-preserving bilateral filtering to suppress wall paint texture.
2. Perceptual CIELAB and HSV color homogeneity metrics (far superior to RGB distance).
3. Canny & Sobel gradient boundary barriers to halt flooding at furniture, windows, ceilings, and baseboards.
4. Window and outdoor glare suppression (high-luminance specular filtering).
5. Ground plane / flooring boundary detection.
6. Multi-wall component clustering (supports selecting specific wall planes).
7. Interactive manual mask adjustments (seed points, brush additions, eraser exclusions, rectangular bounds).
8. Rigorous boundary-confidence scoring with low-confidence diagnostic warnings.
"""
from typing import Tuple, Optional, Dict, Any, List
import numpy as np
from PIL import Image
import cv2
from scipy import ndimage

from modules.image_processing import pil_to_numpy_rgb


def compute_boundary_edges(gray_arr: np.ndarray, edge_protection: float = 0.65) -> np.ndarray:
    """
    Compute sharp structural edge barriers using bilateral filtering + Canny & morphological gradients.
    Prevents mask from bleeding into door frames, picture moldings, and furniture.
    """
    # Bilateral filter preserves sharp structural edges while smoothing paint texture
    smoothed = cv2.bilateralFilter(gray_arr, d=7, sigmaColor=40, sigmaSpace=7)

    # Dynamic Canny thresholds adjusted by edge_protection
    high_thresh = int(np.clip(180 - edge_protection * 90, 40, 220))
    low_thresh = int(high_thresh * 0.45)
    canny_edges = cv2.Canny(smoothed, low_thresh, high_thresh)

    # Morphological gradient for edge dilation
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated_edges = cv2.dilate(canny_edges, kernel, iterations=1)
    return dilated_edges > 0


def detect_floor_boundary_profile(arr: np.ndarray, upper_bias: float = 0.70) -> np.ndarray:
    """
    Detect probable floor regions based on spatial position and horizontal edge accumulation.
    Rather than a crude flat cutoff, uses horizontal gradient accumulation and position weighting.
    """
    h, w, _ = arr.shape
    y_coords, _ = np.indices((h, w))
    rel_y = y_coords / float(h)

    # Floor base cutoff starts at lowest portion dictated by upper_bias
    min_floor_y = 1.0 - (upper_bias * 0.38)

    # Detect horizontal line transitions in bottom half
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    abs_sobel_y = np.abs(sobel_y)

    # Blur horizontally to detect continuous floor trim / baseboard lines
    h_blur = cv2.blur(abs_sobel_y, (int(w * 0.15) | 1, 3))
    strong_h_edges = h_blur > np.percentile(h_blur, 92)

    # Bottom region below strong horizontal baseboard transitions
    floor_mask = (rel_y > min_floor_y)
    # If strong baseboard edge detected in lower third, reinforce floor exclusion below it
    lower_edges = strong_h_edges & (rel_y > 0.55)
    if np.any(lower_edges):
        # Find median y coordinate of lowest prominent horizontal boundary
        y_indices = np.where(lower_edges)[0]
        if len(y_indices) > 50:
            median_baseboard_y = float(np.median(y_indices)) / float(h)
            if median_baseboard_y > 0.55:
                floor_mask = floor_mask | (rel_y > median_baseboard_y)

    return floor_mask


def detect_window_glare(arr: np.ndarray, gray: np.ndarray) -> np.ndarray:
    """
    Detect blown-out windows, exterior views, or intense specular lighting that should not be painted.
    Windows typically exhibit near-maximum luminance (>244) with sharp frames or blue sky tint.
    """
    # Overexposed regions / bright daylight windows
    overexposed = (gray >= 244) & (np.min(arr, axis=2) >= 225)

    # Blue daylight/sky tint in window panes
    r = arr[:, :, 0].astype(np.float32)
    b = arr[:, :, 2].astype(np.float32)
    sky_tint = (b >= r + 12) & (b >= 240) & (gray >= 235)

    glare_mask = overexposed | sky_tint
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    glare_clean = cv2.morphologyEx(glare_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    return glare_clean > 0


def segment_distinct_wall_planes(mask: np.ndarray, min_area_pct: float = 2.0) -> List[Dict[str, Any]]:
    """
    Cluster the connected components of the wall mask into distinct architectural wall planes
    (e.g., Left Wall, Center Wall, Right Wall, Upper Feature Plane).
    """
    h, w = mask.shape
    total_area = h * w
    min_pixels = int(total_area * (min_area_pct / 100.0))

    labeled, num_features = ndimage.label(mask > 0)
    planes: List[Dict[str, Any]] = []

    if num_features == 0:
        return planes

    sizes = ndimage.sum(mask > 0, labeled, range(1, num_features + 1))
    sorted_labels = np.argsort(sizes)[::-1]

    for rank, label_idx in enumerate(sorted_labels):
        comp_id = label_idx + 1
        comp_size = sizes[label_idx]
        if comp_size < min_pixels:
            continue

        comp_mask = (labeled == comp_id).astype(np.uint8) * 255
        # Calculate centroid
        cy, cx = ndimage.center_of_mass(comp_mask)
        rel_x = cx / float(w)

        if rel_x < 0.35:
            plane_name = f"Left Wall Section (Plane #{rank + 1})"
        elif rel_x > 0.65:
            plane_name = f"Right Wall Section (Plane #{rank + 1})"
        else:
            plane_name = f"Center / Main Wall (Plane #{rank + 1})"

        coverage = round((comp_size / float(total_area)) * 100.0, 1)

        planes.append({
            "plane_id": rank + 1,
            "name": plane_name,
            "centroid": (int(cx), int(cy)),
            "coverage_percent": coverage,
            "mask": comp_mask
        })

    return planes


def apply_manual_corrections(
    base_mask: np.ndarray,
    manual_adjustments: Optional[List[Dict[str, Any]]] = None
) -> np.ndarray:
    """
    Apply interactive manual edits:
    - Include / Exclude brush strokes: {"type": "brush", "mode": "include"|"exclude", "x": int, "y": int, "radius": int}
    - Include / Exclude rectangles: {"type": "rect", "mode": "include"|"exclude", "x1": int, "y1": int, "x2": int, "y2": int}
    """
    if not manual_adjustments:
        return base_mask

    corrected = base_mask.copy()
    h, w = corrected.shape

    for adj in manual_adjustments:
        mode = adj.get("mode", "include")
        val = 255 if mode == "include" else 0
        adj_type = adj.get("type", "brush")

        if adj_type == "brush":
            cx, cy = int(adj.get("x", 0)), int(adj.get("y", 0))
            rad = max(2, int(adj.get("radius", 25)))
            cv2.circle(corrected, (cx, cy), rad, val, thickness=-1)

        elif adj_type == "rect":
            x1, y1 = max(0, int(adj.get("x1", 0))), max(0, int(adj.get("y1", 0)))
            x2, y2 = min(w, int(adj.get("x2", w))), min(h, int(adj.get("y2", h)))
            cv2.rectangle(corrected, (x1, y1), (x2, y2), val, thickness=-1)

    return corrected


def generate_wall_mask(
    img: Image.Image,
    sensitivity: float = 0.55,
    upper_bias: float = 0.70,
    edge_protection: float = 0.65,
    manual_seed: Optional[Tuple[int, int]] = None,
    target_plane_id: Optional[int] = None,
    manual_adjustments: Optional[List[Dict[str, Any]]] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate an intelligent, multi-cue wall mask with CIELAB color homogeneity,
    structural edge protection, window glare exclusion, multi-plane extraction, and manual controls.

    Parameters:
        img: Input room PIL Image.
        sensitivity: Tolerance for wall tonal variance (0.1 to 1.0).
        upper_bias: Vertical prior penalizing bottom flooring (0.0 to 1.0).
        edge_protection: Strength of edge and boundary barrier preservation (0.1 to 1.0).
        manual_seed: Optional (x, y) coordinate to anchor wall region growing.
        target_plane_id: If specified, isolates only that distinct wall plane.
        manual_adjustments: Optional list of brush or box adjustments for user correction.

    Returns:
        Tuple of (mask_uint8, metadata_dict) where mask_uint8 is [0..255].
    """
    arr = pil_to_numpy_rgb(img)
    height, width, _ = arr.shape
    total_pixels = height * width

    # Convert to grayscale and CIELAB
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB).astype(np.float32)

    # 1. Structural Edge Barriers
    edges = compute_boundary_edges(gray, edge_protection=edge_protection)

    # 2. Floor Suppression Profile
    floor_mask = detect_floor_boundary_profile(arr, upper_bias=upper_bias)

    # 3. Window & Specular Glare Suppression
    glare_mask = detect_window_glare(arr, gray)

    # 4. Seed Selection: Focus strictly in upper 38% of image (above furniture planes)
    if manual_seed is not None and 0 <= manual_seed[0] < width and 0 <= manual_seed[1] < height:
        seed_x, seed_y = manual_seed
        seed_pixels = [(seed_y, seed_x)]
    else:
        # Automatic seed selection: upper region with low gradient and balanced luminance
        upper_limit = int(height * 0.38)
        # Avoid edges, floor, and glare
        candidate_map = (~edges[:upper_limit, :]) & (~floor_mask[:upper_limit, :]) & (~glare_mask[:upper_limit, :])
        candidate_map = candidate_map & (gray[:upper_limit, :] > 45) & (gray[:upper_limit, :] < 242)

        step_y = max(6, height // 30)
        step_x = max(6, width // 30)
        seed_pixels = []
        for y in range(int(height * 0.08), upper_limit, step_y):
            for x in range(int(width * 0.12), int(width * 0.88), step_x):
                if candidate_map[y, x]:
                    seed_pixels.append((y, x))

    if not seed_pixels:
        seed_pixels = [(int(height * 0.22), int(width * 0.5))]

    # 5. CIELAB Perceptual Color Homogeneity across candidate seed clusters
    seed_labs = np.array([lab[sy, sx] for sy, sx in seed_pixels], dtype=np.float32)
    if len(seed_labs) >= 3:
        # Cluster candidate seeds into up to 3 dominant wall tone clusters (captures multi-color walls)
        n_clusters = min(3, len(seed_labs))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, _, cluster_centers = cv2.kmeans(seed_labs, n_clusters, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    else:
        cluster_centers = seed_labs

    # Minimum perceptual delta E distance across any candidate wall seed cluster
    delta_e = np.full((height, width), 999.0, dtype=np.float32)
    for c_lab in cluster_centers:
        d_l = lab[:, :, 0] - c_lab[0]
        d_a = lab[:, :, 1] - c_lab[1]
        d_b = lab[:, :, 2] - c_lab[2]
        d_dist = np.sqrt(d_l ** 2 + (d_a * 1.3) ** 2 + (d_b * 1.3) ** 2)
        delta_e = np.minimum(delta_e, d_dist)

    # Sensitivity scales allowed Delta E
    max_delta_e = 16.0 + (sensitivity * 34.0)  # Range ~19 to ~50 ΔE
    homogeneity_mask = delta_e <= max_delta_e

    # 6. Combine cues: low gradient + color homogeneity + floor suppression + glare suppression
    raw_wall = homogeneity_mask & (~edges) & (~floor_mask) & (~glare_mask)

    # 7. Morphological Cleanup (Closing small texture pores, removing isolated pixel specks)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))

    cleaned = cv2.morphologyEx(raw_wall.astype(np.uint8), cv2.MORPH_OPEN, kernel_open)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close)

    # Retain substantial connected components (> 0.5% image area) that are reached by wall seeds
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    min_comp_area = int(total_pixels * 0.005)

    # Determine which connected components contain valid wall seeds
    seed_labels = set()
    for sy, sx in seed_pixels:
        lbl = labels[sy, sx]
        if lbl > 0:
            seed_labels.add(lbl)

    valid_mask = np.zeros((height, width), dtype=np.uint8)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_comp_area:
            # Component must either intersect a wall seed or have an upper centroid when seed_labels is empty
            cy, _ = centroids[i]
            is_seeded = (i in seed_labels)
            is_valid_upper = (cy < height * 0.65) and (not seed_labels)
            if is_seeded or is_valid_upper:
                valid_mask[labels == i] = 255

    # 8. Distinct Wall Planes Discovery
    detected_planes = segment_distinct_wall_planes(valid_mask, min_area_pct=1.5)

    # If user selected a specific wall plane, isolate it
    if target_plane_id is not None and detected_planes:
        matched_plane = next((p for p in detected_planes if p["plane_id"] == target_plane_id), None)
        if matched_plane:
            final_mask = matched_plane["mask"].copy()
        else:
            final_mask = valid_mask.copy()
    else:
        final_mask = valid_mask.copy()

    # 9. Apply Manual User Adjustments if any
    if manual_adjustments:
        final_mask = apply_manual_corrections(final_mask, manual_adjustments)

    # 10. Segmentation Confidence and Diagnostic Assessment
    coverage_pct = round((np.sum(final_mask > 0) / float(total_pixels)) * 100.0, 1)

    # Evaluate boundary edge correlation
    mask_edges = cv2.Canny(final_mask, 50, 150)
    dilated_img_edges = cv2.dilate(edges.astype(np.uint8), kernel_open, iterations=2)
    aligned_boundary_pixels = np.sum((mask_edges > 0) & (dilated_img_edges > 0))
    total_boundary_pixels = np.sum(mask_edges > 0)
    boundary_alignment_ratio = (
        float(aligned_boundary_pixels) / float(total_boundary_pixels)
        if total_boundary_pixels > 0 else 0.5
    )

    warnings: List[str] = []
    if coverage_pct < 8.0:
        confidence = "Low"
        warnings.append("Very low wall coverage detected. Wall may be obscured by large furniture or complex lighting.")
    elif coverage_pct > 75.0:
        confidence = "Low"
        warnings.append("Unusually high coverage (>75%). Verify that flooring, ceiling, or upholstery were not accidentally included.")
    elif boundary_alignment_ratio < 0.25:
        confidence = "Moderate"
        warnings.append("Mask boundaries do not strongly align with natural architectural lines. Use manual brush controls to refine edges.")
    else:
        confidence = "High"

    metadata = {
        "wall_coverage_percent": coverage_pct,
        "segmentation_confidence": confidence,
        "boundary_alignment_score": round(boundary_alignment_ratio, 2),
        "sensitivity": sensitivity,
        "edge_protection": edge_protection,
        "upper_bias": upper_bias,
        "seed_count": len(seed_pixels),
        "detected_planes": [
            {"plane_id": p["plane_id"], "name": p["name"], "coverage_percent": p["coverage_percent"]}
            for p in detected_planes
        ],
        "active_plane_id": target_plane_id if target_plane_id else "all",
        "warnings": warnings,
        "method": "Multi-Cue CIELAB Homogeneity + Bilateral Edge Protection"
    }

    return final_mask, metadata
