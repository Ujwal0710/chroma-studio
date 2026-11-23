"""Renovation Shopping Assistant: Project bill of materials, quantities, and INR budgeting."""
from typing import Dict, Any, List, Optional
import math
from models.schemas import PaletteConcept, PaintEstimateResult


# Standard estimated rates in INR for essential painting & renovation tools
STANDARD_EQUIPMENT_PRICING = {
    "acrylic_primer": {"unit": "10-Litre Bucket", "cost_inr": 1850.0, "coverage_sqm": 110.0},
    "roller_kit": {"unit": "Set (9-inch Microfiber Roller + Tray)", "cost_inr": 380.0},
    "edging_brush": {"unit": "2.5-inch Synthetic Sash Brush", "cost_inr": 220.0},
    "detail_brush": {"unit": "1.5-inch Precision Cutting Brush", "cost_inr": 140.0},
    "masking_tape": {"unit": "Roll (24mm x 50m Painter's Blue Tape)", "cost_inr": 160.0},
    "drop_cloth": {"unit": "Heavy Duty Plastic Sheet (12x15 ft)", "cost_inr": 290.0},
    "sandpaper": {"unit": "Pack (120 & 180 Grit Emery Sheets)", "cost_inr": 120.0},
    "wall_putty": {"unit": "5kg Acrylic Wall Putty", "cost_inr": 340.0}
}


class ShoppingItem:
    """Individual renovation or interior shopping line item."""
    def __init__(
        self,
        category: str,  # 'Paint & Coating', 'Tools & Consumables', 'Lighting', 'Furniture', 'Decor'
        item_name: str,
        specification: str,
        quantity: float,
        unit: str,
        unit_price_inr: float,
        is_optional: bool = False
    ):
        self.category = category
        self.item_name = item_name
        self.specification = specification
        self.quantity = float(quantity)
        self.unit = unit
        self.unit_price_inr = float(unit_price_inr)
        self.total_price_inr = round(self.quantity * self.unit_price_inr, 2)
        self.is_optional = is_optional

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "item_name": self.item_name,
            "specification": self.specification,
            "quantity": self.quantity,
            "unit": self.unit,
            "unit_price_inr": self.unit_price_inr,
            "total_price_inr": self.total_price_inr,
            "is_optional": self.is_optional
        }


def generate_renovation_shopping_list(
    palette: PaletteConcept,
    paint_estimate: Optional[PaintEstimateResult] = None,
    room_type: str = "Living Room",
    include_furniture: bool = True
) -> Dict[str, Any]:
    """
    Generate an itemized renovation bill of materials based on room dimensions,
    paint requirements, and architectural design palette.
    """
    items: List[ShoppingItem] = []

    # 1. Paint Coatings
    liters_needed = paint_estimate.paint_liters_required if paint_estimate else 12.0
    paint_rate = 520.0  # INR/L average premium architectural interior paint
    items.append(ShoppingItem(
        category="Paint & Coating",
        item_name=f"Primary Wall Emulsion ({palette.primary_wall.name})",
        specification=f"HEX: {palette.primary_wall.hex} | 2 coats over primer | 60% Room Surface",
        quantity=round(liters_needed * 0.75, 1),
        unit="Litres",
        unit_price_inr=paint_rate
    ))

    items.append(ShoppingItem(
        category="Paint & Coating",
        item_name=f"Secondary / Accent Paint ({palette.secondary_wall.name})",
        specification=f"HEX: {palette.secondary_wall.hex} | Feature wall / millwork | 30% Area",
        quantity=round(max(2.0, liters_needed * 0.25), 1),
        unit="Litres",
        unit_price_inr=paint_rate + 40.0
    ))

    items.append(ShoppingItem(
        category="Paint & Coating",
        item_name=f"Accent Detail Enamel ({palette.accent.name})",
        specification=f"HEX: {palette.accent.hex} | Hardware, trim highlights or niche feature",
        quantity=1.0,
        unit="Litre Can",
        unit_price_inr=650.0,
        is_optional=True
    ))

    items.append(ShoppingItem(
        category="Paint & Coating",
        item_name="Interior Acrylic Wall Primer",
        specification="Water-based acrylic sealer ensuring uniform porosity & adhesion",
        quantity=max(1.0, math.ceil(liters_needed / 10.0)),
        unit="10-Litre Buckets",
        unit_price_inr=STANDARD_EQUIPMENT_PRICING["acrylic_primer"]["cost_inr"]
    ))

    # 2. Application Tools & Consumables
    items.append(ShoppingItem(
        category="Tools & Consumables",
        item_name="Microfiber Roller & Paint Tray Kit",
        specification="9-inch lint-free roller sleeve, ergonomic cage frame & textured tray",
        quantity=2.0,
        unit="Kits",
        unit_price_inr=STANDARD_EQUIPMENT_PRICING["roller_kit"]["cost_inr"]
    ))

    items.append(ShoppingItem(
        category="Tools & Consumables",
        item_name="Precision Sash & Cutting Brushes",
        specification="2.5-inch and 1.5-inch synthetic filament brushes for clean edges",
        quantity=2.0,
        unit="Brushes",
        unit_price_inr=STANDARD_EQUIPMENT_PRICING["edging_brush"]["cost_inr"]
    ))

    items.append(ShoppingItem(
        category="Tools & Consumables",
        item_name="Painter's Precision Masking Tape",
        specification="24mm clean-release blue paper tape for baseboards, switches & trim",
        quantity=3.0,
        unit="Rolls",
        unit_price_inr=STANDARD_EQUIPMENT_PRICING["masking_tape"]["cost_inr"]
    ))

    items.append(ShoppingItem(
        category="Tools & Consumables",
        item_name="Floor Protection Drop Cloths",
        specification="Heavy-duty 12x15 ft polyethylene waterproof dust & drip barrier",
        quantity=2.0,
        unit="Tarps",
        unit_price_inr=STANDARD_EQUIPMENT_PRICING["drop_cloth"]["cost_inr"]
    ))

    # 3. Lighting & Hardware
    items.append(ShoppingItem(
        category="Lighting",
        item_name="Warm Ambient Architectural Wall Sconces (Pair)",
        specification="2700K-3000K Warm white CRI > 90, brushed brass or matte charcoal finish",
        quantity=1.0,
        unit="Pair",
        unit_price_inr=3200.0,
        is_optional=True
    ))

    # 4. Furniture and Textiles (if requested)
    if include_furniture:
        items.append(ShoppingItem(
            category="Decor",
            item_name=f"Textured Throw Pillows / Accent Fabric ({palette.accent.name})",
            specification=f"Natural linen / velvet coordinating with {palette.accent.name}",
            quantity=2.0,
            unit="Pieces",
            unit_price_inr=850.0,
            is_optional=True
        ))

    total_cost = sum(item.total_price_inr for item in items if not item.is_optional)
    optional_cost = sum(item.total_price_inr for item in items if item.is_optional)

    return {
        "project_name": f"{palette.name} Renovation",
        "room_type": room_type,
        "items": [it.to_dict() for it in items],
        "essential_budget_inr": round(total_cost, 2),
        "optional_budget_inr": round(optional_cost, 2),
        "total_budget_inr": round(total_cost + optional_cost, 2)
    }


def export_shopping_list_markdown(shopping_data: Dict[str, Any]) -> str:
    """Format shopping list into clean markdown table and checklist."""
    lines = [
        f"# Renovation Shopping List — {shopping_data['project_name']}",
        f"**Room Type:** {shopping_data.get('room_type', 'Living Room')}  ",
        f"**Essential Budget:** ₹{shopping_data['essential_budget_inr']:,.2f}  ",
        f"**Total Budget (incl. optional):** ₹{shopping_data['total_budget_inr']:,.2f}",
        "",
        "---",
        "",
        "| Item | Category | Specification | Quantity | Unit Price (₹) | Total (₹) | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for it in shopping_data.get("items", []):
        opt_tag = "Optional" if it.get("is_optional") else "Essential"
        lines.append(
            f"| [ ] {it['item_name']} | {it['category']} | {it['specification']} | "
            f"{it['quantity']} {it['unit']} | ₹{it['unit_price_inr']:,.2f} | ₹{it['total_price_inr']:,.2f} | {opt_tag} |"
        )

    lines.extend([
        "",
        "---",
        "*Generated by CHROMA STUDIO AI Renovation Assistant.*"
    ])
    return "\n".join(lines)
