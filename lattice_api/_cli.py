from __future__ import annotations

import os

import uvicorn


def serve():
    """Run the development server.

    Example: `python -m lattice_api._cli` or `lattice-api serve` if installed.
    """
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("lattice_api.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":  # pragma: no cover
    serve()
