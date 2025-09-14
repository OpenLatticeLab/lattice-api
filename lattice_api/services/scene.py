from __future__ import annotations

import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def structure_to_scene_dict(structure) -> dict:
    """Convert a pymatgen Structure to CrystalToolkitScene JSON.

    Preferred: call CTK's `get_structure_scene(structure).to_json()`.
    Fallback: build a minimal CrystalToolkitScene-like JSON in cartesian coords.
    """
    try:  # pragma: no cover - environment dependent
        from crystal_toolkit.renderables.structure import (  # type: ignore
            get_structure_scene,
        )
        logger.debug("Generating CrystalToolkitScene via CTK get_structure_scene().")
        scene_obj = get_structure_scene(structure)
        scene_json = scene_obj.to_json()
        logger.debug("CrystalToolkitScene generated successfully (keys: %s)", list(scene_json.keys()))
        return scene_json
    except Exception as exc:
        logger.exception("Failed to generate CrystalToolkitScene using CTK: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Crystal Toolkit not available or incompatible. "
                "Install 'crystal-toolkit' and ensure compatible versions of pymatgen/ctk."
            ),
        )
