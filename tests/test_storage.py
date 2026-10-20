"""Tests for SQLite database persistence, retrieval, deletion, and exports."""
import os
import json
import tempfile
import pytest

from models.schemas import PaletteConcept, ColorSwatch, PreferenceSettings, RoomAnalysisResult, ExtractedColorAnalysis
from modules.storage import (
    init_db,
    save_palette,
    list_saved_palettes,
    get_saved_palette_by_id,
    delete_saved_palette,
    save_user_preferences_preset,
    list_saved_preferences_presets
)
from modules.export_service import (
    export_palette_json,
    export_palette_csv,
    generate_swatch_sheet_png,
    generate_text_report
)


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass


def create_sample_palette() -> PaletteConcept:
    """Create a sample palette for persistence tests."""
    return PaletteConcept(
        id="pal-test-123",
        name="Desert Alabaster Suite",
        concept_category="Warm and Inviting",
        harmony_type="Analogous Harmony",
        description="Warm sandy tones for a cozy atmosphere.",
        atmosphere="Warm and peaceful",
        primary_wall=ColorSwatch(hex="#EAD8C2", rgb=(234, 216, 194), role="Primary Wall (60%)", name="Desert Sand"),
        secondary_wall=ColorSwatch(hex="#D4BBA2", rgb=(212, 187, 162), role="Secondary Wall (30%)", name="Pale Oat"),
        accent=ColorSwatch(hex="#B86C45", rgb=(184, 108, 69), role="Accent (10%)", name="Terracotta Clay"),
        trim=ColorSwatch(hex="#FBF8F3", rgb=(251, 248, 243), role="Trim & Ceiling", name="Alabaster White"),
        proportions={"Primary Wall": "60%", "Secondary Wall / Trim": "30%", "Accent Accents": "10%"},
        design_rationale="Coordinates with ambient daylight.",
        furniture_flooring_compatibility="Elevates light oak flooring."
    )


def test_sqlite_save_and_retrieve(temp_db):
    """Requirement 10: Saving and retrieving palettes from SQLite works."""
    pal = create_sample_palette()
    prefs = PreferenceSettings(temperature_preference="Warm")

    rec_id = save_palette(
        palette=pal,
        custom_name="Master Bedroom Desert Suite",
        room_type="Bedroom",
        interior_style="Minimalist",
        preferences=prefs,
        notes="Client requested warm undertones.",
        db_path=temp_db
    )

    assert rec_id.startswith("pal_")

    # Retrieve all
    saved_list = list_saved_palettes(db_path=temp_db)
    assert len(saved_list) == 1
    rec = saved_list[0]

    assert rec["id"] == rec_id
    assert rec["name"] == "Master Bedroom Desert Suite"
    assert rec["room_type"] == "Bedroom"
    assert rec["interior_style"] == "Minimalist"
    assert rec["palette"]["primary_wall"]["hex"] == "#EAD8C2"
    assert rec["preferences"]["temperature_preference"] == "Warm"

    # Retrieve by ID
    by_id = get_saved_palette_by_id(rec_id, db_path=temp_db)
    assert by_id is not None
    assert by_id["name"] == "Master Bedroom Desert Suite"


def test_sqlite_deletion(temp_db):
    """Requirement 11: Deleting saved palettes works."""
    pal = create_sample_palette()
    rec_id = save_palette(pal, "Delete Me", "Living Room", "Modern", db_path=temp_db)

    assert len(list_saved_palettes(db_path=temp_db)) == 1

    # Delete
    deleted = delete_saved_palette(rec_id, db_path=temp_db)
    assert deleted is True

    # Verify empty
    assert len(list_saved_palettes(db_path=temp_db)) == 0
    assert get_saved_palette_by_id(rec_id, db_path=temp_db) is None


def test_json_and_csv_exports():
    """Requirement 12: JSON and CSV exports contain valid data."""
    pal = create_sample_palette()

    # 1. JSON Export
    json_out = export_palette_json(pal)
    parsed = json.loads(json_out)
    assert parsed["name"] == pal.name
    assert len(parsed["colors"]) == 4
    assert parsed["colors"][0]["hex"] == "#EAD8C2"
    assert parsed["colors"][2]["name"] == "Terracotta Clay"

    # 2. CSV Export
    csv_out = export_palette_csv(pal)
    lines = [line.strip() for line in csv_out.splitlines() if line.strip()]
    assert len(lines) >= 5  # Header + 4 colors
    assert "Role,Name,HEX,RGB" in lines[0]
    assert "#EAD8C2" in csv_out
    assert "#B86C45" in csv_out


def test_swatch_sheet_and_report_exports():
    """Verify PNG Swatch sheet and Text report generation."""
    pal = create_sample_palette()

    # PNG Swatch Sheet
    buf = generate_swatch_sheet_png(pal, room_type="Bedroom")
    assert buf.getvalue().startswith(b"\x89PNG\r\n\x1a\n")  # Valid PNG signature
    assert len(buf.getvalue()) > 5000

    # Text report
    extracted = ExtractedColorAnalysis(
        dominant_colors=[pal.primary_wall, pal.accent],
        overall_brightness=0.65,
        overall_temperature_tendency="warm",
        mean_saturation=0.25,
        neutral_count=1,
        warm_count=2,
        cool_count=0,
        lighting_condition_estimate="Bright natural light"
    )
    room_analysis = RoomAnalysisResult(
        detected_room_type="Bedroom",
        detected_style="Modern",
        existing_wall_description="Alabaster base",
        flooring_description="Warm timber",
        apparent_lighting="Bright",
        recommended_direction="Warm tones",
        confidence_notes="Test",
        is_ai_inferred=False
    )

    report = generate_text_report(pal, room_analysis, extracted, room_type="Bedroom")
    assert "AI INTERIOR COLOUR PALETTE CONSULTATION REPORT" in report
    assert "#EAD8C2" in report
    assert "Warm and peaceful" in report
