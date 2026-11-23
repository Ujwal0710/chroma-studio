"""Image upload handling, state caching, and cleanup."""
from typing import Tuple, Dict, Any
from PIL import Image
from modules.image_validation import validate_image_bytes


def process_uploaded_file(
    file_bytes: bytes,
    filename: str = ""
) -> Tuple[Image.Image, Image.Image, Dict[str, Any]]:
    """
    Validate, sanitize, and prepare uploaded image for display and computer-vision processing.
    """
    return validate_image_bytes(file_bytes, filename=filename)
