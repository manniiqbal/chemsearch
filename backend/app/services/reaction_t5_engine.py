"""Lazy, process-scoped adapter for the ReactionT5 forward predictor."""

from threading import Lock

from app.domain.errors import PredictionUnavailableError
from app.domain.reaction import ReactionParticipant
from app.domain.reaction_prediction import (
    ReactionPredictionCandidate,
    ReactionPredictionRequest,
)
from app.services.prediction_engine import PredictionEngine
from app.services.rdkit_service import RDKitService


class ReactionT5Engine(PredictionEngine):
    def __init__(self, rdkit_service: RDKitService | None = None):
        self.model_name = "sagawa/ReactionT5v2-forward"
        self.rdkit_service = rdkit_service or RDKitService()
        self.tokenizer = None
        self.model = None
        self._torch = None
        self._load_lock = Lock()

    def _ensure_loaded(self) -> None:
        if self.model is not None and self.tokenizer is not None:
            return

        with self._load_lock:
            if self.model is not None and self.tokenizer is not None:
                return
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

                self._torch = torch
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
                self.model.eval()
            except Exception as exc:
                self.tokenizer = None
                self.model = None
                raise PredictionUnavailableError(
                    "ReactionT5 could not be loaded. Check model-cache and network access."
                ) from exc

    def predict(
        self,
        request: ReactionPredictionRequest,
    ) -> list[ReactionPredictionCandidate]:
        self._ensure_loaded()
        assert self.tokenizer is not None
        assert self.model is not None
        assert self._torch is not None

        reactant_smiles = ".".join(reactant.canonical_smiles for reactant in request.reactants)
        reagent_smiles = ".".join(reagent.canonical_smiles for reagent in request.reagents)
        input_text = f"REACTANT:{reactant_smiles}REAGENT:{reagent_smiles}"
        encoded = self.tokenizer(input_text, return_tensors="pt", truncation=True)

        try:
            with self._torch.inference_mode():
                generated = self.model.generate(
                    **encoded,
                    num_beams=5,
                    num_return_sequences=5,
                    return_dict_in_generate=True,
                    output_scores=True,
                    max_new_tokens=256,
                )
        except Exception as exc:
            raise PredictionUnavailableError(
                "ReactionT5 inference failed for this request."
            ) from exc

        decoded_predictions = self.tokenizer.batch_decode(
            generated.sequences,
            skip_special_tokens=True,
        )
        beam_weights = self._torch.softmax(generated.sequences_scores, dim=0)
        deduplicated: dict[tuple[str, ...], tuple[list[ReactionParticipant], float]] = {}

        for decoded, weight in zip(decoded_predictions, beam_weights, strict=False):
            raw_products = [
                part for part in decoded.replace(" ", "").rstrip(".").split(".") if part
            ]
            if not raw_products:
                continue
            try:
                canonical_products = [
                    self.rdkit_service.canonicalise_molecule(smiles) for smiles in raw_products
                ]
            except Exception:
                continue

            key = tuple(sorted(canonical_products))
            confidence = float(weight.item())
            existing = deduplicated.get(key)
            if existing is None or confidence > existing[1]:
                deduplicated[key] = (
                    [ReactionParticipant(smiles) for smiles in canonical_products],
                    confidence,
                )

        ranked = sorted(deduplicated.values(), key=lambda item: item[1], reverse=True)
        total = sum(weight for _, weight in ranked)
        if total <= 0:
            return []

        return [
            ReactionPredictionCandidate(
                products=products,
                confidence=weight / total,
                rank=rank,
                model_name=self.model_name,
            )
            for rank, (products, weight) in enumerate(ranked, start=1)
        ]
