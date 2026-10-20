"""Tests for external AI service resilience, fallback triggers, and offline operation."""
from PIL import Image
from unittest.mock import patch

from models.schemas import ExtractedColorAnalysis, ColorSwatch, PaletteConcept
from services.vision_provider import perform_room_analysis, generate_local_rule_based_analysis
from services.image_editing_provider import generate_ai_room_preview


def get_mock_extracted_simple() -> ExtractedColorAnalysis:
    swatch = ColorSwatch(hex="#D9C5B2", rgb=(217, 197, 178), role="Dominant #1", name="Pale Oat", luminance=0.6, percentage=60.0)
    return ExtractedColorAnalysis(
        dominant_colors=[swatch],
        overall_brightness=0.60,
        overall_temperature_tendency="neutral",
        mean_saturation=0.15,
        neutral_count=1,
        warm_count=0,
        cool_count=0,
        lighting_condition_estimate="Moderate daylight"
    )


def test_missing_api_credentials_triggers_controlled_fallback():
    """Requirement 13: Missing API credentials trigger a controlled fallback."""
    img = Image.new("RGB", (100, 100), (220, 200, 180))
    extracted = get_mock_extracted_simple()

    # Pass empty override_api_key (simulating no API credentials)
    result = perform_room_analysis(
        img=img,
        extracted_analysis=extracted,
        selected_room_type="Living Room",
        selected_style="Scandinavian",
        override_api_key=""
    )

    # Must succeed without throwing
    assert result is not None
    assert result.is_ai_inferred is False
    assert "Local" in result.provider_name
    assert result.detected_room_type == "Living Room"
    assert result.detected_style == "Scandinavian"


def test_provider_failure_does_not_crash_application():
    """Requirement 14: Provider failures do not crash the entire application."""
    img = Image.new("RGB", (100, 100), (220, 200, 180))
    extracted = get_mock_extracted_simple()

    # Mock call_gemini_vision to simulate network timeout / auth failure
    with patch("services.vision_provider.call_gemini_vision", side_effect=RuntimeError("Connection timed out after 30s")):
        result = perform_room_analysis(
            img=img,
            extracted_analysis=extracted,
            override_api_key="fake-test-key-12345"
        )

        assert result is not None
        assert result.is_ai_inferred is False
        assert "failed" in result.confidence_notes.lower()
        # Fallback fields are populated
        assert len(result.dominant_color_observations) > 0
        assert result.apparent_lighting


def test_image_edit_provider_handles_missing_keys_gracefully():
    """Verify image edit provider does not crash and provides clear feedback when key is missing."""
    img = Image.new("RGB", (100, 100), (200, 200, 200))
    pal = PaletteConcept(
        id="test-pal",
        name="Test Suite",
        concept_category="Modern Neutral",
        harmony_type="Neutral",
        description="Test",
        atmosphere="Calm",
        primary_wall=ColorSwatch(hex="#D9C5B2", rgb=(217, 197, 178)),
        secondary_wall=ColorSwatch(hex="#C5B09D", rgb=(197, 176, 157)),
        accent=ColorSwatch(hex="#8B4513", rgb=(139, 69, 19)),
        trim=ColorSwatch(hex="#FFFFFF", rgb=(255, 255, 255)),
        design_rationale="Test",
        furniture_flooring_compatibility="Test"
    )

    gen_img, meta = generate_ai_room_preview(img, pal, override_api_key="")
    assert gen_img is None
    assert meta["success"] is False
    assert meta["status"] == "not_configured"
    assert "not configured" in meta["message"]


def test_application_can_start_without_paid_ai_services():
    """Requirement 15: The application can start without paid AI services."""
    # Test importing app modules without errors
    import config.settings as settings
    import modules.image_validation as img_val
    import modules.colour_extraction as col_ext
    import modules.palette_engine as pal_eng
    import modules.room_visualization as room_vis
    import modules.storage as storage

    # Initialize DB in-memory
    storage.init_db(":memory:")
    assert True


def test_analyze_room_photograph_supports_omitted_extracted_analysis():
    """Verify analyze_room_photograph works gracefully when extracted_analysis is omitted or None."""
    from modules.room_analysis import analyze_room_photograph
    img = Image.new("RGB", (80, 80), (210, 190, 170))
    # Call with ONLY img
    result = analyze_room_photograph(img)
    assert result is not None
    assert result.detected_room_type is not None
    assert result.detected_style is not None
    assert "Local" in result.provider_name


def test_env_path_anchored_to_project_root():
    """Verify .env path is resolved from project base directory regardless of cwd."""
    from config.settings import BASE_DIR, ENV_PATH
    assert ENV_PATH == BASE_DIR / ".env"
    assert ENV_PATH.is_absolute()


def test_image_edit_status_detection_and_key_masking():
    """Verify status diagnostics detects presence of key without exposing the raw secret."""
    from services.image_editing_provider import get_image_editing_status, mask_api_key
    
    # 1. Unconfigured scenario
    status_unconf = get_image_editing_status(override_api_key="")
    assert status_unconf["is_configured"] is False
    assert status_unconf["masked_key"] is None
    assert "not detected" in status_unconf["message"]
    assert "Active" in status_unconf["mode1_status"]
    assert "Unavailable" in status_unconf["mode2_status"]
    
    # 2. Configured scenario
    raw_secret = "sk-proj-testSecretKeyValue987654321"
    status_conf = get_image_editing_status(override_api_key=raw_secret)
    assert status_conf["is_configured"] is True
    assert status_conf["masked_key"] is not None
    # Crucial security check: raw secret must NEVER be exposed
    assert raw_secret not in status_conf["masked_key"]
    assert raw_secret not in status_conf["message"]
    assert status_conf["masked_key"].startswith("sk-p")
    assert status_conf["masked_key"].endswith("4321")
    assert "Ready" in status_conf["mode2_status"]


def test_image_edit_provider_with_valid_credentials_and_mocked_api():
    """Verify provider generates preview image when valid credentials and provider response are returned."""
    import base64
    import io
    from unittest.mock import patch, MagicMock
    from services.image_editing_provider import generate_ai_room_preview
    
    img = Image.new("RGB", (100, 100), (200, 200, 200))
    pal = PaletteConcept(
        id="test-pal-gen",
        name="Test Harmony",
        concept_category="Modern Neutral",
        harmony_type="Neutral",
        description="Test",
        atmosphere="Calm",
        primary_wall=ColorSwatch(hex="#D9C5B2", rgb=(217, 197, 178)),
        secondary_wall=ColorSwatch(hex="#C5B09D", rgb=(197, 176, 157)),
        accent=ColorSwatch(hex="#8B4513", rgb=(139, 69, 19)),
        trim=ColorSwatch(hex="#FFFFFF", rgb=(255, 255, 255)),
        design_rationale="Test",
        furniture_flooring_compatibility="Test"
    )
    
    # Create synthetic return image b64
    fake_ret_img = Image.new("RGB", (64, 64), (180, 120, 90))
    buf = io.BytesIO()
    fake_ret_img.save(buf, format="PNG")
    b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [{"b64_json": b64_data}]
    }
    mock_resp.raise_for_status = MagicMock()
    
    with patch("requests.post", return_value=mock_resp):
        gen_img, meta = generate_ai_room_preview(
            original_img=img,
            palette=pal,
            override_api_key="sk-test-mocked-key"
        )
        assert gen_img is not None
        assert meta["success"] is True
        assert meta["status"] == "generated"
        assert "OpenAI" in meta["provider"]


def test_image_edit_provider_handles_api_failure_gracefully():
    """Verify provider failure returns clean error metadata and does not crash."""
    from unittest.mock import patch
    import requests
    from services.image_editing_provider import generate_ai_room_preview
    
    img = Image.new("RGB", (100, 100), (200, 200, 200))
    pal = PaletteConcept(
        id="test-pal-fail",
        name="Test Harmony",
        concept_category="Modern Neutral",
        harmony_type="Neutral",
        description="Test",
        atmosphere="Calm",
        primary_wall=ColorSwatch(hex="#D9C5B2", rgb=(217, 197, 178)),
        secondary_wall=ColorSwatch(hex="#C5B09D", rgb=(197, 176, 157)),
        accent=ColorSwatch(hex="#8B4513", rgb=(139, 69, 19)),
        trim=ColorSwatch(hex="#FFFFFF", rgb=(255, 255, 255)),
        design_rationale="Test",
        furniture_flooring_compatibility="Test"
    )
    
    with patch("requests.post", side_effect=requests.exceptions.HTTPError("401 Client Error: Unauthorized")):
        gen_img, meta = generate_ai_room_preview(
            original_img=img,
            palette=pal,
            override_api_key="sk-invalid-test-key"
        )
        assert gen_img is None
        assert meta["success"] is False
        assert meta["status"] == "error"
        assert "HTTPError" in meta["message"]
        assert "Local preview remains fully operational" in meta["message"]


