from pydantic import BaseModel

from app.domain.search_input_type import SearchInputType


class MoleculeResponse(BaseModel):
    """A single resolved molecule"""

    canonical_smiles: str
    cid: int | None = None
    name: str | None = None
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    structure_svg: str | None = None


class MoleculeSearchResponse(BaseModel):
    """Molecule search response"""

    query: str
    requested_input_type: SearchInputType
    resolved_input_type: SearchInputType
    warnings: list[str] = []
    molecule: MoleculeResponse
