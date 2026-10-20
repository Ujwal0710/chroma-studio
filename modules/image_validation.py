"""Image validation, sanitation, and EXIF orientation handling."""
import io
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageOps

from config.settings import (
    MAX_IMAGE_SIZE_BYTES,
    MAX_IMAGE_SIZE_MB,
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    PROCESSING_MAX_DIMENSION
)


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation."""
    pass


def get_image_metadata(
    img: Image.Image,
    raw_bytes: bytes,
    filename: str = "",
    detected_format: str = ""
) -> Dict[str, Any]:
    """Extract metadata including dimensions, format, color mode, and file size."""
    width, height = img.size
    aspect_ratio = round(width / max(height, 1), 2)
    size_kb = round(len(raw_bytes) / 1024, 1)
    size_mb = round(len(raw_bytes) / (1024 * 1024), 2)

    fmt = detected_format or img.format or "Unknown"

    return {
        "filename": filename or "uploaded_room_image",
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "format": fmt,
        "mode": img.mode,
        "size_kb": size_kb,
        "size_mb": size_mb,
        "megapixels": round((width * height) / 1_000_000, 2)
    }


def validate_image_bytes(
    file_bytes: bytes,
    filename: str = ""
) -> Tuple[Image.Image, Image.Image, Dict[str, Any]]:
    """
    Validate, sanitize, fix EXIF orientation, and prepare images for display and processing.

    Returns:
        Tuple of (original_image, processing_image, metadata)
    Raises:
        ImageValidationError: If image is corrupt, empty, oversized, or unsupported format.
    """
    if not file_bytes:
        raise ImageValidationError("The uploaded file is empty. Please select a valid room image.")

    file_size = len(file_bytes)
    if file_size > MAX_IMAGE_SIZE_BYTES:
        raise ImageValidationError(
            f"Image size ({round(file_size / (1024*1024), 2)} MB) exceeds the maximum allowed limit of {MAX_IMAGE_SIZE_MB} MB."
        )

    # Extension check if filename provided
    if filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext and ext not in ALLOWED_EXTENSIONS:
            allowed_str = ", ".join(ALLOWED_EXTENSIONS)
            raise ImageValidationError(
                f"Unsupported file extension '{ext}'. Allowed extensions: {allowed_str}."
            )

    # Magic byte check for standard formats
    # JPEG: FF D8 FF
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    # WEBP: RIFF....WEBP
    is_jpeg = file_bytes.startswith(b"\xff\xd8\xff")
    is_png = file_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = len(file_bytes) > 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP"

    if not (is_jpeg or is_png or is_webp):
        raise ImageValidationError(
            "Uploaded file header does not match a supported image format (JPEG, PNG, or WEBP)."
        )

    # Attempt opening and verifying with Pillow
    try:
        raw_stream = io.BytesIO(file_bytes)
        test_img = Image.open(raw_stream)
        test_img.verify()
    except Exception as e:
        raise ImageValidationError(f"Corrupted or unreadable image file: {str(e)}")

    # Re-open stream for actual processing (verify closes stream in Pillow)
    raw_stream = io.BytesIO(file_bytes)
    try:
        img = Image.open(raw_stream)
        detected_format = img.format or ("JPEG" if is_jpeg else ("PNG" if is_png else ("WEBP" if is_webp else "Unknown")))
        img.load()  # Force decode into memory
    except Exception as e:
        raise ImageValidationError(f"Failed to decode image data: {str(e)}")

    # Correct EXIF orientation
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass  # If EXIF reading fails, keep original orientation

    # Ensure standard RGB mode (strip alpha or palette safely)
    if img.mode != "RGB":
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            # Convert with white background
            bg = Image.new("RGB", img.size, (255, 255, 255))
            rgba_img = img.convert("RGBA")
            bg.paste(rgba_img, mask=rgba_img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")

    metadata = get_image_metadata(img, file_bytes, filename, detected_format=detected_format)

    # Check minimum dimensions (too small won't provide meaningful room analysis)
    if img.width < 100 or img.height < 100:
        raise ImageValidationError(
            f"Image resolution ({img.width}x{img.height}) is too small. Please upload an image with at least 100x100 resolution."
        )

    # Create resized version for fast CV processing while keeping original
    proc_img = img.copy()
    if max(proc_img.size) > PROCESSING_MAX_DIMENSION:
        proc_img.thumbnail((PROCESSING_MAX_DIMENSION, PROCESSING_MAX_DIMENSION), Image.Resampling.LANCZOS)

    return img, proc_img, metadata
