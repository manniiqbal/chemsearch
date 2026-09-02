from fastapi import APIRouter, Request

from app.api.schemas.reaction_prediction_request import (
    ReactionPredictionRequestSchema,
)
from app.api.schemas.reaction_prediction_response import (
    ReactionPredictionCandidateResponse,
    ReactionPredictionResponseSchema,
)
from app.api.schemas.reaction_response import ReactionParticipantResponse
from app.domain.reaction import ReactionConditions, ReactionParticipant
from app.domain.reaction_prediction import ReactionPredictionRequest

router = APIRouter()


@router.post(
    "/reactions/predict",
    response_model=ReactionPredictionResponseSchema,
)
async def predict_reaction(
    payload: ReactionPredictionRequestSchema,
    request: Request,
):
    reactants = [
        ReactionParticipant(
            canonical_smiles=reactant.canonical_smiles,
            coefficient=reactant.coefficient,
        )
        for reactant in payload.reactants
    ]

    reagents = [
        ReactionParticipant(
            canonical_smiles=reagent.canonical_smiles,
            coefficient=reagent.coefficient,
        )
        for reagent in payload.reagents
    ]

    conditions = (
        ReactionConditions(
            temperature_c=payload.conditions.temperature_c,
            pressure_bar=payload.conditions.pressure_bar,
            duration_minutes=payload.conditions.duration_minutes,
            ph=payload.conditions.ph,
            solvent=payload.conditions.solvent,
            notes=payload.conditions.notes,
        )
        if payload.conditions is not None
        else None
    )

    prediction_request = ReactionPredictionRequest(
        reactants=reactants,
        reagents=reagents,
        conditions=conditions,
    )

    prediction_service = request.app.state.reaction_prediction_service
    result = prediction_service.predict(prediction_request)

    candidates = [
        ReactionPredictionCandidateResponse(
            products=[
                ReactionParticipantResponse(
                    canonical_smiles=product.canonical_smiles,
                    coefficient=product.coefficient,
                )
                for product in candidate.products
            ],
            confidence=candidate.confidence,
            rank=candidate.rank,
            model_name=candidate.model_name,
        )
        for candidate in result.candidates
    ]

    return ReactionPredictionResponseSchema(
        candidates=candidates,
        warnings=result.warnings,
    )
