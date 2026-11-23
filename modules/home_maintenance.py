"""Home Maintenance: Periodic condition tracking, damage diagnostics, maintenance logs, and reminders."""
from typing import Dict, Any
from PIL import Image
import numpy as np
import cv2

DAMAGE_CATEGORIES = {
    "Hairline Cracks": {
        "severity_levels": ["Minor (<1mm)", "Moderate (1-3mm)", "Structural (>3mm)"],
        "recommended_treatment": "V-groove chase, elastomeric acrylic crack filler, sand smooth, spot-prime before topcoat.",
        "urgency": "Medium"
    },
    "Dampness & Efflorescence": {
        "severity_levels": ["Slight moisture patch", "White mineral bloom", "Active water seepage"],
        "recommended_treatment": "Locate water ingress source, dry completely, apply penetrating silicone waterproofing barrier before replastering.",
        "urgency": "High"
    },
    "Paint Peeling & Flaking": {
        "severity_levels": ["Edge curling", "Localized patch peeling", "Widespread adhesion failure"],
        "recommended_treatment": "Scrape all loose flakes to firm edge, feather with 120-grit emery paper, apply alkali-resistant primer.",
        "urgency": "Medium"
    },
    "Surface Scuffs & Stains": {
        "severity_levels": ["Light pencil/furniture marks", "Grease/oil stains", "Deep gouges"],
        "recommended_treatment": "Clean with mild detergent sponge; for gouges apply ready-mix interior putty, dry 4 hours, spot repaint.",
        "urgency": "Low"
    },
    "None (Healthy Condition)": {
        "severity_levels": ["Flawless architectural finish"],
        "recommended_treatment": "No remedial action required. Clean periodically with dry microfiber duster.",
        "urgency": "None"
    }
}


def evaluate_wall_damage_heuristics(damage_type: str, severity: str) -> Dict[str, Any]:
    """Provide architectural assessment and step-by-step remediation protocol."""
    info = DAMAGE_CATEGORIES.get(damage_type, DAMAGE_CATEGORIES["None (Healthy Condition)"])
    return {
        "damage_type": damage_type,
        "severity": severity,
        "urgency": info["urgency"],
        "treatment_protocol": info["recommended_treatment"]
    }


def create_condition_comparison_image(
    earlier_image: Image.Image,
    later_image: Image.Image,
    label_earlier: str = "Initial Condition",
    label_later: str = "Current Inspection"
) -> Image.Image:
    """
    Generate side-by-side comparison image of room condition over time
    with architectural date and condition stamps.
    """
    # Resize both to same height
    target_h = 600
    w1, h1 = earlier_image.size
    w2, h2 = later_image.size

    new_w1 = int(w1 * (target_h / float(h1)))
    new_w2 = int(w2 * (target_h / float(h2)))

    im1 = earlier_image.resize((new_w1, target_h), Image.Resampling.LANCZOS)
    im2 = later_image.resize((new_w2, target_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (new_w1 + new_w2 + 8, target_h + 60), color=(245, 240, 232))
    canvas.paste(im1, (0, 60))
    canvas.paste(im2, (new_w1 + 8, 60))

    # Convert to OpenCV to draw clean text labels
    cv_img = cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)

    # Header bar
    cv2.rectangle(cv_img, (0, 0), (new_w1 + new_w2 + 8, 56), (255, 252, 247), cv2.FILLED)
    cv2.line(cv_img, (0, 56), (new_w1 + new_w2 + 8, 56), (227, 216, 203), 1)

    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(cv_img, f"BEFORE: {label_earlier}", (20, 36), font, 0.65, (48, 39, 31), 2, cv2.LINE_AA)
    cv2.putText(cv_img, f"AFTER: {label_later}", (new_w1 + 24, 36), font, 0.65, (114, 86, 64), 2, cv2.LINE_AA)

    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
