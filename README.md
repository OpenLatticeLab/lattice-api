## lattice-api

FastAPI service that converts CIF files to Crystal Toolkit Scene JSON. Includes a stub for prompt-driven structure generation and future workflow orchestration.

### Run

- Install (use a virtualenv):
  - `pip install -e .` or `pip install .`
- Start dev server:
  - `uvicorn lattice_api.main:app --reload`
  - or `python -m lattice_api._cli` / `serve` script (when installed)

Environment variables:
- `CORS_ALLOW_ORIGINS`: comma-separated origins. If unset, none are allowed via explicit list.
- `CORS_ALLOW_ORIGIN_REGEX`: optional regex to match origins (e.g. `^https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$` or `^https?://203\\.0\\.113\\.10(:\\d+)?$`).

Examples:
- Allow localhost any port (dev): `CORS_ALLOW_ORIGIN_REGEX=^https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$`
- Allow a public IP any port (dev): `CORS_ALLOW_ORIGIN_REGEX=^https?://203\\.0\\.113\\.10(:\\d+)?$`
- Production fixed domains only: `CORS_ALLOW_ORIGINS=https://app.example.com,https://admin.example.com`

### Dependencies
- FastAPI, uvicorn[standard], pydantic
- pymatgen (CIF parsing)
- crystal-toolkit (Scene generation)
- python-multipart (file upload)

These are declared in `pyproject.toml`.

### API

- POST `/api/scene`
  - Form file: `file` (.cif, <=10MB)
  - Behavior:
    - Validates `.cif` extension; returns 413 if >10MB
    - Parses CIF to `Structure` using pymatgen
    - Generates Scene JSON using Crystal Toolkit (includes bonds/cylinders + unit_cell + axes by default); returns 500 if Crystal Toolkit is unavailable
  - Response example:
    ```json
    {
      "scene": {
        "name": "StructureGraph",
        "contents": [
          { "name": "atoms", "contents": [ { "type": "spheres", "positions": [[x,y,z]], "radius": 0.5, "color": "#..." } ], "origin": [ ... ], "visible": true },
          { "name": "bonds", "contents": [ { "type": "cylinders", "positionPairs": [[[x1,y1,z1],[x2,y2,z2]]], "radius": 0.1, "color": "#..." } ], "origin": [ ... ], "visible": true },
          { "name": "unit_cell", "contents": [ { "type": "lines", "positions": [[...],[...], "..."], "clickable": false } ], "origin": [ ... ], "visible": true },
          { "name": "axes", "contents": [ { "type": "arrows", "positionPairs": [[[0,0,0],[1,0,0]]], "color": "red" } ], "origin": [ ... ], "visible": true }
        ],
        "origin": [x0, y0, z0],
        "visible": true
      },
      "formula": "SiO2",
      "lattice": { "a": 4.91, "b": 4.91, "c": 5.43, "alpha": 90, "beta": 90, "gamma": 120, "volume": 131.3 },
      "n_sites": 9,
      "source": "upload"
    }
    ```
  - Error codes:
    - 400 not a .cif
    - 413 file too large
    - 422 parse failed
    - 500 crystal toolkit unavailable/incompatible

- POST `/api/prompt-structure`
  - JSON: `{ "prompt": "..." }`
  - Currently returns `501 Not Implemented`, but includes `"source": "prompt"` in the JSON
  - Future: prompt -> structure generation

- GET `/health`
  - Returns `{ "status": "ok" }`

- POST `/api/export`
  - JSON body:
    - `format`: one of `cif_symm|cif|poscar|json|prismatic|mpr`
    - one of `structure` (pymatgen JSON) | `cif` (raw text) | `material_id` (not wired in this repo)
    - `options`: `{ cell: 'input'|'primitive'|'conventional', symmetrize?: boolean, mpr?: { functional?, potcar?, kpoint_density? } }`
  - Response: file stream with appropriate `Content-Type` and `Content-Disposition` for download
  - Examples:
    - `curl -X POST localhost:8000/api/export -H 'Content-Type: application/json' --data '{"format":"cif_symm","structure":{...},"options":{"cell":"conventional","symmetrize":true}}' --output Si_symm.cif`
    - `curl -X POST localhost:8000/api/export -H 'Content-Type: application/json' --data '{"format":"poscar","cif":"<CIF TEXT>","options":{"cell":"primitive"}}' --output POSCAR`
    - `curl -X POST localhost:8000/api/export -H 'Content-Type: application/json' --data '{"format":"mpr","structure":{...}}' --output vasp_inputs_mprelaxset.zip`

OpenAPI: visit `/docs` to see the `SceneResponse` model including the `source` field.

### Tools
- Convert CIF -> Structure JSON + CrystalToolkitScene JSON:
  - `python tools/cif_to_scene.py <input.cif> [--pretty] [--scene-out <path>] [--structure-out <path>] [--radius-strategy <scheme>] [--no-axes]`
  - Examples:
    - `python tools/cif_to_scene.py sample.cif --pretty`
    - `python tools/cif_to_scene.py sample.cif --scene-out scene.json --structure-out structure.json`
    - `python tools/cif_to_scene.py sample.cif --radius-strategy uniform --no-axes`
  - Notes:
    - Uses the same parsing and scene-building code as `/api/scene` (includes bonds and axes by default).
    - Element color scheme follows Crystal Toolkit default; configure via `CT_LEGEND_COLOR_SCHEME` (e.g., `VESTA`, `Jmol`).
    - Radius strategy defaults to `uniform`; other options: `atomic`, `covalent`, `van_der_waals`, `atomic_calculated`, `specified_or_average_ionic`.

### Testing
- Install dev dependencies:
  - `pip install -e '.[dev]'`
- Run tests:
  - `pytest -q`
- Notes:
  - Tests exercise CIF parsing, scene JSON generation, and `/api/scene` + `/api/export` endpoints.
  - The suite uses a small Si CIF fixture at `tests/data/si.cif` and relies on project runtime deps (pymatgen, crystal-toolkit).

### Structure
```
lattice_api/
  main.py
  routers/
    scene.py          # /api/scene
    prompt.py         # /api/prompt-structure
    health.py         # /health
  services/
    cif.py            # CIF validation and parsing
    scene.py          # Structure -> Scene JSON (Crystal Toolkit)
    prompt_gen.py     # Placeholder: prompt-driven structure generation
    workflows.py      # Placeholder: Agents/MCP/VASP orchestration (band/DOS)
pyproject.toml
```

### Roadmap
- Prompt → structure generation: `lattice_api/services/prompt_gen.py`
  - Convert natural-language prompts into candidate crystal structures (planned).
- VASP band/DOS calculations: `lattice_api/services/workflows.py`
  - Run first-principles workflows (band structure, DOS) for evaluation (planned).
- Validation & orchestration (Agents/MCP): `lattice_api/services/workflows.py`
  - Multi-agent coordination, validation, and pipeline orchestration (planned).
