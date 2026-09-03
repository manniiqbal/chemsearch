from app.domain.default_reaction_rules import build_default_registry
from app.domain.reaction import (
    ReactionConditions,
    ReactionParticipant,
    ReactionRequest,
    ReactionStatus,
)
from app.domain.reaction_rule import ReactionRule, RuleConstraints
from app.services.rdkit_service import RDKitService
from app.services.reaction_engine import ReactionEngine
from app.services.reaction_rule_registry import ReactionRuleRegistry
from app.services.reaction_service import ReactionService


def build_reaction_service() -> ReactionService:
    rdkit_service = RDKitService()
    reaction_engine = ReactionEngine(rdkit_service)
    rule_registry = build_default_registry()

    return ReactionService(
        reaction_engine,
        rule_registry,
    )


def test_successful_hydrogenation_simulation():
    reaction_service = build_reaction_service()

    request = ReactionRequest(
        reactants=[ReactionParticipant(canonical_smiles="C=C")],
        reagents=[ReactionParticipant(canonical_smiles="[H][H]")],
        reaction_type="hydrogenation",
    )

    result = reaction_service.simulate_reaction(request)

    assert result.status == ReactionStatus.SIMULATED
    assert len(result.product_sets) == 1
    assert result.product_sets[0].products[0].canonical_smiles == "CC"


def test_missing_reaction_type_triggers_detection():
    reaction_service = build_reaction_service()

    request = ReactionRequest(
        reactants=[ReactionParticipant(canonical_smiles="CCO")],
        reaction_type=None,
    )

    result = reaction_service.simulate_reaction(request)

    assert result.status == ReactionStatus.SIMULATED
    assert result.reaction_type == "alcohol_oxidation"


def test_unsupported_reaction_type_returns_unsupported():
    reaction_service = build_reaction_service()

    request = ReactionRequest(
        reactants=[ReactionParticipant(canonical_smiles="C=C")],
        reaction_type="metathesis",
    )

    result = reaction_service.simulate_reaction(request)

    assert result.status == ReactionStatus.UNSUPPORTED
    assert result.product_sets == []


def test_incorrect_reactant_count_returns_failed():
    reaction_service = build_reaction_service()

    request = ReactionRequest(
        reactants=[
            ReactionParticipant(canonical_smiles="C=C"),
            ReactionParticipant(canonical_smiles="O"),
        ],
        reaction_type="hydrogenation",
    )

    result = reaction_service.simulate_reaction(request)

    assert result.status == ReactionStatus.FAILED
    assert result.product_sets == []


def test_no_reaction_returns_no_reaction():
    reaction_service = build_reaction_service()

    request = ReactionRequest(
        reactants=[ReactionParticipant(canonical_smiles="CC")],
        reagents=[ReactionParticipant(canonical_smiles="[H][H]")],
        reaction_type="hydrogenation",
    )

    result = reaction_service.simulate_reaction(request)

    assert result.status == ReactionStatus.NO_REACTION
    assert result.product_sets == []


def test_missing_required_conditions_simulates_with_warning():
    rdkit_service = RDKitService()
    reaction_engine = ReactionEngine(rdkit_service)

    constrained_rule = ReactionRule(
        rule_id="test_hydrogenation_conditions",
        name="Test Hydrogenation Conditions",
        reaction_type="hydrogenation",
        smarts="[C:1]=[C:2]>>[C:1]-[C:2]",
        reactant_count=1,
        constraints=RuleConstraints(
            min_temperature_c=20,
            max_temperature_c=80,
        ),
    )

    rule_registry = ReactionRuleRegistry()
    rule_registry.register(constrained_rule)

    reaction_service = ReactionService(
        reaction_engine,
        rule_registry,
    )

    request = ReactionRequest(
        reactants=[ReactionParticipant(canonical_smiles="C=C")],
        reaction_type="hydrogenation",
        conditions=None,
    )

    result = reaction_service.simulate_reaction(request)

    assert result.status == ReactionStatus.SIMULATED
    assert result.product_sets[0].products[0].canonical_smiles == "CC"
    assert len(result.warnings) > 0
    assert "condition" in result.warnings[0].lower()


def test_out_of_range_temperature_returns_failed():
    rdkit_service = RDKitService()
    reaction_engine = ReactionEngine(rdkit_service)

    constrained_rule = ReactionRule(
        rule_id="test_hydrogenation_conditions",
        name="Test Hydrogenation Conditions",
        reaction_type="hydrogenation",
        smarts="[C:1]=[C:2]>>[C:1]-[C:2]",
        reactant_count=1,
        constraints=RuleConstraints(
            min_temperature_c=20,
            max_temperature_c=80,
        ),
    )

    rule_registry = ReactionRuleRegistry()
    rule_registry.register(constrained_rule)

    reaction_service = ReactionService(
        reaction_engine,
        rule_registry,
    )

    request = ReactionRequest(
        reactants=[ReactionParticipant(canonical_smiles="C=C")],
        reaction_type="hydrogenation",
        conditions=ReactionConditions(
            temperature_c=120,
        ),
    )

    result = reaction_service.simulate_reaction(request)

    assert result.status == ReactionStatus.FAILED
    assert result.product_sets == []
