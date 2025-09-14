#!/usr/bin/env python3
"""Convert a CIF file to pymatgen Structure JSON and CrystalToolkitScene JSON.

Reuses lattice_api services to ensure parity with the API output.

Usage examples:
  python tools/cif_to_scene.py input.cif
  python tools/cif_to_scene.py input.cif --pretty
  python tools/cif_to_scene.py input.cif --scene-out scene.json --structure-out structure.json
  python tools/cif_to_scene.py input.cif --no-axes
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def _strip_axes(scene: dict) -> dict:
    """Remove axes group from scene in-place and return scene.

    Looks for a top-level child with name == 'axes'.
    """
    contents = scene.get("contents")
    if isinstance(contents, list):
        scene["contents"] = [c for c in contents if not (isinstance(c, dict) and c.get("name") == "axes")]
    return scene


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CIF -> Structure JSON and CrystalToolkitScene JSON")
    parser.add_argument("cif", help="Path to .cif file")
    parser.add_argument("--scene-out", default=None, help="Output path for scene JSON (default: <stem>.scene.json)")
    parser.add_argument(
        "--structure-out", default=None, help="Output path for Structure JSON (default: <stem>.structure.json)"
    )
    parser.add_argument(
        "--radius-strategy",
        default="uniform",
        choices=[
            "uniform",
            "atomic",
            "specified_or_average_ionic",
            "covalent",
            "van_der_waals",
            "atomic_calculated",
        ],
        help="Radius scheme passed to CTK Legend (default: uniform; color scheme uses CT default)",
    )
    parser.add_argument("--no-axes", action="store_true", help="Do not include axes (arrows) in scene output")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON outputs (indent=2)")

    args = parser.parse_args(argv)

    cif_path = args.cif
    if not os.path.isfile(cif_path):
        print(f"Error: file not found: {cif_path}", file=sys.stderr)
        return 2

    # Derive defaults for outputs
    stem, _ = os.path.splitext(cif_path)
    scene_out = args.scene_out or f"{stem}.scene.json"
    structure_out = args.structure_out or f"{stem}.structure.json"

    # Lazy imports from project services to avoid CLI import cost if not needed
    try:
        from lattice_api.services.cif import parse_cif_bytes  # type: ignore
        from lattice_api.services.scene import structure_to_scene_dict  # type: ignore
    except Exception as exc:
        print(f"Error: failed to import project modules: {exc}", file=sys.stderr)
        return 1

    try:
        data = open(cif_path, "rb").read()
        structure = parse_cif_bytes(data)
    except Exception as exc:
        print(f"Error: failed to parse CIF: {exc}", file=sys.stderr)
        return 1

    # Write Structure JSON (MSON-compatible)
    try:
        struct_json: dict[str, Any] = structure.as_dict()  # monty-serializable
        with open(structure_out, "w", encoding="utf-8") as f:
            json.dump(struct_json, f, indent=2 if args.pretty else None)
    except Exception as exc:
        print(f"Warning: failed to write structure JSON: {exc}", file=sys.stderr)

    # Build Scene JSON (with bonds and axes, using configured color scheme)
    try:
        scene = structure_to_scene_dict(structure, radius_strategy=args.radius_strategy)
        if args.no_axes:
            scene = _strip_axes(scene)
        with open(scene_out, "w", encoding="utf-8") as f:
            json.dump(scene, f, indent=2 if args.pretty else None)
    except Exception as exc:
        print(f"Error: failed to build/write scene JSON: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote:\n- {structure_out}\n- {scene_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
