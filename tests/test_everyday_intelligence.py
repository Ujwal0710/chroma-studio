"""Comprehensive automated tests for Everyday Intelligence and Live Camera Expansion.

Covers:
- Live Camera & Thread-Safe Frame Buffers
- Live Room Intelligence & Architectural Segmentation
- Live Colour Scanner & Reticle Sampling
- Paint Brand Matcher (Asian Paints, Berger, Nerolac, Dulux)
- Smart Furniture & Room Planner Clearances
- Renovation Shopping Assistant & INR Budgeting
- Home Maintenance Tracker & Condition Comparisons
- Chroma AI Contextual Assistant
- Database Persistence for all expansion features
"""
import pytest
import os
import tempfile
import numpy as np
from PIL import Image

from modules.live_camera import ThreadSafeFrameHolder, LiveVideoTransformer, is_webrtc_available
from modules.live_intelligence import analyze_live_frame_intelligence, draw_intelligence_bounding_boxes
from modules.live_colour_scanner import scan_color_at_reticle, scan_frame_dominant_palette, draw_reticle_crosshair
from modules.paint_brand_matcher import match_paint_brand_shades, get_available_brands
from modules.room_planner import check_room_clearances, get_furniture_suggestions
from modules.shopping_assistant import generate_renovation_shopping_list, export_shopping_list_markdown
from modules.home_maintenance import evaluate_wall_damage_heuristics, create_condition_comparison_image
from modules.chroma_assistant import generate_assistant_response
from models.schemas import PaletteConcept, ColorSwatch, PaintEstimateResult
from modules.storage import (
    init_db,
    save_scanned_color,
    list_scanned_colors,
    delete_scanned_color,
    save_room_plan,
    list_room_plans,
    delete_room_plan,
    save_shopping_list,
    list_shopping_lists,
    save_maintenance_record,
    list_maintenance_records,
    save_assistant_message,
    get_assistant_history,
    clear_assistant_history
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_test_palette():
    swatch_p = ColorSwatch(hex="#F5F0E8", rgb=(245, 240, 232), role="Primary Wall", name="Warm Linen", percentage=60.0)
    swatch_s = ColorSwatch(hex="#D8C3B0", rgb=(216, 195, 176), role="Secondary Wall", name="Desert Sand", percentage=30.0)
    swatch_a = ColorSwatch(hex="#B85C38", rgb=(184, 92, 56), role="Accent Details", name="Terracotta", percentage=10.0)
    swatch_t = ColorSwatch(hex="#FAF8F5", rgb=(250, 248, 245), role="Trim", name="Chalk White", percentage=5.0)

    return PaletteConcept(
        id="test_exp_pal",
        name="Santorini Terracotta",
        concept_category="Warm and Inviting",
        harmony_type="Analogous",
        description="Warm mineral aesthetic",
        atmosphere="Calm & Relaxing",
        primary_wall=swatch_p,
        secondary_wall=swatch_s,
        accent=swatch_a,
        trim=swatch_t,
        design_rationale="Grounded earth tones",
        furniture_flooring_compatibility="Warm Oak floors",
        heuristic_score=88.0
    )


# -------------------------------------------------------------
# 1. Live Camera Studio Tests
# -------------------------------------------------------------
def test_thread_safe_frame_holder():
    holder = ThreadSafeFrameHolder()
    assert holder.get_frame() is None

    # Push mock BGR frame
    dummy_bgr = np.zeros((120, 160, 3), dtype=np.uint8)
    dummy_bgr[:, :] = [100, 150, 200]
    holder.set_frame(dummy_bgr)

    retrieved = holder.get_frame()
    assert retrieved is not None
    assert retrieved.shape == (120, 160, 3)

    pil_img = holder.get_pil_image()
    assert isinstance(pil_img, Image.Image)
    assert pil_img.size == (160, 120)

    metrics = holder.get_metrics()
    assert metrics["has_frame"] is True
    assert metrics["resolution"] == (160, 120)


def test_webrtc_availability_and_transformer():
    assert isinstance(is_webrtc_available(), bool)
    transformer = LiveVideoTransformer()
    assert transformer.overlay_mode == "none"

    # Test quick wall overlay on synthetic frame
    dummy_bgr = np.ones((100, 100, 3), dtype=np.uint8) * 200
    transformer.target_rgb = (180, 100, 50)
    out = transformer._apply_quick_wall_overlay(dummy_bgr)
    assert out.shape == dummy_bgr.shape


# -------------------------------------------------------------
# 2. Live Room Intelligence Tests
# -------------------------------------------------------------
def test_live_frame_intelligence_detection():
    # Construct synthetic room with distinct floor, wall, and ceiling
    arr = np.zeros((200, 300, 3), dtype=np.uint8)
    arr[:40, :] = [240, 240, 240]    # Ceiling
    arr[40:150, :] = [225, 215, 200] # Wall
    arr[150:, :] = [80, 50, 30]      # Floor
    img = Image.fromarray(arr)

    res = analyze_live_frame_intelligence(img)
    assert res["elements_detected_count"] >= 3
    cats = res["categories"]
    assert "Wall" in cats
    assert "Floor" in cats
    assert "Ceiling" in cats

    # Check bounding box overlay
    overlay = draw_intelligence_bounding_boxes(img, res)
    assert overlay.size == img.size


# -------------------------------------------------------------
# 3. Live Colour Scanner Tests
# -------------------------------------------------------------
def test_live_colour_scanner_reticle_and_palette():
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[:, :] = [184, 92, 56] # Terracotta
    img = Image.fromarray(arr)

    # Reticle sample
    scanned = scan_color_at_reticle(img, 0.5, 0.5)
    assert scanned.hex.startswith("#")
    assert scanned.rgb[0] == 184
    assert scanned.rgb[1] == 92
    assert scanned.rgb[2] == 56
    assert scanned.temperature == "warm"

    # Reticle overlay
    cross_img = draw_reticle_crosshair(img, 0.5, 0.5)
    assert cross_img.size == img.size

    # Dominant cluster extraction
    palette = scan_frame_dominant_palette(img, k_clusters=3)
    assert len(palette) > 0
    assert palette[0].hex.startswith("#")


# -------------------------------------------------------------
# 4. Paint Brand Matcher Tests
# -------------------------------------------------------------
def test_paint_brand_matcher_indian_catalogue():
    brands = get_available_brands()
    assert "All Brands" in brands
    assert "Asian Paints" in brands
    assert "Berger Paints" in brands

    # Target: Rich Terracotta (#B85C38)
    target = (184, 92, 56)
    matches = match_paint_brand_shades(target, max_results=3)

    assert len(matches) <= 3
    top = matches[0]
    assert top["delta_e"] >= 0.0
    assert top["match_confidence"] > 70.0
    assert "brand" in top
    assert "shade_name" in top
    assert "shade_code" in top
    assert top["is_estimate"] is True

    # Filtered by brand
    asian_matches = match_paint_brand_shades(target, brand_filter="Asian Paints")
    assert all(m["brand"] == "Asian Paints" for m in asian_matches)


# -------------------------------------------------------------
# 5. Smart Furniture & Room Planner Tests
# -------------------------------------------------------------
def test_room_planner_clearances_and_suggestions():
    suggestions = get_furniture_suggestions("Living Room")
    assert len(suggestions) >= 4

    # Generous room clearance check (5.0m x 4.0m = 20 sqm)
    checks = check_room_clearances(5.0, 4.0, suggestions[:3])
    assert len(checks) >= 2
    assert any(c["check"] == "Overall Floor Occupancy" for c in checks)

    # Narrow room warning (2.2m width)
    narrow_checks = check_room_clearances(5.0, 2.2, suggestions)
    corridor_check = next((c for c in narrow_checks if "Circulation" in c["check"]), None)
    assert corridor_check is not None
    assert corridor_check["status"] == "caution"


# -------------------------------------------------------------
# 6. Renovation Shopping Assistant Tests
# -------------------------------------------------------------
def test_renovation_shopping_list_generation(sample_test_palette):
    estimate = PaintEstimateResult(
        gross_wall_area_sqm=50.0,
        deductions_sqm=4.5,
        net_wall_area_sqm=45.5,
        total_coated_area_sqm=91.0,
        paint_liters_required=8.5,
        recommended_cans_breakdown={"10-Litre Buckets": 0, "4-Litre Tins": 2, "1-Litre Cans": 1},
        estimated_cost_inr=3825.0
    )

    shop_data = generate_renovation_shopping_list(sample_test_palette, estimate, room_type="Master Suite")
    assert len(shop_data["items"]) >= 5
    assert shop_data["essential_budget_inr"] > 0
    assert shop_data["total_budget_inr"] >= shop_data["essential_budget_inr"]

    # Markdown table export
    md_table = export_shopping_list_markdown(shop_data)
    assert "# Renovation Shopping List" in md_table
    assert "Primary Wall" in md_table
    assert "₹" in md_table


# -------------------------------------------------------------
# 7. Home Maintenance Tracker Tests
# -------------------------------------------------------------
def test_home_maintenance_heuristics_and_comparison():
    res = evaluate_wall_damage_heuristics("Hairline Cracks", "Minor (<1mm)")
    assert res["urgency"] == "Medium"
    assert "crack filler" in res["treatment_protocol"].lower()

    # Before-and-after side-by-side comparison
    im1 = Image.new("RGB", (120, 100), (220, 220, 220))
    im2 = Image.new("RGB", (120, 100), (200, 180, 160))
    cmp = create_condition_comparison_image(im1, im2, "Jan 2026", "Nov 2026")
    assert cmp.size[0] > 240
    assert cmp.size[1] >= 600


# -------------------------------------------------------------
# 8. Chroma AI Assistant Tests
# -------------------------------------------------------------
def test_chroma_assistant_contextual_responses():
    # Query with keyword match (daylight orientation)
    ans1 = generate_assistant_response("How does north-facing morning sunlight affect paint?")
    assert "North-Facing" in ans1
    assert "Kelvin" in ans1 or "diffuse" in ans1

    # Query with accent wall
    ans2 = generate_assistant_response("Which wall should I choose as the accent wall?")
    assert "Focal Point" in ans2

    # Contextual query with active palette
    ctx = {
        "active_palette": {"name": "Terracotta Sunset", "concept_category": "Warm", "harmony_type": "Analogous"},
        "room_type": "Living Room",
        "selected_materials": ["Oak Wood", "Natural Linen"]
    }
    ans3 = generate_assistant_response("Suggest coordinating curtains and furniture.", context=ctx)
    assert "Context Active" in ans3 or "Terracotta Sunset" in ans3


# -------------------------------------------------------------
# 9. Database CRUD Tests for Expansion Subsystems
# -------------------------------------------------------------
def test_database_expansion_crud(temp_db):
    user_id = "test_user_expansion"

    # Scanned color
    col_id = save_scanned_color(user_id, {
        "name": "Terracotta Rust",
        "hex": "#B85C38",
        "rgb": (184, 92, 56),
        "hsv": (16.9, 0.70, 0.72),
        "lab": (49.5, 36.2, 34.1),
        "temperature": "warm"
    }, db_path=temp_db)
    assert col_id.startswith("col_")
    cols = list_scanned_colors(user_id, db_path=temp_db)
    assert len(cols) == 1
    assert cols[0]["hex"] == "#B85C38"

    # Delete scanned color
    assert delete_scanned_color(col_id, user_id, db_path=temp_db) is True
    assert len(list_scanned_colors(user_id, db_path=temp_db)) == 0

    # Room plan
    plan_id = save_room_plan(user_id, {
        "name": "Living Room Minimalist Layout",
        "room_type": "Living Room",
        "length_m": 5.2,
        "width_m": 4.1,
        "height_m": 2.9,
        "furniture": [{"item": "Sofa", "width_cm": 220}],
        "clearances": [{"check": "Door Swing", "status": "pass"}]
    }, db_path=temp_db)
    assert plan_id.startswith("plan_")
    plans = list_room_plans(user_id, db_path=temp_db)
    assert len(plans) == 1
    assert plans[0]["length_m"] == 5.2
    assert delete_room_plan(plan_id, user_id, db_path=temp_db) is True

    # Shopping list
    shop_id = save_shopping_list(user_id, {
        "project_name": "Studio Renovation",
        "items": [{"item_name": "Primer", "quantity": 1}],
        "total_budget_inr": 4500.0
    }, db_path=temp_db)
    assert shop_id.startswith("shop_")
    shops = list_shopping_lists(user_id, db_path=temp_db)
    assert len(shops) == 1
    assert shops[0]["total_budget_inr"] == 4500.0

    # Maintenance record
    maint_id = save_maintenance_record(user_id, {
        "room_name": "Master Suite",
        "damage_type": "Hairline Cracks",
        "severity": "Minor (<1mm)",
        "maintenance_activity": "Filled and sanded",
        "reminder_date": "2026-12-01"
    }, db_path=temp_db)
    assert maint_id.startswith("maint_")
    records = list_maintenance_records(user_id, db_path=temp_db)
    assert len(records) == 1
    assert records[0]["damage_type"] == "Hairline Cracks"

    # Assistant conversation history
    save_assistant_message(user_id, "sess_1", "user", "What paint finish should I use?", db_path=temp_db)
    save_assistant_message(user_id, "sess_1", "assistant", "Use eggshell for walls.", db_path=temp_db)
    history = get_assistant_history(user_id, "sess_1", db_path=temp_db)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    clear_assistant_history(user_id, "sess_1", db_path=temp_db)
    assert len(get_assistant_history(user_id, "sess_1", db_path=temp_db)) == 0
