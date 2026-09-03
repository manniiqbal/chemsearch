import pytest

from app.domain.default_reaction_rules import DEFAULT_RULES, build_default_registry
from app.domain.reaction import ReactionParticipant, ReactionRequest, ReactionStatus
from app.services.rdkit_service import RDKitService
from app.services.reaction_engine import ReactionEngine
from app.services.reaction_service import ReactionService


@pytest.fixture
def service():
    rdkit = RDKitService()
    return ReactionService(ReactionEngine(rdkit), build_default_registry())


@pytest.mark.parametrize(
    ("reaction_type", "reactants", "reagents", "expected_products"),
    [
        ("hydrogenation", ["C=C"], ["[H][H]"], {"CC"}),
        ("alkene_halogenation", ["C=C"], ["ClCl"], {"ClCCCl"}),
        ("alkene_halogenation", ["C=C"], ["BrBr"], {"BrCCBr"}),
        ("alcohol_oxidation", ["CCO"], [], {"CC=O"}),
        ("alcohol_oxidation", ["CC(O)C"], [], {"CC(C)=O"}),
        ("aerobic_oxidation", ["CCO", "O=O"], [], {"CC(=O)O", "O"}),
        ("carbonyl_reduction", ["CC=O"], [], {"CCO"}),
        ("carbonyl_reduction", ["CC(C)=O"], [], {"CC(C)O"}),
        ("esterification", ["CC(=O)O", "CO"], [], {"COC(C)=O"}),
        ("ester_hydrolysis", ["CC(=O)OC"], [], {"CC(=O)O", "CO"}),
        ("nucleophilic_substitution", ["CCCl"], [], {"CCO"}),
    ],
)
def test_curated_rule_valid_transformations(
    service, reaction_type, reactants, reagents, expected_products
):
    result = service.simulate_reaction(
        ReactionRequest(
            reactants=[ReactionParticipant(value) for value in reactants],
            reagents=[ReactionParticipant(value) for value in reagents],
            reaction_type=reaction_type,
        )
    )
    assert result.status == ReactionStatus.SIMULATED
    assert any(
        {product.canonical_smiles for product in product_set.products} == expected_products
        for product_set in result.product_sets
    )
    assert all(product_set.rule_id for product_set in result.product_sets)


@pytest.mark.parametrize("rule", DEFAULT_RULES, ids=lambda rule: rule.rule_id)
def test_each_rule_rejects_incorrect_reactant_count(rule):
    engine = ReactionEngine(RDKitService())
    with pytest.raises(ValueError, match="expects"):
        engine.apply_rule(rule, [])


@pytest.mark.parametrize(
    "reaction_type",
    sorted({rule.reaction_type for rule in DEFAULT_RULES}),
)
def test_each_reaction_class_ignores_incompatible_substrate(service, reaction_type):
    expected_count = build_default_registry().get_by_reaction_type(reaction_type)[0].reactant_count
    inert = [ReactionParticipant("C")] * expected_count
    result = service.simulate_reaction(
        ReactionRequest(reactants=inert, reaction_type=reaction_type)
    )
    assert result.status in {ReactionStatus.NO_REACTION, ReactionStatus.FAILED}


def test_reaction_type_is_detected_from_chemicals(service):
    result = service.simulate_reaction(
        ReactionRequest(
            reactants=[ReactionParticipant("CCO"), ReactionParticipant("O=O")],
        )
    )
    assert result.status == ReactionStatus.SIMULATED
    assert result.reaction_type == "aerobic_oxidation"


def test_hydrogenation_requires_hydrogen(service):
    result = service.simulate_reaction(
        ReactionRequest(reactants=[ReactionParticipant("C=C")])
    )
    assert result.status != ReactionStatus.SIMULATED


def test_hydrogenation_accepts_pubchem_hydrogen_notation(service):
    result = service.simulate_reaction(
        ReactionRequest(
            reactants=[ReactionParticipant("C=C")],
            reagents=[ReactionParticipant("[HH]")],
        )
    )
    assert result.status == ReactionStatus.SIMULATED
    assert result.reaction_type == "hydrogenation"


@pytest.mark.parametrize(
    ("reactants", "expected_type"),
    [
        (["O=O", "CCO"], "aerobic_oxidation"),
        (["CO", "CC(=O)O"], "esterification"),
    ],
)
def test_two_reactant_rules_accept_reversed_input_order(service, reactants, expected_type):
    result = service.simulate_reaction(
        ReactionRequest(reactants=[ReactionParticipant(value) for value in reactants])
    )
    assert result.status == ReactionStatus.SIMULATED
    assert result.reaction_type == expected_type
