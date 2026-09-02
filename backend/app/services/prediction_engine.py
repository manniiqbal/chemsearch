from abc import ABC, abstractmethod

from app.domain.reaction_prediction import (
    ReactionPredictionCandidate,
    ReactionPredictionRequest,
)


class PredictionEngine(ABC):
    @abstractmethod
    def predict(
        self,
        request: ReactionPredictionRequest,
    ) -> list[ReactionPredictionCandidate]:
        pass
