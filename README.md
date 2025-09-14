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
- `CORS_ALLOW_ORIGIN_REGEX`: optional regex to match origins (e.g. `^https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$` or `^https?://203\\.0\\.113\\.10(:\\d+)?$`). If set, it takes precedence and the explicit list is ignored.
- `HOST`, `PORT`: used by the CLI entrypoint (default `0.0.0.0:8000`).

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
    - Generates Scene JSON using Crystal Toolkit; returns 500 if Crystal Toolkit is unavailable
  - Response example:
    ```json
    {
      "scene": { "type": "Scene", "...": "..." },
      "formula": "NaCl",
      "lattice": { "a": 5.6, "b": 5.6, "c": 5.6, "alpha": 90, "beta": 90, "gamma": 90, "volume": 179.4 },
      "n_sites": 8,
      "source": "upload"
    }
    ```
  - Error codes:
    - 400 not a .cif
    - 413 file too large
    - 422 parse failed

- POST `/api/prompt-structure`
  - JSON: `{ "prompt": "..." }`
  - Currently returns `501 Not Implemented`, but includes `"source": "prompt"` in the JSON
  - Future: prompt -> structure generation

- GET `/health`
  - Returns `{ "status": "ok" }`

OpenAPI: visit `/docs` to see the `SceneResponse` model including the `source` field.

### Logging
- Uvicorn CLI: set the log level via `--log-level` (`critical|error|warning|info|debug`).
  - Example: `uvicorn lattice_api.main:app --reload --log-level debug --access-log`

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
    workflows.py      # Placeholder: CrewAI/MCP/VASP orchestration (band/DOS)
pyproject.toml
```

### Roadmap
- Prompt -> structure generation (`lattice_api/services/prompt_gen.py`)
- VASP band/DOS calculations (`lattice_api/services/workflows.py`)
- Validation/orchestration using CrewAI/MCP
