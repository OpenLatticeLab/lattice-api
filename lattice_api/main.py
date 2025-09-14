from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lattice_api.routers.health import router as health_router
from lattice_api.routers.prompt import router as prompt_router
from lattice_api.routers.export import router as export_router
from lattice_api.routers.scene import router as scene_router

# Set Crystal Toolkit default color scheme if not provided externally
os.environ.setdefault("CT_LEGEND_COLOR_SCHEME", "VESTA")


def get_allowed_origins() -> List[str]:
    """Return explicit allowed origins list from env.

    Env var: CORS_ALLOW_ORIGINS (comma-separated). If unset/empty, return [].
    """
    origins_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    return [o.strip() for o in origins_env.split(",") if o.strip()]


def get_allowed_origin_regex() -> str | None:
    """Return an optional regex for allowed origins from env.

    Env var: CORS_ALLOW_ORIGIN_REGEX, e.g. ^https?://(localhost|127\.0\.0\.1)(:\\d+)?$
    If unset or empty, return None.
    """
    regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX", "^https?://(localhost|127\.0\.0\.1)(:\\d+)?$").strip()
    return regex or None


app = FastAPI(
    title="lattice-api",
    description=(
        "API for CIF -> Crystal Toolkit Scene conversion.\n\n"
        "Future: Prompt -> structure generation -> VASP band/DOS -> CrewAI/MCP validation."
    ),
    version="0.1.0",
)

# CORS
_origin_regex = get_allowed_origin_regex()
_allowed_origins = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)
app.include_router(scene_router)
app.include_router(prompt_router)
app.include_router(export_router)


@app.get("/")
def root():
    return {"service": "lattice-api"}
