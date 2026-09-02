from pydantic import BaseModel, Field, field_validator


class ReactionParticipantRequest(BaseModel):
    canonical_smiles: str = Field(min_length=1, max_length=2000)
    coefficient: int = Field(default=1, gt=0)

    @field_validator("canonical_smiles")
    @classmethod
    def clean_smiles(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("SMILES must not be blank")
        return cleaned


class ReactionConditionsRequest(BaseModel):
    temperature_c: float | None = None
    pressure_bar: float | None = None
    duration_minutes: float | None = None
    ph: float | None = None
    solvent: str | None = None
    notes: str | None = None


class ReactionSimulationRequest(BaseModel):
    reactants: list[ReactionParticipantRequest] = Field(min_length=1, max_length=4)
    reagents: list[ReactionParticipantRequest] = Field(default_factory=list)
    reaction_type: str | None = Field(default=None, max_length=100)
    conditions: ReactionConditionsRequest | None = None
