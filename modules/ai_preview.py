"""AI room preview integration boundary."""
from typing import Optional, Tuple, Dict, Any
from PIL import Image

from models.schemas import PaletteConcept
from services.image_editing_provider import generate_ai_room_preview


def request_ai_enhanced_preview(
    original_img: Image.Image,
    palette: PaletteConcept,
    room_type: str = "Living Room",
    interior_style: str = "Modern",
    override_api_key: Optional[str] = None
) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
    """
    Request AI-enhanced preview from configured generative provider.
    """
    return generate_ai_room_preview(
        original_img=original_img,
        palette=palette,
        room_type=room_type,
        interior_style=interior_style,
        override_api_key=override_api_key
    )
