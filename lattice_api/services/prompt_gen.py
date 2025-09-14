"""
Placeholder for prompt-driven structure generation.

Future plan:
- Accept natural-language prompts and generate candidate crystal structures
  using generative models or search (e.g., composition + prototype hints).
- Validate structures with pymatgen, then run VASP workflows to compute band
  structure and DOS.
- Orchestrate the workflow with Agents/MCP and verify outputs.
"""

from typing import Any, Dict


def generate_structure_from_prompt(prompt: str) -> Dict[str, Any]:
    """Not implemented yet. Reserved for future expansion.

    This function will map prompts -> crystal structures, then downstream to
    electronic structure calculations (band/DOS) for validation.
    """
    raise NotImplementedError("Prompt-driven structure generation is not implemented yet.")

