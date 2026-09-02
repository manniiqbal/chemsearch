from pydantic import BaseModel, Field

from app.api.schemas.reaction_request import (
    ReactionConditionsRequest,
    ReactionParticipantRequest,
)


class ReactionPredictionRequestSchema(BaseModel):
    reactants: list[ReactionParticipantRequest] = Field(min_length=1, max_length=8)
    reagents: list[ReactionParticipantRequest] = Field(default_factory=list)
    conditions: ReactionConditionsRequest | None = None
