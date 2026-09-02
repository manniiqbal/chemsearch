"""Conservative reaction SMARTS used by the deterministic simulator.

Rules model principal organic products. Broad or regioselective transformations
are deliberately left to the ML predictor.
"""

from app.domain.reaction import ReactionParticipant
from app.domain.reaction_rule import ReactionRule
from app.services.reaction_rule_registry import ReactionRuleRegistry

ALKENE_HYDROGENATION = ReactionRule(
    rule_id="alkene_hydrogenation_v1",
    name="Alkene hydrogenation",
    reaction_type="hydrogenation",
    smarts="[C;!$(C=O):1]=[C:2]>>[C:1]-[C:2]",
    reactant_count=1,
    description=("Reduces one non-carbonyl carbon-carbon double bond."),
)

ALKENE_CHLORINATION = ReactionRule(
    rule_id="alkene_chlorination_v1",
    name="Alkene chlorination",
    reaction_type="alkene_halogenation",
    smarts="[C;!$(C=O):1]=[C:2]>>[C:1]([Cl])-[C:2]([Cl])",
    reactant_count=1,
    required_reagents=[ReactionParticipant("ClCl")],
    description="Adds chlorine across one non-aromatic carbon-carbon double bond.",
)

ALKENE_BROMINATION = ReactionRule(
    rule_id="alkene_bromination_v1",
    name="Alkene bromination",
    reaction_type="alkene_halogenation",
    smarts="[C;!$(C=O):1]=[C:2]>>[C:1]([Br])-[C:2]([Br])",
    reactant_count=1,
    required_reagents=[ReactionParticipant("BrBr")],
    description="Adds bromine across one non-aromatic carbon-carbon double bond.",
)

PRIMARY_ALCOHOL_OXIDATION = ReactionRule(
    rule_id="primary_alcohol_oxidation_v1",
    name="Primary alcohol oxidation",
    reaction_type="alcohol_oxidation",
    smarts="[CH2:1][OH:2]>>[CH:1]=[O:2]",
    reactant_count=1,
    description="Oxidises a primary alcohol to its aldehyde.",
)

SECONDARY_ALCOHOL_OXIDATION = ReactionRule(
    rule_id="secondary_alcohol_oxidation_v1",
    name="Secondary alcohol oxidation",
    reaction_type="alcohol_oxidation",
    smarts="[CH:1]([#6:2])([#6:3])[OH:4]>>[C:1]([#6:2])([#6:3])=[O:4]",
    reactant_count=1,
    description="Oxidises a secondary alcohol to its ketone.",
)

ALDEHYDE_REDUCTION = ReactionRule(
    rule_id="aldehyde_reduction_v1",
    name="Aldehyde reduction",
    reaction_type="carbonyl_reduction",
    smarts="[CH:1]=[O:2]>>[CH2:1][OH:2]",
    reactant_count=1,
    description="Reduces an aldehyde carbonyl to a primary alcohol.",
)

KETONE_REDUCTION = ReactionRule(
    rule_id="ketone_reduction_v1",
    name="Ketone reduction",
    reaction_type="carbonyl_reduction",
    smarts="[C:1](=[O:2])([#6:3])[#6:4]>>[CH:1]([OH:2])([#6:3])[#6:4]",
    reactant_count=1,
    description="Reduces a ketone carbonyl to a secondary alcohol.",
)

FISCHER_ESTERIFICATION = ReactionRule(
    rule_id="fischer_esterification_v1",
    name="Fischer esterification",
    reaction_type="esterification",
    smarts="[C:1](=[O:2])[OH:3].[OH:4][C:5]>>[C:1](=[O:2])[O:4][C:5]",
    reactant_count=2,
    description="Forms the principal ester product from a carboxylic acid and alcohol.",
)

ESTER_HYDROLYSIS = ReactionRule(
    rule_id="ester_hydrolysis_v1",
    name="Ester hydrolysis",
    reaction_type="ester_hydrolysis",
    smarts="[C:1](=[O:2])[O:3][C:4]>>[C:1](=[O:2])O.[OH:3][C:4]",
    reactant_count=1,
    description="Cleaves a simple ester into its acid and alcohol products.",
)

ALKYL_HALIDE_SUBSTITUTION = ReactionRule(
    rule_id="alkyl_halide_substitution_v1",
    name="Alkyl halide substitution",
    reaction_type="nucleophilic_substitution",
    smarts="[C;X4:1][Cl,Br,I:2]>>[C:1]O",
    reactant_count=1,
    description="Replaces a simple alkyl chloride, bromide, or iodide with hydroxyl.",
)

DEFAULT_RULES: tuple[ReactionRule, ...] = (
    ALKENE_HYDROGENATION,
    ALKENE_CHLORINATION,
    ALKENE_BROMINATION,
    PRIMARY_ALCOHOL_OXIDATION,
    SECONDARY_ALCOHOL_OXIDATION,
    ALDEHYDE_REDUCTION,
    KETONE_REDUCTION,
    FISCHER_ESTERIFICATION,
    ESTER_HYDROLYSIS,
    ALKYL_HALIDE_SUBSTITUTION,
)


def build_default_registry() -> ReactionRuleRegistry:
    """Construct a registry populated with every built-in rule."""
    registry = ReactionRuleRegistry()
    for rule in DEFAULT_RULES:
        registry.register(rule)
    return registry
