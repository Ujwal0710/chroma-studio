"""Tests for image validation, decode safety, corrupt rejection, and orientation."""
import io
import pytest
from PIL import Image
from modules.image_validation import (
    validate_image_bytes,
    ImageValidationError
)


def create_synthetic_image(width: int = 400, height: int = 300, color=(200, 150, 100), fmt="JPEG") -> bytes:
    """Create a deterministic synthetic image in bytes."""
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    return buffer.getvalue()


def test_valid_image_decodes_successfully():
    """Requirement 1: Valid images upload and decode successfully."""
    raw_bytes = create_synthetic_image(width=500, height=400, color=(210, 180, 140), fmt="JPEG")
    orig_img, proc_img, metadata = validate_image_bytes(raw_bytes, filename="test_room.jpg")

    assert orig_img is not None
    assert orig_img.size == (500, 400)
    assert proc_img is not None
    assert metadata["format"] == "JPEG"
    assert metadata["width"] == 500
    assert metadata["height"] == 400
    assert metadata["aspect_ratio"] == 1.25


def test_png_and_webp_support():
    """Verify PNG and WEBP formats validate properly."""
    png_bytes = create_synthetic_image(fmt="PNG")
    orig, _, meta = validate_image_bytes(png_bytes, filename="test.png")
    assert meta["format"] == "PNG"

    webp_bytes = create_synthetic_image(fmt="WEBP")
    orig_w, _, meta_w = validate_image_bytes(webp_bytes, filename="test.webp")
    assert meta_w["format"] == "WEBP"


def test_corrupt_and_invalid_images_rejected():
    """Requirement 2: Invalid and corrupt images are rejected."""
    # 1. Empty bytes
    with pytest.raises(ImageValidationError, match="empty"):
        validate_image_bytes(b"", filename="empty.jpg")

    # 2. Corrupt fake bytes with valid extension
    corrupt_bytes = b"This is not a real image at all, just fake text data."
    with pytest.raises(ImageValidationError, match="format"):
        validate_image_bytes(corrupt_bytes, filename="corrupt.jpg")

    # 3. Valid JPEG header but truncated corrupted body
    truncated_header = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    with pytest.raises(ImageValidationError):
        validate_image_bytes(truncated_header, filename="truncated.jpg")

    # 4. Disallowed extension
    valid_bytes = create_synthetic_image()
    with pytest.raises(ImageValidationError, match="Unsupported file extension"):
        validate_image_bytes(valid_bytes, filename="test.exe")


def test_oversized_images_rejected():
    """Reject files larger than MAX_IMAGE_SIZE_MB."""
    # Test with fake oversize bytes
    from config.settings import MAX_IMAGE_SIZE_BYTES
    fake_oversized = b"\xff\xd8\xff" + b"\x00" * (MAX_IMAGE_SIZE_BYTES + 1024)
    with pytest.raises(ImageValidationError, match="exceeds the maximum allowed limit"):
        validate_image_bytes(fake_oversized, filename="huge.jpg")


def test_tiny_resolution_rejected():
    """Reject images smaller than 100x100 resolution."""
    tiny_bytes = create_synthetic_image(width=50, height=50)
    with pytest.raises(ImageValidationError, match="too small"):
        validate_image_bytes(tiny_bytes, filename="tiny.jpg")
