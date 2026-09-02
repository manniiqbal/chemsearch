from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from app.domain.reaction import ReactionParticipant
from app.domain.reaction_prediction import ReactionPredictionRequest
from app.services.reaction_t5_engine import ReactionT5Engine


class FakeWeight:
    def __init__(self, value):
        self.value = value

    def item(self):
        return self.value


class FakeTorch:
    @staticmethod
    def inference_mode():
        return nullcontext()

    @staticmethod
    def softmax(scores, dim=0):
        return scores


class FakeTokenizer:
    def __call__(self, value, **kwargs):
        assert value == "REACTANT:C=CREAGENT:"
        return {"input_ids": [1, 2, 3]}

    def batch_decode(self, sequences, **kwargs):
        return ["CC", "C(C)", "not-smiles", "CO"]


class FakeModel:
    def generate(self, **kwargs):
        return SimpleNamespace(
            sequences=[1, 2, 3, 4],
            sequences_scores=[
                FakeWeight(0.5),
                FakeWeight(0.3),
                FakeWeight(0.1),
                FakeWeight(0.1),
            ],
        )


def test_adapter_validates_deduplicates_and_renormalises_candidates():
    engine = ReactionT5Engine()
    assert engine.model is None

    engine.tokenizer = FakeTokenizer()
    engine.model = FakeModel()
    engine._torch = FakeTorch()

    candidates = engine.predict(ReactionPredictionRequest(reactants=[ReactionParticipant("C=C")]))

    assert [candidate.products[0].canonical_smiles for candidate in candidates] == [
        "CC",
        "CO",
    ]
    assert [candidate.rank for candidate in candidates] == [1, 2]
    assert sum(candidate.confidence for candidate in candidates) == pytest.approx(1.0)
    assert candidates[0].confidence == pytest.approx(5 / 6)
