from app.domain.errors import InvalidReactionInputError
from app.domain.reaction_prediction import (
    ReactionPredictionRequest,
    ReactionPredictionResult,
)
from app.services.prediction_engine import PredictionEngine
from app.services.rdkit_service import RDKitService


class ReactionPredictionService:
    def __init__(
        self,
        prediction_engine: PredictionEngine,
        rdkit_service: RDKitService | None = None,
    ):
        self.prediction_engine = prediction_engine
        self.rdkit_service = rdkit_service

    def predict(
        self,
        request: ReactionPredictionRequest,
    ) -> ReactionPredictionResult:
        if not request.reactants:
            raise InvalidReactionInputError("At least one reactant is required.")

        if self.rdkit_service is not None:
            for participant in [*request.reactants, *request.reagents]:
                self.rdkit_service.validate_molecule(participant.canonical_smiles)

        candidates = self.prediction_engine.predict(request)
        return ReactionPredictionResult(
            candidates=candidates,
            warnings=[] if candidates else ["The model produced no valid products."],
        )
