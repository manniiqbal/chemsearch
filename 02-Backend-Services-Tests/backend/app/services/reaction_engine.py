from rdkit.Chem import rdChemReactions

from app.domain.errors import InvalidReactionRuleError
from app.domain.reaction import ReactionParticipant, ReactionProductSet
from app.domain.reaction_rule import ReactionRule
from app.services.rdkit_service import RDKitService


class ReactionEngine:
    """A service that applies reaction rules to reactants to generate products."""

    def __init__(self, rdkit_service: RDKitService):
        self.rdkit_service = rdkit_service

    def apply_rule(
        self,
        rule: ReactionRule,
        reactants: list[ReactionParticipant],
    ) -> list[ReactionProductSet]:
        """Apply a reaction rule to a set of reactants and return the products."""
        if len(reactants) != rule.reactant_count:
            raise ValueError(
                f"Rule {rule.rule_id} expects {rule.reactant_count} reactants, "
                f"but {len(reactants)} were provided."
            )

        try:
            reaction = rdChemReactions.ReactionFromSmarts(rule.smarts)
        except Exception as exc:
            raise InvalidReactionRuleError(
                f"Invalid SMARTS for reaction rule {rule.rule_id}."
            ) from exc

        if reaction is None:
            raise InvalidReactionRuleError(f"Invalid SMARTS for reaction rule {rule.rule_id}.")

        reactant_mols = tuple(
            self.rdkit_service.validate_molecule(rp.canonical_smiles) for rp in reactants
        )

        product_sets = reaction.RunReactants(reactant_mols)

        converted_product_sets = []
        seen_product_sets = set()

        for product_set in product_sets:
            converted_products = [
                ReactionParticipant(
                    canonical_smiles=self.rdkit_service.mol_to_canonical_smiles(prod),
                    coefficient=1,
                )
                for prod in product_set
            ]

            product_key = tuple(sorted(product.canonical_smiles for product in converted_products))

            if product_key not in seen_product_sets:
                seen_product_sets.add(product_key)
                converted_product_sets.append(
                    ReactionProductSet(
                        products=converted_products,
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                    )
                )

        return converted_product_sets
