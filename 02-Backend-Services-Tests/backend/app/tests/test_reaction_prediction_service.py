from app.domain.reaction import ReactionParticipant
from app.domain.reaction_prediction import (
    ReactionPredictionCandidate,
    ReactionPredictionRequest,
)
from app.services.prediction_engine import PredictionEngine
from app.services.prediction_service import ReactionPredictionService


class FakePredictionEngine(PredictionEngine):
    def predict(
        self,
        request: ReactionPredictionRequest,
    ) -> list[ReactionPredictionCandidate]:
        return [
            ReactionPredictionCandidate(
                products=[ReactionParticipant(canonical_smiles="CC")],
                confidence=0.9,
                rank=1,
                model_name="fake model",
            )
        ]


def test_prediction_service_returns_candidates():
    engine = FakePredictionEngine()
    service = ReactionPredictionService(engine)

    request = ReactionPredictionRequest(reactants=[ReactionParticipant(canonical_smiles="C=C")])

    result = service.predict(request)

    assert len(result.candidates) == 1
    assert result.candidates[0].confidence == 0.9
    assert result.candidates[0].rank == 1
    assert result.candidates[0].products[0].canonical_smiles == "CC"
    assert result.warnings == []
