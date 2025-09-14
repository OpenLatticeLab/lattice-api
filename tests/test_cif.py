import json
from pathlib import Path

import pytest

from lattice_api.services.cif import (
    ensure_cif_extension,
    ensure_size_limit,
    parse_cif_bytes,
)
from fastapi import HTTPException


FIXTURES = Path(__file__).parent / "data"


def test_ensure_cif_extension_valid():
    ensure_cif_extension("foo.CIF")
    ensure_cif_extension("bar.cif")


def test_ensure_cif_extension_invalid():
    with pytest.raises(HTTPException):
        ensure_cif_extension("foo.txt")
    with pytest.raises(HTTPException):
        ensure_cif_extension(None)


def test_ensure_size_limit():
    ensure_size_limit(10)
    with pytest.raises(HTTPException):
        ensure_size_limit(10 * 1024 * 1024 + 1)


def test_parse_cif_bytes_success():
    data = (FIXTURES / "si.cif").read_bytes()
    structure = parse_cif_bytes(data)
    assert structure.composition.reduced_formula == "Si"


def test_parse_cif_bytes_failure():
    with pytest.raises(HTTPException):
        parse_cif_bytes(b"not a cif")

