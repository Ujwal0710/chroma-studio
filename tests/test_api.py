"""Comprehensive REST API test suite for CHROMA STUDIO AI FastAPI Backend."""
import io
import uuid
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app

client = TestClient(app)


def create_test_image_bytes(w: int = 240, h: int = 180, color=(220, 205, 190)) -> io.BytesIO:
    img = Image.new("RGB", (w, h), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return buf


def test_health_check_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "offline_mode" in data


def test_auth_full_lifecycle():
    email = f"architect_test_{uuid.uuid4().hex[:8]}@atelier.com"
    pwd = "StrongDesignPassword#2026"
    
    # 1. Register
    reg_resp = client.post("/auth/register", json={
        "email": email,
        "full_name": "Test Architect",
        "password": pwd
    })
    # Either 201 or 400 if user already exists
    assert reg_resp.status_code in (201, 400)
    
    # 2. Login
    login_resp = client.post("/auth/login", json={
        "email": email,
        "password": pwd
    })
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.cookies
    cookie_token = login_resp.cookies["access_token"]
    
    # 3. Get profile /auth/me with cookie
    me_resp = client.get("/auth/me", cookies={"access_token": cookie_token})
    assert me_resp.status_code == 200
    assert me_resp.json()["authenticated"] is True
    assert me_resp.json()["user"]["email"] == email

    # 4. Password reset request
    reset_req = client.post("/auth/reset-request", json={"email": email})
    assert reset_req.status_code == 200
    dev_token = reset_req.json().get("dev_token")
    if dev_token:
        # Confirm reset
        conf_resp = client.post("/auth/reset-confirm", json={
            "token": dev_token,
            "new_password": "NewStrongPassword#2026"
        })
        assert conf_resp.status_code == 200

    # 5. Logout
    logout_resp = client.post("/auth/logout")
    assert logout_resp.status_code == 200


def test_rooms_sample_and_analyse():
    # 1. Sample room
    sample_resp = client.get("/rooms/sample")
    assert sample_resp.status_code == 200
    sample_data = sample_resp.json()
    assert sample_data["status"] == "success"
    assert sample_data["image_data_url"].startswith("data:image/jpeg;base64,")

    # 2. Analyse uploaded image
    img_buf = create_test_image_bytes()
    files = {"file": ("room.jpg", img_buf, "image/jpeg")}
    data = {"room_type": "Living Room", "interior_style": "Contemporary"}
    
    analyse_resp = client.post("/rooms/analyse", files=files, data=data)
    assert analyse_resp.status_code == 200
    res = analyse_resp.json()
    assert res["status"] == "success"
    assert len(res["dominant_tones"]["dominant_colors"]) > 0
    assert res["room_analysis"]["detected_room_type"] == "Living Room"


def test_rooms_segmentation_and_recolouring():
    # 1. Segmentation
    img_buf = create_test_image_bytes()
    files = {"file": ("room.jpg", img_buf, "image/jpeg")}
    seg_resp = client.post("/rooms/segment", files=files, data={"sensitivity": 0.55})
    assert seg_resp.status_code == 200
    seg_res = seg_resp.json()
    assert seg_res["status"] == "success"
    assert "mask_png" in seg_res
    assert seg_res["mask_png"].startswith("data:image/png;base64,")

    # 2. Recolour
    img_buf2 = create_test_image_bytes()
    files2 = {"file": ("room.jpg", img_buf2, "image/jpeg")}
    recol_resp = client.post("/rooms/recolour", files=files2, data={
        "target_hex": "#B85C38",
        "intensity": 0.85,
        "strategy": "cielab_perceptual"
    })
    assert recol_resp.status_code == 200
    recol_res = recol_resp.json()
    assert recol_res["status"] == "success"
    assert recol_res["recoloured_image"].startswith("data:image/jpeg;base64,")


def test_palettes_generate_and_swap():
    # 1. Generate palettes from extracted colors
    img_buf = create_test_image_bytes()
    files = {"file": ("room.jpg", img_buf, "image/jpeg")}
    analyse_resp = client.post("/rooms/analyse", files=files)
    analyse_data = analyse_resp.json()

    pal_req = {
        "extracted": analyse_data["dominant_tones"],
        "room_analysis": analyse_data["room_analysis"],
        "preferences": {
            "room_type": "Living Room",
            "desired_atmosphere": "Calm & Relaxing"
        }
    }
    gen_resp = client.post("/palettes/generate", json=pal_req)
    assert gen_resp.status_code == 200
    palettes = gen_resp.json()
    assert len(palettes) >= 4
    for p in palettes:
        assert p["primary_wall"]["percentage"] == 60.0
        assert p["secondary_wall"]["percentage"] == 30.0
        assert p["accent"]["percentage"] == 10.0

    # 2. Swap color in active palette
    active_pal = palettes[0]
    swap_req = {
        "palette": active_pal,
        "target_role": "accent",
        "new_hex": "#2C3E3A"
    }
    swap_resp = client.post("/palettes/swap", json=swap_req)
    assert swap_resp.status_code == 200
    swapped = swap_resp.json()
    assert swapped["accent"]["hex"].upper() == "#2C3E3A"
    assert swapped["primary_wall"]["hex"] == active_pal["primary_wall"]["hex"]

    # 3. Swap roles (from_role -> to_role)
    swap_role_resp = client.post("/palettes/swap", json={
        "palette": active_pal,
        "from_role": "primary_wall",
        "to_role": "secondary_wall"
    })
    assert swap_role_resp.status_code == 200
    swapped_role = swap_role_resp.json()
    assert swapped_role["primary_wall"]["hex"] == active_pal["secondary_wall"]["hex"]
    assert swapped_role["secondary_wall"]["hex"] == active_pal["primary_wall"]["hex"]


def test_palette_valid_and_invalid_validation_errors():
    """Verify palette generation handles valid requests and rejects invalid requests with detailed 422 errors."""
    # A. Valid request using primary_hex fallback
    valid_hex_req = {"primary_hex": "#B85C38", "room_type": "Living Room"}
    res_valid = client.post("/palettes/generate", json=valid_hex_req)
    assert res_valid.status_code == 200
    concepts = res_valid.json()
    assert len(concepts) == 4
    assert "colors" in concepts[0]
    assert len(concepts[0]["colors"]) == 4

    # B. Invalid request: empty body (missing extracted and primary_hex)
    res_empty = client.post("/palettes/generate", json={})
    assert res_empty.status_code == 422
    err_body = res_empty.json()
    assert err_body["code"] == 422
    assert "extracted" in err_body["detail"] or "primary_hex" in err_body["detail"]

    # C. Invalid request: malformed primary_hex
    res_bad_hex = client.post("/palettes/generate", json={"primary_hex": "NOT_A_HEX_CODE"})
    assert res_bad_hex.status_code == 422
    assert "Invalid primary_hex" in res_bad_hex.json()["detail"]


def test_lighting_and_materials_endpoints():
    # 1. Daylight conditions
    cond_resp = client.get("/daylight/conditions")
    assert cond_resp.status_code == 200
    assert "Warm Morning Light" in cond_resp.json()

    # 2. Daylight simulate
    img_buf = create_test_image_bytes()
    files = {"file": ("room.jpg", img_buf, "image/jpeg")}
    sim_resp = client.post("/daylight/simulate", files=files, data={"condition_name": "Warm Morning Light"})
    assert sim_resp.status_code == 200
    assert sim_resp.json()["simulated_image"].startswith("data:image/jpeg;base64,")

    # 3. Materials
    mats_resp = client.get("/materials/all")
    assert mats_resp.status_code == 200
    assert len(mats_resp.json()["materials"]) == 9


def test_estimator_endpoint():
    est_req = {
        "room_length_meters": 6.0,
        "room_width_meters": 4.5,
        "wall_height_meters": 3.0,
        "num_doors": 1,
        "num_windows": 2,
        "coats": 2,
        "cost_per_liter_inr": 480.0
    }
    resp = client.post("/estimator/calculate", json=est_req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["paint_liters_required"] > 0
    assert "recommended_cans_breakdown" in data
    assert data["estimated_cost_inr"] > 0


def test_timeline_and_memory_endpoints():
    # 1. Timeline
    tl_resp = client.get("/timeline?project_id=test_proj")
    assert tl_resp.status_code == 200

    # 2. Chroma DNA
    dna_resp = client.get("/dna")
    assert dna_resp.status_code == 200
    assert "temperature_bias" in dna_resp.json()
    assert "signature_swatches" in dna_resp.json()


def test_billing_and_plans():
    plans_resp = client.get("/plans")
    assert plans_resp.status_code == 200
    assert "free" in plans_resp.json()
    assert "plus" in plans_resp.json()
    assert "pro" in plans_resp.json()

    # Test sandbox order
    order_resp = client.post("/billing/order", json={"plan_id": "plus", "billing_cycle": "monthly"})
    assert order_resp.status_code == 200
    assert "checkout" in order_resp.json()


def test_live_segment_endpoint():
    """Verify real-time live camera frame downscaled segmentation endpoint."""
    import base64
    img_buf = create_test_image_bytes()
    b64 = "data:image/jpeg;base64," + base64.b64encode(img_buf.getvalue()).decode("utf-8")
    
    resp = client.post("/rooms/live-segment", json={
        "image_base64": b64,
        "target_hex": "#B85C38",
        "intensity": 0.85
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "recoloured_frame" in data
    assert "mask_png" in data
    assert "wall_coverage" in data

