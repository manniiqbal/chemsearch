from app.domain.default_reaction_rules import ALKENE_HYDROGENATION
from app.domain.reaction import ReactionParticipant
from app.services.rdkit_service import RDKitService
from app.services.reaction_engine import ReactionEngine


def test_alkene_hydrogenation():
    rdkit_service = RDKitService()
    engine = ReactionEngine(rdkit_service)

    reactants = [ReactionParticipant(canonical_smiles="C=C")]

    product_sets = engine.apply_rule(
        ALKENE_HYDROGENATION,
        reactants,
    )

    assert len(product_sets) == 1
    assert len(product_sets[0].products) == 1
    assert product_sets[0].products[0].canonical_smiles == "CC"
