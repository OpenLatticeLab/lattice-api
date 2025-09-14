from __future__ import annotations

import logging
from io import StringIO

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def ensure_cif_extension(filename: str | None) -> None:
    """Validate that file has a .cif extension.

    Raises HTTP 400 if not.
    """
    if not filename or "." not in filename:
        logger.warning("Upload rejected: missing filename or extension")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .cif files are accepted.",
        )
    if not filename.lower().endswith(".cif"):
        logger.warning("Upload rejected: not a .cif file (%s)", filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .cif files are accepted.",
        )
    logger.debug("Validated .cif extension: %s", filename)


def ensure_size_limit(num_bytes: int) -> None:
    """Enforce 10 MB size limit.

    Raises HTTP 413 if exceeded.
    """
    if num_bytes > MAX_UPLOAD_SIZE:
        logger.warning("Upload too large: %d bytes (limit=%d)", num_bytes, MAX_UPLOAD_SIZE)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Max 10MB.",
        )
    logger.debug("Upload size OK: %d bytes", num_bytes)


def parse_cif_bytes(data: bytes):
    """Parse CIF bytes into a pymatgen Structure.

    Raises HTTP 422 on parse failure.
    """
    try:
        from pymatgen.io.cif import CifParser  # type: ignore
    except Exception as exc:  # pragma: no cover
        logger.exception("pymatgen not available: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"pymatgen not available: {exc}",
        ) from exc

    # Try UTF-8 first, then latin-1 as a permissive fallback
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1", errors="ignore")

    try:
        parser = CifParser(StringIO(text))
        structures = parser.get_structures()
        if not structures:
            raise ValueError("CIF produced no structures")
        structure = structures[0]
        try:
            n_sites = getattr(structure, "num_sites", None)
        except Exception:
            n_sites = None
        logger.info("Parsed CIF successfully (sites=%s)", n_sites)
        return structure
    except Exception as exc:
        logger.exception("Failed to parse CIF: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse CIF: {exc}",
        ) from exc
