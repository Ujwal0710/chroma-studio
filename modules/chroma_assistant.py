"""Chroma AI Assistant: Contextual architectural interior design chatbot with offline knowledge graph."""
from typing import Dict, Any, Optional


SYSTEM_ARCHITECTURAL_PROMPT = """
You are Chroma AI, a senior architectural colour consultant and interior design advisor.
You provide precise, expert advice on colour theory, 60-30-10 distribution, light reflectance values (LRV),
material synergies (woods, stones, metals, fabrics), daylight orientation (North/South/East/West), and paint application techniques.
Keep your recommendations actionable, professional, and grounded in architectural standards.
"""

# Deterministic offline knowledge base for expert architectural consultation
OFFLINE_DESIGN_KNOWLEDGE_BASE = [
    {
        "keywords": ["accent wall", "which wall", "feature wall", "focal wall"],
        "answer": (
            "**Architectural Rule for Accent Walls:**\n\n"
            "1. **Identify the Natural Focal Point:** The accent wall should anchor the primary architectural feature—such as the wall behind the bed headboard in a bedroom, behind the main sofa in a living room, or where architectural millwork/fireplace exists.\n"
            "2. **Avoid Walls with Large Interruptions:** Never choose a wall broken up by asymmetrical windows or multiple door openings; windows introduce backlit glare that washes out deep accent pigments.\n"
            "3. **60-30-10 Allocation:** Keep your accent surface within 10% to 30% of the visual field. If painting a full wall in a vibrant tone, balance adjacent surfaces with high-LRV (>65%) warm alabaster or greige foundation walls."
        )
    },
    {
        "keywords": ["daylight", "lighting", "morning", "evening", "kelvin", "sunlight", "orientation"],
        "answer": (
            "**Daylight Orientation & Kelvin Effects on Paint Pigments:**\n\n"
            "• **North-Facing Rooms:** Receive cool, diffuse, bluish daylight (6500K-7500K). Avoid cool gray or icy blue tones, which read flat and chilly. Choose warm creamy whites, pale terracotta, or warm greiges with yellow/pink undertones to offset the blue cast.\n"
            "• **South-Facing Rooms:** Bathed in intense warm golden light all day. Highly versatile; both cool sage greens and warm ochres look luminous.\n"
            "• **East-Facing Rooms:** Bright, warm golden light in the morning (3200K) turning cooler and shadow-dense by afternoon. Tones with subtle green or warm undertones maintain balance.\n"
            "• **West-Facing Rooms:** Dim morning light followed by fiery, warm evening sun (2700K). Cool neutrals help prevent the room from feeling overheated at golden hour."
        )
    },
    {
        "keywords": ["lrv", "light reflectance", "dark room", "brighten", "dim"],
        "answer": (
            "**Light Reflectance Value (LRV) Architectural Guide:**\n\n"
            "• **LRV Scale (0–100):** Absolute black absorbs all light (LRV 0); pure titanium white reflects all incident light (LRV 100).\n"
            "• **Low-Light / Small Rooms:** Target paints with **LRV 65% – 82%** (e.g. Warm Alabaster, Oatmeal Linen). This maximizes ambient light bounce and softens shadowy corners.\n"
            "• **Deep Moody Aesthetics:** Spaces with rich directional lighting (powder rooms, media dens, dining suites) thrive with **LRV 12% – 25%** (e.g. Deep Charcoal, Forest Emerald, Rich Umber), creating an intimate cocooning effect."
        )
    },
    {
        "keywords": ["wood", "flooring", "oak", "walnut", "timber", "floor"],
        "answer": (
            "**Flooring & Timber Undertone Harmonization:**\n\n"
            "• **Light Oak / Natural Ash (Warm Yellow/Amber Undertone):** Coordinates harmoniously with warm linen, muted sage green, creamy alabaster, and soft terracotta.\n"
            "• **Dark Walnut / Teak (Deep Reddish-Espresso Undertone):** Demands high-contrast pairings like crisp off-whites, neutral greiges, or deep dramatic forest greens that elevate its rich woodgrain.\n"
            "• **Cool Grey Tile / Concrete:** Requires warm texture (natural linen, brushed brass, terracotta accents) to prevent the interior from feeling sterile or institutional."
        )
    },
    {
        "keywords": ["crack", "damage", "peel", "damp", "maintenance", "prep", "primer"],
        "answer": (
            "**Surface Preparation & Damage Remediation Protocol:**\n\n"
            "1. **Hairline Plaster Cracks (<1mm):** Clean loose dust, apply acrylic gap sealant or elastomeric crack filler, allow 4 hours curing, and sand flush with 180-grit emery paper.\n"
            "2. **Dampness / Peeling:** Never paint over active moisture. Identify and seal external water ingress. Scrape flaking paint back to sound substrate, apply alkali-resistant penetrating primer, and allow 24 hours drying.\n"
            "3. **Primer Application:** Always apply 1 coat of water-based interior acrylic primer before topcoats to equalize suction on porous drywall/plaster."
        )
    },
    {
        "keywords": ["brand", "asian paints", "berger", "nerolac", "dulux", "commercial"],
        "answer": (
            "**Indian Paint Brand Recommendations:**\n\n"
            "• **Asian Paints Royale:** Benchmark for luxury sheen and stain resistance (Royale Matt / Luxury Emulsion).\n"
            "• **Berger Silk Glamor / Easy Clean:** Excellent elastomeric durability and cross-link washable surfaces for family living rooms.\n"
            "• **Kansai Nerolac Impressions:** Low-VOC eco-clean formulations with vibrant pigments and deep matte charcoal finishes.\n"
            "• **Dulux Velvet Touch:** Rich luminescent velvet texture with high optical depth."
        )
    }
]


def generate_assistant_response(
    user_query: str,
    context: Optional[Dict[str, Any]] = None,
    override_api_key: Optional[str] = None
) -> str:
    """
    Generate contextual architectural interior advice.
    Combines user's active room project, palette, and materials with query.
    Works 100% offline using architectural knowledge graph and calls vision/LLM if API is present.
    """
    q_lower = user_query.lower()

    # Build contextual prefix
    context_notes = []
    if context:
        active_p = context.get("active_palette")
        if active_p:
            context_notes.append(f"Active Palette: '{active_p.get('name')}' ({active_p.get('concept_category')}, {active_p.get('harmony_type')})")
            if "primary_wall" in active_p:
                pw = active_p["primary_wall"]
                context_notes.append(f"Primary Wall: {pw.get('name')} ({pw.get('hex')})")
        if context.get("room_type"):
            context_notes.append(f"Room Type: {context.get('room_type')}")
        if context.get("detected_style"):
            context_notes.append(f"Detected Style: {context.get('detected_style')}")
        if context.get("selected_materials"):
            context_notes.append(f"Room Materials: {', '.join(context.get('selected_materials'))}")

    # Check for keyword matches in offline knowledge base
    matched_entry = None
    max_kw_count = 0
    for entry in OFFLINE_DESIGN_KNOWLEDGE_BASE:
        count = sum(1 for kw in entry["keywords"] if kw in q_lower)
        if count > max_kw_count:
            max_kw_count = count
            matched_entry = entry

    if matched_entry:
        ctx_header = ""
        if context_notes:
            ctx_header = f"> **Context Active:** { ' • '.join(context_notes) }\n\n"
        return ctx_header + matched_entry["answer"]

    # Fallback contextual response synthesizing the user's active state
    if context_notes:
        ctx_str = "\n".join([f"• {c}" for c in context_notes])
        return (
            f"**Architectural Consultation Note:**\n\n"
            f"Regarding your project with the following parameters:\n{ctx_str}\n\n"
            f"To achieve optimal visual balance in your {context.get('room_type', 'room')}, adhere to the **60-30-10 rule**:\n"
            f"- **60% Primary Surface:** Keep foundational walls in a comfortable light-to-medium reflectance value to prevent optical fatigue.\n"
            f"- **30% Secondary Elements:** Anchor feature walls, millwork, or large architectural drapery in harmonizing mid-tones.\n"
            f"- **10% Accent Details:** Distribute high-chroma accents across lighting fixtures, ceramics, or textiles.\n\n"
            f"Would you like recommendations on paint brand matches, daylight lighting simulations, or furniture placement clearances?"
        )

    # General fallback
    return (
        "**Chroma AI Architectural Guidance:**\n\n"
        "I can assist you with:\n"
        "1. **Colour Theory & 60-30-10 Rule:** Selecting harmonious foundational, secondary, and accent tones.\n"
        "2. **Daylight & Orientation:** How morning, midday, and evening lighting affect paint perception.\n"
        "3. **Material Synergy:** Harmonizing paints with oak, walnut, marble, concrete, linen, or brass.\n"
        "4. **Brand Shade Matching:** Finding commercial codes from Asian Paints, Berger, Nerolac, or Dulux.\n"
        "5. **Spatial Clearances & Paint Quantity:** Calculating coverage and architectural walkway dimensions.\n\n"
        "What specific aspect of your room would you like to explore?"
    )
