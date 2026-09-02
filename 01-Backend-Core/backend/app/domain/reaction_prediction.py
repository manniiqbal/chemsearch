from dataclasses import dataclass, field

from app.domain.reaction import ReactionConditions, ReactionParticipant


@dataclass(frozen=True)
class ReactionPredictionRequest:
    reactants: list[ReactionParticipant]
    reagents: list[ReactionParticipant] = field(default_factory=list)
    conditions: ReactionConditions | None = None


@dataclass(frozen=True)
class ReactionPredictionCandidate:
    products: list[ReactionParticipant]
    confidence: float
    rank: int
    model_name: str | None

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if self.rank < 1:
            raise ValueError("rank must be at least 1")


@dataclass(frozen=True)
class ReactionPredictionResult:
    candidates: list[ReactionPredictionCandidate]
    warnings: list[str]
