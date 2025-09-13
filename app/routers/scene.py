from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models import SceneResponse
from app.services.cif import ensure_cif_extension, ensure_size_limit, parse_cif_bytes
from app.services.scene import structure_to_scene_dict


router = APIRouter(prefix="/api", tags=["scene"])


@router.post("/scene", response_model=SceneResponse)
async def create_scene(file: UploadFile = File(...)) -> SceneResponse:
    """Accept a .cif file (<=10MB), parse it, and return a Scene JSON.

    Errors:
    - 400: not a .cif
    - 413: file too large
    - 422: parse failure
    """
    ensure_cif_extension(file.filename)

    data = await file.read()
    ensure_size_limit(len(data))

    structure = parse_cif_bytes(data)

    scene_dict = structure_to_scene_dict(structure)

    lattice = structure.lattice
    lattice_dict: Dict[str, float] = {
        "a": float(lattice.a),
        "b": float(lattice.b),
        "c": float(lattice.c),
        "alpha": float(lattice.alpha),
        "beta": float(lattice.beta),
        "gamma": float(lattice.gamma),
        "volume": float(lattice.volume),
    }

    try:
        formula = structure.composition.reduced_formula
    except Exception:
        formula = str(getattr(structure, "formula", ""))

    return SceneResponse(
        scene=scene_dict,
        formula=formula,
        lattice=lattice_dict,
        n_sites=int(structure.num_sites),
        source="upload",
    )

