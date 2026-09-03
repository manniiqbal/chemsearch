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
    temperature_c: float | None = Field(default=None, ge=-273.15)
    pressure_bar: float | None = Field(default=None, gt=0)
    duration_minutes: float | None = Field(default=None, gt=0)
    ph: float | None = Field(default=None, ge=0, le=14)
    solvent: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=1000)


class ReactionSimulationRequest(BaseModel):
    reactants: list[ReactionParticipantRequest] = Field(min_length=1, max_length=4)
    reagents: list[ReactionParticipantRequest] = Field(default_factory=list, max_length=8)
    reaction_type: str | None = Field(default=None, max_length=100)
    conditions: ReactionConditionsRequest | None = None
