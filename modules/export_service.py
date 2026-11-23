"""Export services for palettes and room analysis (JSON, CSV, Swatch Sheet PNG, Text Report)."""
import io
import csv
import json
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw

from models.schemas import PaletteConcept, RoomAnalysisResult, ExtractedColorAnalysis


def export_palette_json(
    palette: PaletteConcept,
    room_analysis: Optional[RoomAnalysisResult] = None
) -> str:
    """Export palette and optional room analysis as formatted JSON string."""
    export_dict: Dict[str, Any] = {
        "palette_id": palette.id,
        "name": palette.name,
        "concept_category": palette.concept_category,
        "harmony_type": palette.harmony_type,
        "atmosphere": palette.atmosphere,
        "description": palette.description,
        "design_rationale": palette.design_rationale,
        "furniture_flooring_compatibility": palette.furniture_flooring_compatibility,
        "proportions": palette.proportions,
        "heuristic_score": palette.heuristic_score,
        "colors": [
            {
                "role": c.role,
                "name": c.name,
                "hex": c.hex,
                "rgb": {"r": c.rgb[0], "g": c.rgb[1], "b": c.rgb[2]},
                "temperature": c.temperature,
                "saturation": c.saturation_category,
                "luminance": c.luminance,
                "description": c.description
            }
            for c in palette.all_colors()
        ]
    }

    if room_analysis:
        export_dict["room_context"] = {
            "room_type": room_analysis.detected_room_type,
            "style": room_analysis.detected_style,
            "existing_wall": room_analysis.existing_wall_description,
            "flooring": room_analysis.flooring_description,
            "apparent_lighting": room_analysis.apparent_lighting,
            "analysis_provider": room_analysis.provider_name
        }

    return json.dumps(export_dict, indent=2)


def export_palette_csv(palette: PaletteConcept) -> str:
    """Export palette swatches as a formatted CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Role", "Name", "HEX", "RGB", "Red", "Green", "Blue", "Temperature", "Proportion", "Description"])

    colors = [
        ("Primary Wall", palette.primary_wall, palette.proportions.get("Primary Wall", "60%")),
        ("Secondary Wall", palette.secondary_wall, palette.proportions.get("Secondary Wall / Trim", "30%")),
        ("Accent", palette.accent, palette.proportions.get("Accent Accents", "10%")),
        ("Trim / Ceiling", palette.trim, "Architectural Trim")
    ]

    for role_label, swatch, prop in colors:
        writer.writerow([
            role_label,
            swatch.name or "Custom Tone",
            swatch.hex,
            f"rgb({swatch.rgb[0]}, {swatch.rgb[1]}, {swatch.rgb[2]})",
            swatch.rgb[0],
            swatch.rgb[1],
            swatch.rgb[2],
            swatch.temperature or "neutral",
            prop,
            swatch.description or ""
        ])

    return output.getvalue()


def generate_swatch_sheet_png(
    palette: PaletteConcept,
    room_type: str = "Interior Room"
) -> io.BytesIO:
    """
    Generate an architectural colour swatch presentation sheet as a high-resolution PNG image.
    Uses warm ivory background (#F5F0E8) and espresso typography (#30271F).
    """
    width = 1200
    height = 700

    sheet = Image.new("RGB", (width, height), color=(245, 240, 232))
    draw = ImageDraw.Draw(sheet)

    # Architectural Header Border
    draw.rectangle([(40, 30), (width - 40, 110)], fill=(255, 252, 247), outline=(227, 216, 203), width=2)
    draw.text((60, 45), f"ARCHITECTURAL INTERIOR SPECIFICATION: {palette.name.upper()}", fill=(48, 39, 31))
    draw.text((60, 75), f"ROOM: {room_type.upper()}  |  HARMONY: {palette.harmony_type.upper()}  |  ATMOSPHERE: {palette.atmosphere}", fill=(120, 107, 96))

    # Swatch Cards Layout (4 cards horizontally)
    card_width = 250
    card_height = 420
    start_x = 60
    spacing = 33
    start_y = 140

    cards_data = [
        ("PRIMARY WALL", palette.primary_wall, palette.proportions.get("Primary Wall", "60%")),
        ("SECONDARY WALL", palette.secondary_wall, palette.proportions.get("Secondary Wall / Trim", "30%")),
        ("ACCENT", palette.accent, palette.proportions.get("Accent Accents", "10%")),
        ("TRIM & CEILING", palette.trim, "Detail / Trim")
    ]

    for i, (role, swatch, prop) in enumerate(cards_data):
        cx = start_x + i * (card_width + spacing)
        cy = start_y

        # Card container with subtle border
        draw.rectangle([(cx, cy), (cx + card_width, cy + card_height)], fill=(255, 252, 247), outline=(227, 216, 203), width=1)

        # Large Color Swatch Box
        swatch_h = 240
        draw.rectangle([(cx + 12, cy + 12), (cx + card_width - 12, cy + 12 + swatch_h)], fill=swatch.rgb)
        # Inner fine border
        draw.rectangle([(cx + 12, cy + 12), (cx + card_width - 12, cy + 12 + swatch_h)], outline=(200, 190, 180), width=1)

        # Card text details
        text_y = cy + swatch_h + 24
        draw.text((cx + 16, text_y), role, fill=(114, 86, 64))
        draw.text((cx + 16, text_y + 24), swatch.name or "Custom Tone", fill=(48, 39, 31))
        draw.text((cx + 16, text_y + 50), f"HEX: {swatch.hex}", fill=(48, 39, 31))
        draw.text((cx + 16, text_y + 74), f"RGB: {swatch.rgb[0]}, {swatch.rgb[1]}, {swatch.rgb[2]}", fill=(120, 107, 96))
        draw.text((cx + 16, text_y + 98), f"Proportion: {prop}", fill=(120, 107, 96))

    # Footer Notes
    draw.rectangle([(40, 590), (width - 40, 660)], fill=(255, 252, 247), outline=(227, 216, 203), width=1)
    rationale_snip = palette.design_rationale[:140] + ("..." if len(palette.design_rationale) > 140 else "")
    draw.text((60, 602), f"DESIGN RATIONALE: {rationale_snip}", fill=(48, 39, 31))
    draw.text((60, 630), f"COMPATIBILITY: {palette.furniture_flooring_compatibility[:140]}", fill=(120, 107, 96))

    buffer = io.BytesIO()
    sheet.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_text_report(
    palette: PaletteConcept,
    room_analysis: Optional[RoomAnalysisResult] = None,
    extracted: Optional[ExtractedColorAnalysis] = None,
    room_type: str = "Living Room"
) -> str:
    """Generate a clean architectural interior design report as plaintext."""
    detected_room = room_analysis.detected_room_type if room_analysis else room_type
    detected_style = room_analysis.detected_style if room_analysis else "Modern Architectural"
    provider_name = room_analysis.provider_name if room_analysis else "Local Computer Vision"
    apparent_light = room_analysis.apparent_lighting if room_analysis else "Balanced Ambient Daylight"
    bright_desc = f"{extracted.overall_brightness:.1%} ({room_analysis.brightness_level.upper() if room_analysis else 'BALANCED'})" if extracted else "60.0% (BALANCED)"
    temp_tendency = extracted.overall_temperature_tendency.upper() if extracted else "BALANCED / NEUTRAL"
    wall_base = room_analysis.existing_wall_description if room_analysis else "Neutral architectural surface base"
    floor_base = room_analysis.flooring_description if room_analysis else "Warm hardwood / mineral flooring"

    lines = [
        "=" * 70,
        " AI INTERIOR COLOUR PALETTE CONSULTATION REPORT",
        "=" * 70,
        f"Generated: {palette.name}",
        f"Room Type: {room_type} (Detected: {detected_room})",
        f"Interior Style: {detected_style}",
        f"Analysis Provider: {provider_name}",
        f"Atmosphere Goal: {palette.atmosphere}",
        "",
        "-" * 70,
        " 1. ROOM OBSERVATIONS & LIGHTING ANALYSIS",
        "-" * 70,
        f"• Apparent Lighting: {apparent_light}",
        f"• Overall Brightness: {bright_desc}",
        f"• Ambient Temperature Tendency: {temp_tendency}",
        f"• Existing Wall Base: {wall_base}",
        f"• Flooring Base: {floor_base}",
        "",
        "Key Design Strengths:",
    ]
    if room_analysis and room_analysis.design_strengths:
        for s in room_analysis.design_strengths:
            lines.append(f"  + {s}")
    else:
        lines.append("  + Balanced spatial illumination with clean sightlines.")
        lines.append("  + Harmonious foundational surfaces providing a versatile canvas.")

    lines.append("")
    lines.append("Design Challenges & Optical Considerations:")
    if room_analysis and room_analysis.design_challenges:
        for c in room_analysis.design_challenges:
            lines.append(f"  - {c}")
    else:
        lines.append("  - Natural daylight shifts between morning and evening lighting.")

    lines.extend([
        "",
        "-" * 70,
        " 2. EXTRACTED DOMINANT COLOURS (FROM PHOTOGRAPH)",
        "-" * 70
    ])
    if extracted and extracted.dominant_colors:
        for sw in extracted.dominant_colors[:6]:
            lines.append(f"• {sw.role}: {sw.name} | HEX: {sw.hex} | RGB: {sw.rgb} | {sw.description or ''}")
    else:
        for sw in palette.all_colors():
            lines.append(f"• {sw.role}: {sw.name} | HEX: {sw.hex} | RGB: {sw.rgb} | {sw.description or ''}")

    lines.extend([
        "",
        "-" * 70,
        f" 3. RECOMMENDED PALETTE: {palette.name.upper()}",
        "-" * 70,
        f"Concept Category: {palette.concept_category}",
        f"Harmony System:   {palette.harmony_type}",
        f"Design Match Score: {palette.heuristic_score} / 100",
        "",
        "COLOUR SPECIFICATION (60-30-10 RULE):",
        "1. Primary Wall (60%):",
        f"   Name: {palette.primary_wall.name} | HEX: {palette.primary_wall.hex} | RGB: {palette.primary_wall.rgb}",
        f"   Traits: {palette.primary_wall.description or ''}",
        "",
        "2. Secondary / Feature Wall (30%):",
        f"   Name: {palette.secondary_wall.name} | HEX: {palette.secondary_wall.hex} | RGB: {palette.secondary_wall.rgb}",
        f"   Traits: {palette.secondary_wall.description or ''}",
        "",
        "3. Accent Details (10%):",
        f"   Name: {palette.accent.name} | HEX: {palette.accent.hex} | RGB: {palette.accent.rgb}",
        f"   Traits: {palette.accent.description or ''}",
        "",
        "4. Architectural Trim & Ceiling:",
        f"   Name: {palette.trim.name} | HEX: {palette.trim.hex} | RGB: {palette.trim.rgb}",
        f"   Traits: {palette.trim.description or ''}",
        "",
        "DESIGN RATIONALE & APPLICATION GUIDELINES:",
        f"{palette.design_rationale}",
        "",
        "FURNITURE & FLOORING HARMONIZATION:",
        f"{palette.furniture_flooring_compatibility}",
        "",
        "=" * 70,
        "End of Architectural Consultation Report",
        "=" * 70
    ])

    return "\n".join(lines)


def generate_markdown_report(
    palette: PaletteConcept,
    room_analysis: Optional[RoomAnalysisResult] = None,
    extracted: Optional[ExtractedColorAnalysis] = None,
    room_type: str = "Living Room"
) -> str:
    """Generate an editorial Markdown design consultation report with structured badges and tables."""
    detected_room = room_analysis.detected_room_type if room_analysis else room_type
    detected_style = room_analysis.detected_style if room_analysis else "Modern Architectural"
    provider_name = room_analysis.provider_name if room_analysis else "Local Computer Vision"
    apparent_light = room_analysis.apparent_lighting if room_analysis else "Balanced Ambient Daylight"

    md = f"""# CHROMA STUDIO AI — Architectural Consultation Report

**Project:** {palette.name}  
**Room Type:** {room_type} (Detected: {detected_room})  
**Style Aesthetic:** {detected_style}  
**Analysis Engine:** `{provider_name}`  
**Atmosphere Goal:** {palette.atmosphere}  
**Design Match Score:** **{palette.heuristic_score} / 100**

---

## 1. Spatial Observations & Lighting Analysis
- **Apparent Lighting:** {apparent_light}
- **Existing Wall Base:** {room_analysis.existing_wall_description if room_analysis else "Neutral architectural surface base"}
- **Flooring:** {room_analysis.flooring_description if room_analysis else "Hardwood / mineral flooring base"}

---

## 2. Recommended Palette Specification (60-30-10 Rule)

| Proportion | Architectural Role | Shade Name | HEX | RGB | Traits |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **60%** | Primary Wall | `{palette.primary_wall.name}` | `{palette.primary_wall.hex}` | `{palette.primary_wall.rgb}` | {palette.primary_wall.description or 'Foundational plane'} |
| **30%** | Secondary Wall / Trim | `{palette.secondary_wall.name}` | `{palette.secondary_wall.hex}` | `{palette.secondary_wall.rgb}` | {palette.secondary_wall.description or 'Contrasting plane'} |
| **10%** | Accent Details | `{palette.accent.name}` | `{palette.accent.hex}` | `{palette.accent.rgb}` | {palette.accent.description or 'Focal highlight'} |
| **Detail** | Trim & Millwork | `{palette.trim.name}` | `{palette.trim.hex}` | `{palette.trim.rgb}` | {palette.trim.description or 'Architectural frame'} |

---

## 3. Design Rationale & Application
> **Architectural Direction:**  
> {palette.design_rationale}

> **Material & Flooring Harmony:**  
> {palette.furniture_flooring_compatibility}

---
*Report generated by CHROMA STUDIO AI — Editorial Architectural Edition.*
"""
    return md


def generate_pdf_report(
    palette: PaletteConcept,
    room_analysis: Optional[RoomAnalysisResult] = None,
    extracted: Optional[ExtractedColorAnalysis] = None,
    room_type: str = "Living Room"
) -> io.BytesIO:
    """
    Generate an architectural consultation presentation report as a publication-ready PDF document.
    Renders high-resolution vector-like layout with warm ivory cards, typography, swatches, and specs.
    """
    width = 1600
    height = 2200
    page = Image.new("RGB", (width, height), color=(245, 240, 232))
    draw = ImageDraw.Draw(page)

    # 1. Header Canvas & Banner
    draw.rectangle([(60, 60), (width - 60, 240)], fill=(255, 252, 247), outline=(227, 216, 203), width=2)
    draw.text((100, 90), "CHROMA STUDIO AI — ARCHITECTURAL COLOUR CONSULTATION", fill=(48, 39, 31))
    draw.text((100, 135), f"PROJECT: {palette.name.upper()}  |  STYLE: {(room_analysis.detected_style if room_analysis else 'MODERN').upper()}", fill=(114, 86, 64))
    draw.text((100, 180), f"ROOM: {room_type.upper()}  |  HARMONY: {palette.harmony_type.upper()}  |  MATCH: {palette.heuristic_score}%", fill=(120, 107, 96))

    # 2. Four Color Swatches Cards
    roles_data = [
        ("PRIMARY WALL (60%)", palette.primary_wall, palette.proportions.get("Primary Wall", "60%")),
        ("SECONDARY WALL (30%)", palette.secondary_wall, palette.proportions.get("Secondary Wall / Trim", "30%")),
        ("ACCENT DETAILS (10%)", palette.accent, palette.proportions.get("Accent Details", "10%")),
        ("TRIM & MILLWORK", palette.trim, "Architectural Frame")
    ]
    card_w = 345
    card_h = 580
    start_x = 80
    gap_x = 35
    start_y = 280

    for i, (r_name, sw, prop) in enumerate(roles_data):
        cx = start_x + i * (card_w + gap_x)
        # Card Background
        draw.rectangle([(cx, start_y), (cx + card_w, start_y + card_h)], fill=(255, 252, 247), outline=(227, 216, 203), width=1)
        # Swatch Block
        draw.rectangle([(cx + 15, start_y + 15), (cx + card_w - 15, start_y + 360)], fill=sw.rgb, outline=(215, 205, 195), width=1)
        # Text details
        draw.text((cx + 20, start_y + 385), r_name, fill=(114, 86, 64))
        draw.text((cx + 20, start_y + 425), sw.name or "Custom Tone", fill=(48, 39, 31))
        draw.text((cx + 20, start_y + 465), f"HEX: {sw.hex}", fill=(48, 39, 31))
        draw.text((cx + 20, start_y + 500), f"RGB: {sw.rgb[0]}, {sw.rgb[1]}, {sw.rgb[2]}", fill=(120, 107, 96))
        draw.text((cx + 20, start_y + 535), f"Allocation: {prop}", fill=(120, 107, 96))

    # 3. Spatial & Lighting Section
    box2_y = 900
    draw.rectangle([(80, box2_y), (width - 80, box2_y + 340)], fill=(255, 252, 247), outline=(227, 216, 203), width=1)
    draw.text((110, box2_y + 25), "SPATIAL ANALYSIS & LIGHTING OBSERVATIONS", fill=(48, 39, 31))
    apparent_light = room_analysis.apparent_lighting if room_analysis else "Balanced Natural Daylight"
    wall_base = room_analysis.existing_wall_description if room_analysis else "Neutral architectural surface base"
    floor_base = room_analysis.flooring_description if room_analysis else "Hardwood / mineral flooring base"
    draw.text((110, box2_y + 75), f"• Apparent Lighting: {apparent_light}", fill=(80, 70, 60))
    draw.text((110, box2_y + 120), f"• Existing Wall Base: {wall_base}", fill=(80, 70, 60))
    draw.text((110, box2_y + 165), f"• Existing Flooring: {floor_base}", fill=(80, 70, 60))
    draw.text((110, box2_y + 210), f"• Atmosphere Objective: {palette.atmosphere}", fill=(80, 70, 60))
    draw.text((110, box2_y + 255), f"• Concept Harmony System: {palette.concept_category} ({palette.harmony_type})", fill=(80, 70, 60))

    # 4. Design Rationale & Application Section
    box3_y = 1280
    draw.rectangle([(80, box3_y), (width - 80, box3_y + 400)], fill=(255, 252, 247), outline=(227, 216, 203), width=1)
    draw.text((110, box3_y + 25), "ARCHITECTURAL SPECIFICATION & RATIONALE", fill=(48, 39, 31))
    rat_text = palette.design_rationale
    draw.text((110, box3_y + 80), f"Rationale: {rat_text[:280]}", fill=(80, 70, 60))
    if len(rat_text) > 280:
        draw.text((110, box3_y + 120), f"{rat_text[280:560]}", fill=(80, 70, 60))
    draw.text((110, box3_y + 190), "Material & Flooring Harmony:", fill=(114, 86, 64))
    mat_text = palette.furniture_flooring_compatibility
    draw.text((110, box3_y + 235), f"{mat_text[:350]}", fill=(80, 70, 60))

    # 5. Paint Quantity & Regulatory Footer
    box4_y = 1720
    draw.rectangle([(80, box4_y), (width - 80, box4_y + 360)], fill=(255, 252, 247), outline=(227, 216, 203), width=1)
    draw.text((110, box4_y + 25), "TECHNICAL PAINT ADVISORY & SPECIFICATIONS", fill=(48, 39, 31))
    draw.text((110, box4_y + 75), "• Standard interior application: 2 coats over 1 coat of acrylic primer.", fill=(80, 70, 60))
    draw.text((110, box4_y + 120), "• Safety allowance: 10% volume safety margin factored into standard coverage (12 m2/L).", fill=(80, 70, 60))
    draw.text((110, box4_y + 165), "• Recommended finish: Eggshell / Low-sheen satin for primary wall; flat matte for ceilings.", fill=(80, 70, 60))
    draw.text((110, box4_y + 240), "Generated with CHROMA STUDIO AI — Production Architectural Specification Suite", fill=(114, 86, 64))

    pdf_buffer = io.BytesIO()
    page.save(pdf_buffer, format="PDF", resolution=150.0)
    pdf_buffer.seek(0)
    return pdf_buffer
