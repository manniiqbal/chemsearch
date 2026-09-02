import os

import pytest

from app.domain.reaction import ReactionParticipant
from app.domain.reaction_prediction import ReactionPredictionRequest
from app.services.reaction_t5_engine import ReactionT5Engine


@pytest.mark.skipif(
    os.getenv("RUN_MODEL_TESTS") != "1",
    reason="Set RUN_MODEL_TESTS=1 to download and run ReactionT5.",
)
def test_reaction_t5_engine_generates_prediction():
    engine = ReactionT5Engine()

    request = ReactionPredictionRequest(
        reactants=[
            ReactionParticipant(
                canonical_smiles="C=C",
                coefficient=1,
            )
        ],
        reagents=[],
    )

    result = engine.predict(request)

    assert len(result) >= 1
    assert len(result) <= 5

    first_candidate = result[0]

    assert len(first_candidate.products) >= 1
    assert first_candidate.products[0].canonical_smiles != ""
    assert first_candidate.rank == 1
    assert first_candidate.model_name == "sagawa/ReactionT5v2-forward"
    assert 0.0 <= first_candidate.confidence <= 1.0

    product_keys = [
        tuple(sorted(product.canonical_smiles for product in candidate.products))
        for candidate in result
    ]

    assert len(product_keys) == len(set(product_keys))

    confidences = [candidate.confidence for candidate in result]

    assert confidences == sorted(
        confidences,
        reverse=True,
    )

    ranks = [candidate.rank for candidate in result]

    assert ranks == list(range(1, len(result) + 1))

    assert sum(confidences) == pytest.approx(
        1.0,
        abs=1e-6,
    )
