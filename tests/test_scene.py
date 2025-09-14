import json
from pathlib import Path

from lattice_api.services.cif import parse_cif_bytes
from lattice_api.services.scene import structure_to_scene_dict


FIXTURES = Path(__file__).parent / "data"


def test_structure_to_scene_is_json_serializable_and_has_groups():
    data = (FIXTURES / "si.cif").read_bytes()
    structure = parse_cif_bytes(data)

    scene = structure_to_scene_dict(structure)
    # Should be pure-Python JSON-serializable
    json.dumps(scene)

    assert isinstance(scene, dict)
    assert scene.get("name") in {"Structure", "StructureGraph"}
    contents = scene.get("contents") or []
    names = {c.get("name") for c in contents if isinstance(c, dict)}
    # Expect typical groups present
    assert "atoms" in names
    assert "unit_cell" in names
    assert "axes" in names
    # Bonds are produced via StructureGraph path
    assert "bonds" in names

