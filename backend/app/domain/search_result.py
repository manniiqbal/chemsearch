from dataclasses import dataclass, field

from app.domain.search_input_type import SearchInputType


@dataclass
class SearchResult:
    """Search result"""

    canonical_smiles: str
    cid: int | None = None
    name: str | None = None
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    structure_svg: str | None = None


@dataclass
class SearchOutcome:
    query: str
    requested_input_type: SearchInputType
    resolved_input_type: SearchInputType
    molecule: SearchResult
    warnings: list[str] = field(default_factory=list)
