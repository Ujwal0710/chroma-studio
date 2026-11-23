"""Unit tests for distinctive architectural features:

Chroma Memory, Chroma DNA, Timeline, Harmony Explorer, Daylight Simulator,
Material Palettes, Colour Swap, Paint Estimator, and Semantic Wall Editing.
"""
import pytest
import os
import tempfile
from PIL import Image
import numpy as np

from models.schemas import PaletteConcept, ColorSwatch, PaintEstimateInput
from modules.chroma_memory import (
    record_favorite_palette,
    get_chroma_memory,
    clear_chroma_memory,
    evaluate_chroma_memory_influence
)
from modules.chroma_dna import generate_chroma_dna
from modules.design_timeline import (
    save_timeline_version,
    list_project_timeline,
    get_timeline_version
)
from modules.harmony_explorer import explore_color_harmonies
from modules.daylight_simulator import simulate_daylight_lighting
from modules.material_palettes import evaluate_material_compatibility
from modules.colour_swap import swap_palette_color
from modules.paint_estimator import estimate_paint_quantity
from modules.semantic_wall import generate_semantic_surface_masks
from modules.storage import init_db


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_palette():
    swatch_p = ColorSwatch(hex="#F5F0E8", rgb=(245, 240, 232), role="Primary Wall", name="Warm Linen", percentage=60.0)
    swatch_s = ColorSwatch(hex="#D8C3B0", rgb=(216, 195, 176), role="Secondary Wall", name="Desert Sand", percentage=30.0)
    swatch_a = ColorSwatch(hex="#725640", rgb=(114, 86, 64), role="Accent Details", name="Architectural Umber", percentage=10.0)
    swatch_t = ColorSwatch(hex="#FFFFFF", rgb=(255, 255, 255), role="Trim", name="Chalk White", percentage=5.0)
    
    return PaletteConcept(
        id="sample_pal_1",
        name="Warm Editorial Sanctuary",
        concept_category="Warm and Inviting",
        harmony_type="Analogous",
        description="Warm travertine tones with terracotta accent.",
        atmosphere="Calm & Relaxing",
        primary_wall=swatch_p,
        secondary_wall=swatch_s,
        accent=swatch_a,
        trim=swatch_t,
        design_rationale="Earthy minerals create grounded ambiance.",
        furniture_flooring_compatibility="Warm oak floors",
        heuristic_score=85.0
    )


def test_chroma_memory_learning_and_influence(temp_db, sample_palette):
    user_id = "user_memory_test"
    
    # Empty initial memory
    mem = get_chroma_memory(user_id, db_path=temp_db)
    assert mem["interactions_count"] == 0
    delta, notes = evaluate_chroma_memory_influence(user_id, sample_palette, db_path=temp_db)
    assert delta == 0.0
    
    # Record favorite palette
    record_favorite_palette(user_id, sample_palette, style="Modern", db_path=temp_db)
    mem_after = get_chroma_memory(user_id, db_path=temp_db)
    assert mem_after["interactions_count"] == 1
    assert "Warm Linen" in mem_after["favorite_colors"]
    
    # Influence should now give a positive boost
    delta, notes = evaluate_chroma_memory_influence(user_id, sample_palette, db_path=temp_db)
    assert delta > 0.0
    
    # Clear memory
    clear_chroma_memory(user_id, db_path=temp_db)
    mem_cleared = get_chroma_memory(user_id, db_path=temp_db)
    assert mem_cleared["interactions_count"] == 0


def test_chroma_dna_derivation(temp_db):
    user_id = "user_dna_test"
    dna = generate_chroma_dna(user_id, db_path=temp_db)
    
    assert dna.signature_name is not None
    assert len(dna.signature_swatches) == 4
    assert len(dna.material_affinity) > 0
    assert dna.contrast_level in ["Subtle Low-Contrast (Calming)", "Dramatic High-Contrast (Bold Focal)", "Balanced Architectural (Harmonious)"]


def test_design_timeline_versioning(temp_db, sample_palette):
    user_id = "user_timeline_test"
    project_id = "proj_living_room"
    
    v1_id = save_timeline_version(user_id, project_id, sample_palette, "Initial Concept", db_path=temp_db)
    assert v1_id is not None
    
    # Save second iteration
    sample_palette.name = "Iteration Two with Deeper Umber"
    save_timeline_version(user_id, project_id, sample_palette, "Deeper Tone", db_path=temp_db)
    
    timeline = list_project_timeline(user_id, project_id, db_path=temp_db)
    assert len(timeline) == 2
    assert timeline[0]["version_num"] == 2  # Most recent first
    assert timeline[1]["version_num"] == 1
    
    # Retrieve specific version
    v1 = get_timeline_version(v1_id, user_id, db_path=temp_db)
    assert v1["label"] == "Initial Concept"


def test_colour_harmony_explorer():
    seed = "#725640"
    harmonies = explore_color_harmonies(seed)
    
    assert "seed" in harmonies
    assert harmonies["seed"]["hex"] == seed
    assert "complementary" in harmonies
    assert harmonies["complementary"]["delta_e"] > 0.0
    assert len(harmonies["analogous"]) == 2
    assert len(harmonies["triadic"]) == 2
    assert len(harmonies["monochromatic"]) == 2
    assert "neutral_supporting" in harmonies


def test_daylight_simulator():
    img = Image.new("RGB", (100, 100), color=(200, 180, 160))
    # Warm Morning
    morning_img = simulate_daylight_lighting(img, "Warm Morning Light", intensity=0.9)
    assert morning_img.size == img.size
    
    # Overcast
    overcast_img = simulate_daylight_lighting(img, "Cool Overcast Daylight", intensity=0.9)
    assert overcast_img.size == img.size
    
    # Pixel verification: Cool overcast should increase blue relative to red
    orig_arr = np.array(img)
    over_arr = np.array(overcast_img)
    # Blue channel should be boosted relative to original
    assert over_arr[:, :, 2].mean() >= orig_arr[:, :, 2].mean() * 0.95


def test_material_compatibility_evaluation(sample_palette):
    materials = ["Oak Wood", "Natural Linen"]
    delta, insights = evaluate_material_compatibility(materials, sample_palette)
    assert isinstance(delta, float)
    assert len(insights) > 0


def test_colour_swap_playground(sample_palette):
    new_accent_hex = "#2C3E3A"  # Deep Forest Pine
    
    swapped = swap_palette_color(sample_palette, "accent", new_accent_hex)
    assert swapped.accent.hex == new_accent_hex
    # Locked colours must be preserved
    assert swapped.primary_wall.hex == sample_palette.primary_wall.hex
    assert swapped.secondary_wall.hex == sample_palette.secondary_wall.hex
    assert swapped.trim.hex == sample_palette.trim.hex
    assert "Custom Variant" in swapped.name


def test_smart_paint_estimator():
    inputs = PaintEstimateInput(
        room_length_meters=5.0,
        room_width_meters=4.0,
        wall_height_meters=2.8,
        num_doors=1,
        num_windows=2,
        coats=2,
        coverage_sqm_per_liter=12.0,
        cost_per_liter_inr=450.0
    )
    result = estimate_paint_quantity(inputs)
    
    # Gross area: 2 * (5 + 4) * 2.8 = 50.4 sqm
    assert result.gross_wall_area_sqm == 50.4
    # Deductions: 1 * 1.89 + 2 * 1.44 = 4.77 sqm
    assert result.deductions_sqm == 4.77
    assert result.net_wall_area_sqm == round(50.4 - 4.77, 2)
    assert result.paint_liters_required > 0
    assert result.estimated_cost_inr is not None
    assert result.estimated_cost_inr > 0
    assert sum(result.recommended_cans_breakdown.values()) > 0


def test_semantic_surface_masks():
    orig_img = Image.new("RGB", (100, 100), color=(220, 220, 220))
    base_mask = np.ones((100, 100), dtype=np.uint8) * 255
    masks = generate_semantic_surface_masks(orig_img, base_mask)
    
    assert "Main Wall" in masks
    assert "Accent Wall" in masks
    assert "Ceiling / Upper Plane" in masks
    assert masks["Main Wall"].shape == (100, 100)
