"""Unit tests for modules.room_3d Three.js WebGL spatial simulation engine."""
from modules.room_3d import generate_3d_room_html
from models.schemas import PaletteConcept, ColorSwatch
from ui.components import render_3d_room_preview_card


def test_generate_3d_room_html_structure():
    """Verify that the generated HTML payload contains essential Three.js and OrbitControls assets."""
    html = generate_3d_room_html(
        primary_wall_hex="#B85C38",
        secondary_wall_hex="#D6C5B3",
        accent_hex="#30271F",
        trim_hex="#F7F3EE",
        room_type="Master Suite",
        theme="light",
        canvas_height=550
    )

    assert "<!DOCTYPE html>" in html
    assert "three.min.js" in html
    assert "OrbitControls.js" in html
    assert "canvas-container" in html
    assert "#B85C38" in html
    assert "#D6C5B3" in html
    assert "#30271F" in html
    assert "#F7F3EE" in html
    assert "Master Suite" in html
    assert "setFinish" in html
    assert "setLighting" in html
    assert "height: 550px;" in html


def test_3d_room_theme_adaptation():
    """Verify background canvas switches cleanly between ivory and obsidian."""
    html_light = generate_3d_room_html(theme="light")
    html_dark = generate_3d_room_html(theme="dark")

    # Light mode ivory background
    assert "#F5F0E8" in html_light
    # Dark mode obsidian background
    assert "#171916" in html_dark


def test_render_3d_room_preview_card_execution(monkeypatch):
    """Verify render_3d_room_preview_card calls components.html without exceptions."""
    called_args = []

    def fake_html(code, height, scrolling):
        called_args.append((code, height, scrolling))

    import streamlit.components.v1 as components
    monkeypatch.setattr(components, "html", fake_html)

    palette = PaletteConcept(
        id="test_3d_pal",
        name="Terracotta Gallery",
        concept_category="Warm and Inviting",
        harmony_type="Monochromatic",
        description="Architectural terracotta tone study",
        atmosphere="Warm and refined",
        design_rationale="Monochromatic warmth providing grounding tranquility.",
        furniture_flooring_compatibility="Natural oak and warm travertine harmony.",
        primary_wall=ColorSwatch(hex="#B85C38", rgb=(184, 92, 56), name="Terracotta", role="Primary Wall"),
        secondary_wall=ColorSwatch(hex="#D6C5B3", rgb=(214, 197, 179), name="Linen", role="Secondary Wall"),
        accent=ColorSwatch(hex="#30271F", rgb=(48, 39, 31), name="Bronze", role="Accent"),
        trim=ColorSwatch(hex="#F7F3EE", rgb=(247, 243, 238), name="Alabaster", role="Trim"),
        heuristic_score=95.0
    )

    render_3d_room_preview_card(palette=palette, room_type="Dining Gallery", theme="light", height=500)

    assert len(called_args) == 1
    code, height, scrolling = called_args[0]
    assert "#B85C38" in code
    assert height == 500
    assert scrolling is False


def test_3d_fastapi_endpoints():
    """Verify FastAPI 3D endpoints: Mode A (depth mesh), Mode B (room box), Mode C (SfM job), and GLB export."""
    from fastapi.testclient import TestClient
    from backend.main import app
    import numpy as np, cv2, io

    client = TestClient(app)
    img = np.full((100, 120, 3), 210, dtype=np.uint8)
    _, buf = cv2.imencode(".png", img)
    file_bytes = io.BytesIO(buf.tobytes())

    # Mode A: Depth Mesh
    res_a = client.post(
        "/3d/depth-mesh",
        files={"file": ("room.png", file_bytes, "image/png")},
        data={"resolution": "20", "target_hex": "#2563EB"}
    )
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["status"] == "success"
    assert "mesh" in data_a
    assert data_a["mesh"]["vertex_count"] > 0
    assert len(data_a["mesh"]["indices"]) > 0

    # Mode B: Room Box
    file_bytes.seek(0)
    res_b = client.post(
        "/3d/room-box",
        files={"file": ("room.png", file_bytes, "image/png")},
        data={"room_width_m": "4.0", "room_depth_m": "5.0", "room_height_m": "2.8"}
    )
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["status"] == "success"
    assert "box" in data_b

    # Mode C: Multi-Photo Reconstruct Job
    res_c = client.post("/3d/reconstruct-multi", json={"photos_count": 8, "project_name": "Living Room Scan"})
    assert res_c.status_code == 200
    data_c = res_c.json()
    assert data_c["status"] == "success"
    job_id = data_c["job_id"]

    res_job = client.get(f"/3d/job/{job_id}")
    assert res_job.status_code == 200
    assert res_job.json()["status"] == "success"
    assert res_job.json()["job"]["status"] in ["processing", "completed"]
    assert "current_stage" in res_job.json()["job"]
    assert res_job.json()["job"]["progress_pct"] >= 0

    # Export Binary GLB
    res_glb = client.get("/3d/export/glb")
    assert res_glb.status_code == 200
    assert res_glb.headers.get("content-type") == "model/gltf-binary"
    assert len(res_glb.content) > 1000
    # Check glTF 2.0 magic bytes: b"glTF"
    assert res_glb.content[:4] == b"glTF"

