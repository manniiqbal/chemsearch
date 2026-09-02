from pydantic import BaseModel, Field

from app.api.schemas.reaction_response import ReactionParticipantResponse


class ReactionPredictionCandidateResponse(BaseModel):
    products: list[ReactionParticipantResponse]
    confidence: float
    rank: int
    model_name: str | None = None


class ReactionPredictionResponseSchema(BaseModel):
    candidates: list[ReactionPredictionCandidateResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
