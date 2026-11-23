"""Tests for the /materials/score endpoint — valid and invalid inputs."""
import os
import sys
import time
import socket
import subprocess
import requests
import pytest

BASE_URL = os.environ.get("TEST_API_URL", "http://127.0.0.1:8000")


def is_server_running(host="127.0.0.1", port=8000) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def ensure_server_running():
    proc = None
    if not is_server_running():
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            if is_server_running():
                break
            time.sleep(0.2)
    yield
    if proc:
        proc.terminate()


class ApiClient:
    def get(self, path: str, **kwargs):
        return requests.get(f"{BASE_URL}{path}", **kwargs)

    def post(self, path: str, **kwargs):
        return requests.post(f"{BASE_URL}{path}", **kwargs)


client = ApiClient()


def test_materials_score_with_valid_hex():
    """POST /materials/score with a valid primary_hex returns 200 and scores list."""
    resp = client.post("/materials/score", json={"primary_hex": "#B85C38"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert isinstance(data["scores"], list)
    assert len(data["scores"]) > 0
    for s in data["scores"]:
        assert "name" in s
        assert "score" in s
        assert "status" in s
        assert s["status"] in ("Harmonious", "Balanced", "Clashing")
        assert 0 <= s["score"] <= 100


def test_materials_score_with_default_hex():
    """POST /materials/score with empty body still uses the fallback and returns 200."""
    resp = client.post("/materials/score", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert isinstance(data["scores"], list)
    assert len(data["scores"]) > 0


def test_materials_score_with_invalid_hex():
    """POST /materials/score with a malformed hex falls back gracefully (no 500)."""
    resp = client.post("/materials/score", json={"primary_hex": "not-a-colour"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert isinstance(data["scores"], list)


def test_materials_score_with_palette_object():
    """POST /materials/score with a full palette object returns 200."""
    palette = {
        "id": "test-pal",
        "name": "Test Palette",
        "concept_category": "Architectural",
        "harmony_type": "Complementary",
        "description": "A test palette",
        "atmosphere": "Balanced",
        "primary_wall": {
            "hex": "#B85C38",
            "rgb": [184, 92, 56],
            "role": "Primary Wall (60%)",
        },
        "secondary_wall": {
            "hex": "#D6C5B3",
            "rgb": [214, 197, 179],
            "role": "Secondary Wall (30%)",
        },
        "accent": {
            "hex": "#30271F",
            "rgb": [48, 39, 31],
            "role": "Accent (10%)",
        },
        "trim": {
            "hex": "#F7F3EE",
            "rgb": [247, 243, 238],
            "role": "Trim",
        },
        "design_rationale": "Test rationale",
        "furniture_flooring_compatibility": "Universal match",
        "colors": [],
    }
    resp = client.post("/materials/score", json={"palette": palette})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert len(data["scores"]) > 0


def test_materials_score_with_specific_materials():
    """POST /materials/score limiting to specific materials returns only those."""
    resp = client.post(
        "/materials/score",
        json={"primary_hex": "#B85C38", "materials": ["Oak Wood", "Carrara Marble"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    names = [s["name"] for s in data["scores"]]
    assert len(names) <= 2
    for n in names:
        assert n in ["Oak Wood", "Carrara Marble"]


def test_materials_score_missing_body_returns_422():
    """POST /materials/score with wrong content-type returns 422 validation error."""
    resp = client.post(
        "/materials/score",
        data="not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["status"] == "error"
    assert data["code"] == 422


def test_cors_headers_on_materials_score():
    """The /materials/score response includes CORS headers for allowed origins."""
    resp = client.post(
        "/materials/score",
        json={"primary_hex": "#B85C38"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert resp.headers.get("access-control-allow-credentials") == "true"


def test_cors_headers_on_error_responses():
    """Even 422 validation error responses carry CORS headers."""
    resp = client.post(
        "/materials/score",
        data="invalid json",
        headers={"Content-Type": "application/json", "Origin": "http://localhost:3000"},
    )
    assert resp.status_code == 422
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert resp.headers.get("access-control-allow-credentials") == "true"
