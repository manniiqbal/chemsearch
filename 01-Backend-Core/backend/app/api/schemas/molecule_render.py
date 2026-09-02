from pydantic import BaseModel, Field, field_validator


class MoleculeRenderRequest(BaseModel):
    smiles: str = Field(min_length=1, max_length=2000)
    width: int = Field(default=420, ge=160, le=1000)
    height: int = Field(default=280, ge=120, le=800)

    @field_validator("smiles")
    @classmethod
    def clean_smiles(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("SMILES must not be blank")
        return cleaned


class MoleculeRenderResponse(BaseModel):
    canonical_smiles: str
    svg: str


class ReactionRuleResponse(BaseModel):
    rule_id: str
    name: str
    reaction_type: str
    reactant_count: int
    description: str | None = None
