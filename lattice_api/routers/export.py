from __future__ import annotations

import io
import json
import zipfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from lattice_api.models import (
    ExportRequest,
    MPROptions,
    CellLiteral,
)
from lattice_api.services.cif import parse_cif_bytes


router = APIRouter(prefix="/api", tags=["export"])


"""
Export API endpoint using models from lattice_api.models
"""


def _error(status: int, error: str, message: str, detail: dict | None = None):
    raise HTTPException(status_code=status, detail={"error": error, "message": message, "detail": detail or {}})


def _load_structure_from_request(req: ExportRequest):
    from pymatgen.core.structure import Structure

    if req.structure:
        try:
            return Structure.from_dict(req.structure)
        except Exception as exc:
            _error(422, "UnprocessableEntity", "Failed to parse structure JSON", {"exc": str(exc)})

    if req.cif:
        try:
            return parse_cif_bytes(req.cif.encode("utf-8"))
        except Exception as exc:
            _error(422, "UnprocessableEntity", "Failed to parse CIF text", {"exc": str(exc)})

    if req.material_id:
        _error(404, "NotFound", "material_id not supported in this instance", {"material_id": req.material_id})

    _error(400, "BadRequest", "One of 'structure', 'cif', or 'material_id' is required")


def _apply_cell_option(structure, cell: CellLiteral):
    if cell == "input":
        return structure
    try:
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

        sga = SpacegroupAnalyzer(structure, symprec=1e-3)
        if cell == "primitive":
            return sga.get_primitive_standard_structure()
        if cell == "conventional":
            return sga.get_conventional_standard_structure()
    except Exception:
        return structure
    return structure


def _export_cif(structure, symm: bool) -> bytes:
    from pymatgen.io.cif import CifWriter

    cif_str = str(CifWriter(structure, symprec=(1e-2 if symm else None)))
    return cif_str.encode("utf-8")


def _export_poscar(structure) -> bytes:
    from pymatgen.io.vasp.inputs import Poscar

    return str(Poscar(structure)).encode("utf-8")


def _export_json(structure) -> bytes:
    return json.dumps(structure.as_dict()).encode("utf-8")


def _export_prismatic_zip(structure) -> bytes:
    # Minimal placeholder: include a CIF and a README for prismatic usage
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", "Prismatic input bundle (placeholder). Includes structure.cif.\n")
        zf.writestr("structure.cif", _export_cif(structure, symm=False))
        zf.writestr("structure.json", _export_json(structure))
    return mem.getvalue()


def _export_mpr_zip(structure, mpr: MPROptions | None) -> bytes:
    from pymatgen.io.vasp.sets import MPRelaxSet

    kwargs = {}
    # Note: mapping options is non-trivial; accept and ignore unknowns gracefully for now.
    vset = MPRelaxSet(structure, **kwargs)
    vasp_input = vset.get_input_set(potcar_spec=True)

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("INCAR", str(vasp_input["INCAR"]))
        zf.writestr("KPOINTS", str(vasp_input["KPOINTS"]))
        zf.writestr("POSCAR", str(vasp_input["POSCAR"]))
        # POTCAR.spec is a string if potcar_spec=True
        potcar_obj = vasp_input["POTCAR"]
        zf.writestr("POTCAR.spec", potcar_obj if isinstance(potcar_obj, str) else str(potcar_obj))
        # Also include a CIF for convenience
        zf.writestr("structure.cif", _export_cif(structure, symm=False))
    return mem.getvalue()


@router.post("/export")
def export_file(req: ExportRequest):
    # 1) Resolve structure
    structure = _load_structure_from_request(req)
    if not structure:
        _error(422, "UnprocessableEntity", "Could not resolve a structure from input")

    # 2) Apply cell choice
    structure = _apply_cell_option(structure, req.options.cell)

    # 3) Build payload by format
    fmt = req.format
    filename = "download"
    content_type = "application/octet-stream"
    payload = b""

    try:
        if fmt == "cif" or fmt == "cif_symm":
            symm = True if fmt == "cif_symm" else bool(req.options.symmetrize)
            payload = _export_cif(structure, symm)
            content_type = "chemical/x-cif"
            filename = f"{structure.composition.reduced_formula}.cif"
        elif fmt == "poscar":
            payload = _export_poscar(structure)
            content_type = "text/plain"
            filename = "POSCAR"
        elif fmt == "json":
            payload = _export_json(structure)
            content_type = "application/json"
            filename = "structure.json"
        elif fmt == "prismatic":
            payload = _export_prismatic_zip(structure)
            content_type = "application/zip"
            filename = "prismatic_inputs.zip"
        elif fmt == "mpr":
            payload = _export_mpr_zip(structure, req.options.mpr)
            content_type = "application/zip"
            filename = "vasp_inputs_mprelaxset.zip"
        else:
            _error(400, "BadRequest", f"Unsupported format: {fmt}")
    except HTTPException:
        raise
    except Exception as exc:
        _error(500, "InternalServerError", "Failed to generate export", {"exc": str(exc)})

    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return Response(content=payload, media_type=content_type, headers=headers)
