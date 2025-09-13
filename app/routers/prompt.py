from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models import PromptRequest


router = APIRouter(prefix="/api", tags=["prompt"])


@router.post("/prompt-structure")
async def prompt_structure(req: PromptRequest):
    """Reserved endpoint for prompt-driven structure generation.

    Returns 501 Not Implemented for now but includes source="prompt" in response.
    """
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "detail": "Prompt-driven structure generation is not implemented yet.",
            "source": "prompt",
        },
    )

