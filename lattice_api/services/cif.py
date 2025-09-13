from __future__ import annotations

from io import StringIO

from fastapi import HTTPException, status


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def ensure_cif_extension(filename: str | None) -> None:
    """Validate that file has a .cif extension.

    Raises HTTP 400 if not.
    """
    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .cif files are accepted.",
        )
    if not filename.lower().endswith(".cif"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .cif files are accepted.",
        )


def ensure_size_limit(num_bytes: int) -> None:
    """Enforce 10 MB size limit.

    Raises HTTP 413 if exceeded.
    """
    if num_bytes > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Max 10MB.",
        )


def parse_cif_bytes(data: bytes):
    """Parse CIF bytes into a pymatgen Structure.

    Raises HTTP 422 on parse failure.
    """
    try:
        from pymatgen.io.cif import CifParser  # type: ignore
    except Exception as exc:  # pragma: no cover
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
        return structures[0]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse CIF: {exc}",
        ) from exc

