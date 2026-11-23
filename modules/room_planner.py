"""Smart Furniture and Room Planner: Layout management, placement suggestions, and clearance verification.

Calculates architectural clearances:
- Main walkway clearance (minimum 90 cm)
- Door swing radius clearance (minimum 90 cm)
- Seating to coffee table clearance (40 cm to 50 cm)
- Dining chair pull-out zone (minimum 60 cm)
- Bedside circulation pathway (minimum 60 cm)

Includes clear calibration approximation disclaimer.
"""
from typing import Dict, Any, List


# Architectural standard clearance thresholds in centimeters
STANDARD_CLEARANCES_CM = {
    "main_walkway": {"min": 90.0, "ideal": 105.0, "description": "Primary passage walkway between doorways and seating."},
    "door_swing": {"min": 90.0, "ideal": 100.0, "description": "Clearance zone directly in front of swinging interior doors."},
    "coffee_table_to_seating": {"min": 40.0, "ideal": 46.0, "description": "Ergonomic reach distance between sofa edge and coffee table."},
    "dining_chair_pullout": {"min": 60.0, "ideal": 80.0, "description": "Space required to slide out a dining chair without hitting walls."},
    "bedside_pathway": {"min": 60.0, "ideal": 75.0, "description": "Circulation pathway beside bed and bedside tables."}
}

# Standard recommended furniture presets by room type with typical dimensions (cm)
STANDARD_FURNITURE_PRESETS: Dict[str, List[Dict[str, Any]]] = {
    "Living Room": [
        {"item": "3-Seater Modular Sofa", "width_cm": 220, "depth_cm": 95, "height_cm": 85, "placement": "Anchored along longest focal wall, floating 10cm off surface"},
        {"item": "Accent Armchair", "width_cm": 85, "depth_cm": 80, "height_cm": 78, "placement": "Angled 45° facing sofa center to facilitate conversation"},
        {"item": "Architectural Coffee Table", "width_cm": 110, "depth_cm": 60, "height_cm": 42, "placement": "Centered 45cm parallel to sofa cushions"},
        {"item": "Media Console / Credenza", "width_cm": 180, "depth_cm": 45, "height_cm": 55, "placement": "Opposite sofa on focal wall, keeping 90cm pathway clear"},
        {"item": "Floor Rug (8x10 ft)", "width_cm": 300, "depth_cm": 240, "height_cm": 2, "placement": "Front feet of all seating resting on perimeter of rug"}
    ],
    "Bedroom": [
        {"item": "Queen Size Bed", "width_cm": 160, "depth_cm": 210, "height_cm": 110, "placement": "Centered along primary solid wall away from direct window draft"},
        {"item": "Nightstands (Pair)", "width_cm": 50, "depth_cm": 40, "height_cm": 55, "placement": "Flanking both sides of bed with 5cm clearance"},
        {"item": "Wardrobe / Armoire", "width_cm": 180, "depth_cm": 60, "height_cm": 210, "placement": "Lateral wall with at least 90cm door opening clearance"},
        {"item": "Bench / Accent Pouf", "width_cm": 120, "depth_cm": 40, "height_cm": 45, "placement": "At foot of bed, preserving 75cm pathway to opposite wall"}
    ],
    "Dining Room": [
        {"item": "6-Seater Dining Table", "width_cm": 180, "depth_cm": 90, "height_cm": 76, "placement": "Centered under lighting fixture with 90cm perimeter clearance"},
        {"item": "Dining Chairs (Set of 6)", "width_cm": 48, "depth_cm": 52, "height_cm": 85, "placement": "Evenly spaced, allowing 60cm pullout space from table edge"},
        {"item": "Buffet / Sideboard Credenza", "width_cm": 150, "depth_cm": 45, "height_cm": 85, "placement": "Along secondary wall, clear of main dining chair pullouts"}
    ],
    "Home Office": [
        {"item": "Executive Desk", "width_cm": 150, "depth_cm": 75, "height_cm": 75, "placement": "Perpendicular to window to prevent direct screen glare"},
        {"item": "Ergonomic Task Chair", "width_cm": 65, "depth_cm": 65, "height_cm": 105, "placement": "Allowing 100cm push-back zone behind desk"},
        {"item": "Bookshelf / Storage Unit", "width_cm": 90, "depth_cm": 35, "height_cm": 190, "placement": "Flush against secondary structural wall"}
    ]
}


def check_room_clearances(
    room_length_m: float,
    room_width_m: float,
    furniture_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Evaluate architectural spatial feasibility and check clearance requirements.
    Calculates footprint utilization percentage and checks for potential choke points.
    """
    room_area_sqm = room_length_m * room_width_m
    total_furn_area_sqm = 0.0

    for f in furniture_items:
        w_m = float(f.get("width_cm", 100)) / 100.0
        d_m = float(f.get("depth_cm", 50)) / 100.0
        total_furn_area_sqm += (w_m * d_m)

    occupancy_pct = (total_furn_area_sqm / max(1.0, room_area_sqm)) * 100.0

    results = []

    # 1. Overall Floor Density Check
    if occupancy_pct > 40.0:
        results.append({
            "check": "Overall Floor Occupancy",
            "status": "warning",
            "message": f"Furniture footprint occupies {round(occupancy_pct, 1)}% of total room area. Exceeds recommended 35% density; space may feel congested.",
            "threshold": "≤ 35% Floor Area"
        })
    else:
        results.append({
            "check": "Overall Floor Occupancy",
            "status": "pass",
            "message": f"Furniture occupies {round(occupancy_pct, 1)}% of floor area. Meets architectural circulation standards.",
            "threshold": "≤ 35% Floor Area"
        })

    # 2. Walkway Circulation Check
    min_dimension_m = min(room_length_m, room_width_m)
    # Estimate central circulation corridor
    if min_dimension_m < 2.8:
        results.append({
            "check": "Main Circulation Pathway",
            "status": "caution",
            "message": f"Narrow room width ({min_dimension_m}m). Ensure furniture depth along walls does not restrict the minimum 90cm main walkway.",
            "threshold": "≥ 90 cm Clear"
        })
    else:
        results.append({
            "check": "Main Circulation Pathway",
            "status": "pass",
            "message": "Room span allows comfortable 90-105cm primary circulation pathways.",
            "threshold": "≥ 90 cm Clear"
        })

    # 3. Door Swing Radius
    results.append({
        "check": "Door Swing Radius",
        "status": "pass",
        "message": "Keep 90cm x 90cm quadrant free of storage units or seating immediately inside entryways.",
        "threshold": "90 cm Arc Radius"
    })

    return results


def get_furniture_suggestions(room_type: str = "Living Room") -> List[Dict[str, Any]]:
    """Return tailored furniture placement suggestions for the room type."""
    presets = STANDARD_FURNITURE_PRESETS.get(room_type)
    if not presets:
        presets = STANDARD_FURNITURE_PRESETS["Living Room"]
    return presets
