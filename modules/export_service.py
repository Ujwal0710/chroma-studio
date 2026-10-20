"""Export services for palettes and room analysis (JSON, CSV, Swatch Sheet PNG, Text Report)."""
import io
import csv
import json
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

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
    room_analysis: RoomAnalysisResult,
    extracted: ExtractedColorAnalysis,
    room_type: str = "Living Room"
) -> str:
    """Generate a clean architectural interior design report as plaintext."""
    lines = [
        "=" * 70,
        " AI INTERIOR COLOUR PALETTE CONSULTATION REPORT",
        "=" * 70,
        f"Generated: {palette.name}",
        f"Room Type: {room_type} (Detected: {room_analysis.detected_room_type})",
        f"Interior Style: {room_analysis.detected_style}",
        f"Analysis Provider: {room_analysis.provider_name}",
        f"Atmosphere Goal: {palette.atmosphere}",
        "",
        "-" * 70,
        " 1. ROOM OBSERVATIONS & LIGHTING ANALYSIS",
        "-" * 70,
        f"• Apparent Lighting: {room_analysis.apparent_lighting}",
        f"• Overall Brightness: {extracted.overall_brightness:.1%} ({room_analysis.brightness_level.upper()})",
        f"• Ambient Temperature Tendency: {extracted.overall_temperature_tendency.upper()}",
        f"• Existing Wall Base: {room_analysis.existing_wall_description}",
        f"• Flooring Base: {room_analysis.flooring_description}",
        "",
        "Key Design Strengths:",
    ]
    for s in room_analysis.design_strengths:
        lines.append(f"  + {s}")

    lines.append("")
    lines.append("Design Challenges & Optical Considerations:")
    for c in room_analysis.design_challenges:
        lines.append(f"  - {c}")

    lines.extend([
        "",
        "-" * 70,
        " 2. EXTRACTED DOMINANT COLOURS (FROM PHOTOGRAPH)",
        "-" * 70
    ])
    for sw in extracted.dominant_colors[:6]:
        lines.append(f"• {sw.role}: {sw.name} | HEX: {sw.hex} | RGB: {sw.rgb} | {sw.description}")

    lines.extend([
        "",
        "-" * 70,
        f" 3. RECOMMENDED PALETTE: {palette.name.upper()}",
        "-" * 70,
        f"Concept Category: {palette.concept_category}",
        f"Harmony System:   {palette.harmony_type}",
        f"Design Match Score: {palette.heuristic_score} / 100",
        "",
        "COLOUR SPECIFICATION:",
        f"1. Primary Wall (60%):",
        f"   Name: {palette.primary_wall.name} | HEX: {palette.primary_wall.hex} | RGB: {palette.primary_wall.rgb}",
        f"   Traits: {palette.primary_wall.description}",
        "",
        f"2. Secondary / Feature Wall (30%):",
        f"   Name: {palette.secondary_wall.name} | HEX: {palette.secondary_wall.hex} | RGB: {palette.secondary_wall.rgb}",
        f"   Traits: {palette.secondary_wall.description}",
        "",
        f"3. Accent Details (10%):",
        f"   Name: {palette.accent.name} | HEX: {palette.accent.hex} | RGB: {palette.accent.rgb}",
        f"   Traits: {palette.accent.description}",
        "",
        f"4. Architectural Trim & Ceiling:",
        f"   Name: {palette.trim.name} | HEX: {palette.trim.hex} | RGB: {palette.trim.rgb}",
        f"   Traits: {palette.trim.description}",
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
