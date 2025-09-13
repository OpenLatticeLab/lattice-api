from __future__ import annotations

from fastapi import HTTPException, status


def _element_color(symbol: str) -> str:
    """Rudimentary element color palette for spheres."""
    el = "".join(ch for ch in symbol if ch.isalpha())
    palette = {
        "H": "#ffffff",
        "He": "#d9ffff",
        "Li": "#cc80ff",
        "Be": "#c2ff00",
        "B": "#ffb5b5",
        "C": "#909090",
        "N": "#3050f8",
        "O": "#ff0d0d",
        "F": "#90e050",
        "Ne": "#b3e3f5",
        "Na": "#ab5cf2",
        "Mg": "#8aff00",
        "Al": "#bfa6a6",
        "Si": "#f0c8a0",
        "P": "#ff8000",
        "S": "#ffff30",
        "Cl": "#1ff01f",
        "Ar": "#80d1e3",
        "K": "#8f40d4",
        "Ca": "#3dff00",
        "Fe": "#e06633",
        "Cu": "#c88033",
        "Zn": "#7d80b0",
    }
    return palette.get(el, "#cccccc")


def structure_to_crystaltoolkit_scene(structure) -> dict:
    """Build a CrystalToolkitScene-like JSON using cartesian coordinates.

    Output format:
    {
      name: str,
      visible: bool,
      contents: [ {type:'spheres', color:'#hex', radius:float, positions:[[x,y,z], ...]}, ... , {type:'lines', positions:[...] } ]
    }
    """
    lattice = structure.lattice  # type: ignore[attr-defined]

    # Basis vectors in cartesian coords (A, B, C)
    a_vec = list(map(float, lattice.matrix[0]))
    b_vec = list(map(float, lattice.matrix[1]))
    c_vec = list(map(float, lattice.matrix[2]))

    # Group atom positions by element with cartesian coordinates
    groups: dict[str, list[list[float]]] = {}
    for site in structure.sites:
        element = str(site.specie)
        cart = lattice.get_cartesian_coords(site.frac_coords)  # type: ignore[attr-defined]
        groups.setdefault(element, []).append([float(cart[0]), float(cart[1]), float(cart[2])])

    # Sphere radius heuristic
    radius = float(min(lattice.a, lattice.b, lattice.c) * 0.08)

    contents: list[dict] = []

    # Optional: add unit cell wireframe as lines (12 edges, 24 vertices)
    o = [0.0, 0.0, 0.0]
    a = a_vec
    b = b_vec
    c = c_vec
    ab = [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
    ac = [a[0] + c[0], a[1] + c[1], a[2] + c[2]]
    bc = [b[0] + c[0], b[1] + c[1], b[2] + c[2]]
    abc = [a[0] + b[0] + c[0], a[1] + b[1] + c[1], a[2] + b[2] + c[2]]

    cell_edges = [
        (o, a), (o, b), (o, c),
        (a, ab), (a, ac),
        (b, ab), (b, bc),
        (c, ac), (c, bc),
        (ab, abc), (ac, abc), (bc, abc),
    ]
    lines_positions: list[list[float]] = []
    for p, q in cell_edges:
        lines_positions.append([float(p[0]), float(p[1]), float(p[2])])
        lines_positions.append([float(q[0]), float(q[1]), float(q[2])])

    contents.append({
        "type": "lines",
        "positions": lines_positions,
    })

    # Add spheres per element group for coloring
    for element, positions in groups.items():
        contents.append({
            "type": "spheres",
            "color": _element_color(element),
            "radius": radius,
            "positions": positions,
        })

    return {"name": "structure", "visible": True, "contents": contents}


def structure_to_scene_dict(structure) -> dict:
    """Convert a pymatgen Structure to a Crystal Toolkit compatible scene dict.

    If Crystal Toolkit is available, try its converters. Otherwise, build a
    minimal CrystalToolkitScene-like dict in cartesian coordinates suitable
    for direct rendering by the front-end.
    """
    # Attempt 1: classic helper
    try:  # pragma: no cover - environment dependent
        from crystal_toolkit.helpers.pythreejs import structure_to_scene  # type: ignore

        scene = structure_to_scene(structure)
        if hasattr(scene, "as_dict"):
            return scene.as_dict()  # monty-serializable Scene
        if isinstance(scene, dict):
            return scene
    except Exception:
        pass

    # Attempt 2: component-based API
    try:  # pragma: no cover - environment dependent
        from crystal_toolkit.renderables.structure import StructureMoleculeComponent  # type: ignore

        comp = StructureMoleculeComponent(structure)
        scene = comp.get_scene()
        if hasattr(scene, "as_dict"):
            return scene.as_dict()
        if isinstance(scene, dict):
            return scene
    except Exception:
        pass

    # If Crystal Toolkit is unavailable or API mismatched, produce a cartesian
    # CrystalToolkitScene-like fallback so the API remains useful without adapters.
    try:
        return structure_to_crystaltoolkit_scene(structure)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not generate scene: {exc}",
        ) from exc
