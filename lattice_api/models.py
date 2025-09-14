from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field


class SceneResponse(BaseModel):
    scene: dict
    formula: str
    lattice: Dict[str, float]  # a,b,c,alpha,beta,gamma,volume
    n_sites: int
    source: Literal["upload", "prompt"]


class PromptRequest(BaseModel):
    prompt: str


# Export API models
FormatLiteral = Literal["cif_symm", "cif", "poscar", "json", "prismatic", "mpr"]
CellLiteral = Literal["input", "primitive", "conventional"]


class MPROptions(BaseModel):
    functional: Optional[str] = Field(default=None, description="DFT functional hint")
    potcar: Optional[Literal["MP", "Auto"]] = Field(default=None)
    kpoint_density: Optional[int] = Field(default=None)


class ExportOptions(BaseModel):
    cell: CellLiteral = Field(default="input")
    symmetrize: Optional[bool] = Field(default=None)
    mpr: Optional[MPROptions] = None


class ExportRequest(BaseModel):
    format: FormatLiteral
    material_id: Optional[str] = None
    cif: Optional[str] = None
    structure: Optional[dict] = None
    options: ExportOptions = Field(default_factory=ExportOptions)
