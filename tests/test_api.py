from pathlib import Path

from fastapi.testclient import TestClient

from lattice_api.main import app


client = TestClient(app)
FIXTURES = Path(__file__).parent / "data"


def test_api_scene_ok():
    file_bytes = (FIXTURES / "si.cif").read_bytes()
    resp = client.post("/api/scene", files={"file": ("si.cif", file_bytes, "chemical/x-cif")})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert set(["scene", "formula", "lattice", "n_sites", "source"]).issubset(data.keys())
    assert data["source"] == "upload"


def test_api_export_cif_and_poscar():
    # Prepare a structure JSON via /api/scene path (parse once)
    (FIXTURES / "si.cif").read_bytes()
    # Export CIF
    payload = {"format": "cif", "cif": (FIXTURES / "si.cif").read_text()}
    resp = client.post("/api/export", json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("content-type") == "chemical/x-cif"
    assert resp.headers.get("content-disposition", "").startswith("attachment;")
    assert len(resp.content) > 0

    # Export POSCAR from same CIF
    payload = {"format": "poscar", "cif": (FIXTURES / "si.cif").read_text()}
    resp = client.post("/api/export", json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("content-type") == "text/plain; charset=utf-8"
    assert len(resp.content) > 0
