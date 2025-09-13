from typing import Dict, Literal

from pydantic import BaseModel


class SceneResponse(BaseModel):
    scene: dict
    formula: str
    lattice: Dict[str, float]  # a,b,c,alpha,beta,gamma,volume
    n_sites: int
    source: Literal["upload", "prompt"]


class PromptRequest(BaseModel):
    prompt: str

