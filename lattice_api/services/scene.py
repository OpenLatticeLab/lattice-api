from __future__ import annotations

from fastapi import HTTPException, status


def structure_to_scene_dict(structure, *, radius_strategy: str = "uniform") -> dict:
    """Convert a pymatgen Structure to CrystalToolkitScene JSON with bonds (cylinders).

    Implementation mirrors MP: build a StructureGraph using a near-neighbor
    strategy, then render via CTK's StructureGraph renderer which includes
    bonds as cylinder primitives.
    """
    try:  # pragma: no cover - environment dependent
        # Build bonding graph
        from pymatgen.analysis.graphs import StructureGraph  # type: ignore
        from pymatgen.analysis.local_env import MinimumDistanceNN  # type: ignore
        from crystal_toolkit.core.legend import Legend  # type: ignore

        # Ensure CTK monkey-patches StructureGraph.get_scene
        from crystal_toolkit.renderables import structuregraph as _ct_structuregraph  # type: ignore  # noqa: F401

        graph = StructureGraph.with_local_env_strategy(structure, MinimumDistanceNN())

        # Render with MP-like defaults: include image atoms, bonds outside cell, hide incomplete
        # Use CTK default color scheme (configurable via CT_LEGEND_COLOR_SCHEME)
        legend = Legend(structure, radius_scheme=radius_strategy)
        scene_obj = graph.get_scene(
            draw_image_atoms=True,
            bonded_sites_outside_unit_cell=True,
            hide_incomplete_edges=True,
            legend=legend,
        )
        # Serialize to dict first to avoid numpy types leaking into Pydantic
        scene_json = scene_obj.to_json()

        # Append axes (arrows) using pure Python lists to avoid numpy arrays
        try:
            lat = getattr(structure, "lattice", None)
            if lat is not None:
                # Axes configuration via env
                import os as _os
                mode = _os.getenv("CT_AXES_MODE", "lattice").lower()  # 'lattice' or 'cartesian'
                scale = float(_os.getenv("CT_AXES_SCALE", "1.6"))
                head_len = float(_os.getenv("CT_AXES_HEAD_LENGTH", "0.32"))
                head_wid = float(_os.getenv("CT_AXES_HEAD_WIDTH", "0.18"))
                radius = float(_os.getenv("CT_AXES_RADIUS", "0.07"))

                if mode == "cartesian":
                    au, bu, cu = [scale, 0.0, 0.0], [0.0, scale, 0.0], [0.0, 0.0, scale]
                else:
                    m = lat.matrix  # 3x3
                    # Normalize basis vectors

                    def _norm(v):
                        return (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5 or 1.0

                    a = [float(m[0][0]), float(m[0][1]), float(m[0][2])]
                    b = [float(m[1][0]), float(m[1][1]), float(m[1][2])]
                    c = [float(m[2][0]), float(m[2][1]), float(m[2][2])]
                    an = _norm(a); bn = _norm(b); cn = _norm(c)
                    au = [a[0] / an * scale, a[1] / an * scale, a[2] / an * scale]
                    bu = [b[0] / bn * scale, b[1] / bn * scale, b[2] / bn * scale]
                    cu = [c[0] / cn * scale, c[1] / cn * scale, c[2] / cn * scale]

                axes_group = {
                    "name": "axes",
                    "contents": [
                        {
                            "type": "arrows",
                            "positionPairs": [[[0.0, 0.0, 0.0], au]],
                            "color": "red",
                            "radius": radius,
                            "headLength": head_len,
                            "headWidth": head_wid,
                            "clickable": False,
                        },
                        {
                            "type": "arrows",
                            "positionPairs": [[[0.0, 0.0, 0.0], bu]],
                            "color": "green",
                            "radius": radius,
                            "headLength": head_len,
                            "headWidth": head_wid,
                            "clickable": False,
                        },
                        {
                            "type": "arrows",
                            "positionPairs": [[[0.0, 0.0, 0.0], cu]],
                            "color": "blue",
                            "radius": radius,
                            "headLength": head_len,
                            "headWidth": head_wid,
                            "clickable": False,
                        },
                    ],
                    "origin": scene_json.get("origin", [0.0, 0.0, 0.0]),
                    "visible": True,
                }
                scene_json.setdefault("contents", []).append(axes_group)
        except Exception:
            # Axes are optional; ignore failures
            pass

        return scene_json
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Failed to generate CrystalToolkitScene with bonds. "
                "Ensure 'crystal-toolkit' and 'pymatgen' are installed and compatible."
            ),
        )
