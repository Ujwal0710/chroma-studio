"""Unit tests for user profiles, theme persistence, personal data export, and cascading account deletion."""
import pytest
import os
import tempfile

from models.schemas import PaletteConcept, ColorSwatch
from modules.storage import (
    init_db,
    create_user_record,
    get_user_profile,
    update_user_profile,
    save_palette,
    list_saved_palettes,
    export_user_data_bundle,
    delete_user_account_cascade
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_user_profile_crud_and_theme_persistence(temp_db):
    user = create_user_record(
        email="architect@chromastudio.ai",
        password_hash="mock_hash",
        salt="mock_salt",
        full_name="Sarah Hadid",
        db_path=temp_db
    )
    user_id = user["id"]
    
    # Check default profile
    profile = get_user_profile(user_id, db_path=temp_db)
    assert profile is not None
    assert profile["theme"] == "light"
    assert profile["display_name"] == "Sarah Hadid"
    
    # Update profile to dark theme and custom preferences
    update_user_profile(user_id, {
        "display_name": "Dame Sarah Hadid",
        "theme": "dark",
        "preferred_language": "Hindi",
        "default_room_type": "Dining Room",
        "default_interior_style": "Minimalist",
        "liked_colors": ["Warm Linen", "Architectural Charcoal"]
    }, db_path=temp_db)
    
    updated = get_user_profile(user_id, db_path=temp_db)
    assert updated["theme"] == "dark"
    assert updated["display_name"] == "Dame Sarah Hadid"
    assert "Architectural Charcoal" in updated["liked_colors"]


def test_personal_data_export_and_account_deletion(temp_db):
    user = create_user_record(
        email="client@chromastudio.ai",
        password_hash="mock_hash",
        salt="mock_salt",
        full_name="David Chipperfield",
        db_path=temp_db
    )
    user_id = user["id"]
    
    # Save a palette under this user
    dummy_swatch = ColorSwatch(hex="#F5F0E8", rgb=(245, 240, 232), role="Wall", name="Warm Linen")
    sample_pal = PaletteConcept(
        id="pal_del_test",
        name="Saved Sanctuary",
        concept_category="Warm and Inviting",
        harmony_type="Monochromatic",
        description="Test palette",
        atmosphere="Calm & Relaxing",
        primary_wall=dummy_swatch,
        secondary_wall=dummy_swatch,
        accent=dummy_swatch,
        trim=dummy_swatch,
        design_rationale="Rationale",
        furniture_flooring_compatibility="Compatibility"
    )
    save_palette(sample_pal, "Saved Sanctuary", "Living Room", "Modern", user_id=user_id, db_path=temp_db)
    
    palettes_before = list_saved_palettes(user_id=user_id, db_path=temp_db)
    assert len(palettes_before) == 1
    
    # Export data bundle
    export_bundle = export_user_data_bundle(user_id, db_path=temp_db)
    assert export_bundle["user_account"]["email"] == "client@chromastudio.ai"
    assert export_bundle["saved_palettes_count"] == 1
    
    # Cascading Account Deletion
    del_ok = delete_user_account_cascade(user_id, db_path=temp_db)
    assert del_ok is True
    
    # Verify everything purged
    palettes_after = list_saved_palettes(user_id=user_id, db_path=temp_db)
    assert len(palettes_after) == 0
    
    profile_after = get_user_profile(user_id, db_path=temp_db)
    assert profile_after is None
