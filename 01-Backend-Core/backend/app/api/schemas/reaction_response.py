from pydantic import BaseModel, Field


class ReactionParticipantResponse(BaseModel):
    canonical_smiles: str
    coefficient: int


class ReactionProductSetResponse(BaseModel):
    products: list[ReactionParticipantResponse]
    rule_id: str | None = None
    rule_name: str | None = None


class AtomMappingResponse(BaseModel):
    reactant_atom_idx: int
    product_atom_idx: int


class BondChangeResponse(BaseModel):
    atom1_idx: int
    atom2_idx: int
    old_bond_order: float | None = None
    new_bond_order: float | None = None


class ReactionMappingResponse(BaseModel):
    atom_mappings: list[AtomMappingResponse] = Field(default_factory=list)
    broken_bonds: list[BondChangeResponse] = Field(default_factory=list)
    formed_bonds: list[BondChangeResponse] = Field(default_factory=list)
    changed_bonds: list[BondChangeResponse] = Field(default_factory=list)


class ReactionSimulationResponse(BaseModel):
    status: str
    reaction_type: str | None = None
    product_sets: list[ReactionProductSetResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    mappings: list[ReactionMappingResponse] = Field(default_factory=list)
