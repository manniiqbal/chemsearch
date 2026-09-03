from app.domain.reaction import (
    ReactionProductSet,
    ReactionRequest,
    ReactionResult,
    ReactionStatus,
)
from app.domain.reaction_rule import ReactionRule
from app.services.reaction_engine import ReactionEngine
from app.services.reaction_rule_registry import ReactionRuleRegistry


class ReactionService:
    """Orchestrates complete rule-based reaction simulations."""

    def __init__(
        self,
        reaction_engine: ReactionEngine,
        rule_registry: ReactionRuleRegistry,
    ):
        self.reaction_engine = reaction_engine
        self.rule_registry = rule_registry

    def simulate_reaction(
        self,
        reaction_request: ReactionRequest,
    ) -> ReactionResult:
        """Simulate a reaction based on the provided request."""

        if not reaction_request.reactants:
            return ReactionResult(
                status=ReactionStatus.FAILED,
                warnings=["At least one reactant is required."],
            )

        for participant in [
            *reaction_request.reactants,
            *reaction_request.reagents,
        ]:
            self.reaction_engine.rdkit_service.validate_molecule(participant.canonical_smiles)

        matching_rules = (
            self.rule_registry.get_by_reaction_type(reaction_request.reaction_type)
            if reaction_request.reaction_type
            else self.rule_registry.list_all()
        )

        if not matching_rules:
            return ReactionResult(
                status=ReactionStatus.UNSUPPORTED,
                reaction_type=reaction_request.reaction_type,
                warnings=["That reaction is not in the supported rule library yet."],
            )

        compatible_rules: list[ReactionRule] = []
        compatibility_warnings: list[str] = []

        for rule in matching_rules:
            compatible, rule_warnings = self._is_rule_compatible(
                rule,
                reaction_request,
            )

            if compatible:
                compatible_rules.append(rule)
                compatibility_warnings.extend(rule_warnings)

        if not compatible_rules:
            return ReactionResult(
                status=ReactionStatus.FAILED,
                reaction_type=reaction_request.reaction_type,
                warnings=[
                    "No supported reaction matches these chemicals. Check the names, "
                    "then try one of the tested examples."
                ],
            )

        all_product_sets: list[ReactionProductSet] = []
        warnings: list[str] = list(compatibility_warnings)
        successful_executions = 0

        for rule in compatible_rules:
            try:
                product_sets = self.reaction_engine.apply_rule(
                    rule,
                    reaction_request.reactants,
                )

                successful_executions += 1
                all_product_sets.extend(product_sets)

            except Exception as exc:
                warnings.append(f"Rule '{rule.rule_id}' failed to execute: {str(exc)}")

        if successful_executions == 0:
            return ReactionResult(
                status=ReactionStatus.FAILED,
                reaction_type=reaction_request.reaction_type,
                warnings=warnings or ["All compatible reaction rules failed to execute."],
            )

        deduplicated_product_sets = self._deduplicate_product_sets(all_product_sets)

        if not deduplicated_product_sets:
            return ReactionResult(
                status=ReactionStatus.NO_REACTION,
                reaction_type=reaction_request.reaction_type,
                warnings=warnings or ["No compatible rules produced products for these reactants."],
            )

        detected_types = {
            rule.reaction_type
            for rule in compatible_rules
            if any(product_set.rule_id == rule.rule_id for product_set in deduplicated_product_sets)
        }
        detected_type = (
            reaction_request.reaction_type
            or (next(iter(detected_types)) if len(detected_types) == 1 else "multiple_matches")
        )

        return ReactionResult(
            status=ReactionStatus.SIMULATED,
            reaction_type=detected_type,
            product_sets=deduplicated_product_sets,
            warnings=warnings,
        )

    def _is_rule_compatible(
        self,
        rule: ReactionRule,
        reaction_request: ReactionRequest,
    ) -> tuple[bool, list[str]]:
        """Check whether a reaction rule is compatible with a reaction request."""

        warnings: list[str] = []

        if rule.reactant_count != len(reaction_request.reactants):
            return False, warnings

        if not self._has_required_reagents(
            rule,
            reaction_request,
        ):
            return False, warnings

        constraints = rule.constraints

        if constraints is None:
            return True, warnings

        conditions = reaction_request.conditions

        if conditions is None:
            warnings.append(
                f"Rule '{rule.rule_id}' has condition constraints, "
                f"but no reaction conditions were provided."
            )
            return True, warnings

        if conditions.temperature_c is not None:
            if (
                constraints.min_temperature_c is not None
                and conditions.temperature_c < constraints.min_temperature_c
            ):
                return False, warnings

            if (
                constraints.max_temperature_c is not None
                and conditions.temperature_c > constraints.max_temperature_c
            ):
                return False, warnings

        elif constraints.min_temperature_c is not None or constraints.max_temperature_c is not None:
            warnings.append(f"Temperature was not provided for rule '{rule.rule_id}'.")

        if conditions.pressure_bar is not None:
            if (
                constraints.min_pressure_bar is not None
                and conditions.pressure_bar < constraints.min_pressure_bar
            ):
                return False, warnings

            if (
                constraints.max_pressure_bar is not None
                and conditions.pressure_bar > constraints.max_pressure_bar
            ):
                return False, warnings

        elif constraints.min_pressure_bar is not None or constraints.max_pressure_bar is not None:
            warnings.append(f"Pressure was not provided for rule '{rule.rule_id}'.")

        if conditions.duration_minutes is not None:
            if (
                constraints.min_duration_minutes is not None
                and conditions.duration_minutes < constraints.min_duration_minutes
            ):
                return False, warnings

            if (
                constraints.max_duration_minutes is not None
                and conditions.duration_minutes > constraints.max_duration_minutes
            ):
                return False, warnings

        elif (
            constraints.min_duration_minutes is not None
            or constraints.max_duration_minutes is not None
        ):
            warnings.append(f"Duration was not provided for rule '{rule.rule_id}'.")

        if conditions.ph is not None:
            if constraints.min_ph is not None and conditions.ph < constraints.min_ph:
                return False, warnings

            if constraints.max_ph is not None and conditions.ph > constraints.max_ph:
                return False, warnings

        elif constraints.min_ph is not None or constraints.max_ph is not None:
            warnings.append(f"pH was not provided for rule '{rule.rule_id}'.")

        if constraints.allowed_solvents is not None:
            if conditions.solvent is None:
                warnings.append(f"Solvent was not provided for rule '{rule.rule_id}'.")

            elif conditions.solvent not in constraints.allowed_solvents:
                return False, warnings

        return True, warnings

    def _has_required_reagents(
        self,
        rule: ReactionRule,
        reaction_request: ReactionRequest,
    ) -> bool:
        """Check whether all reagents required by a rule were supplied."""

        requested_reagent_counts: dict[str, int] = {}

        for reagent in reaction_request.reagents:
            identity = self._reagent_identity(reagent.canonical_smiles)
            requested_reagent_counts[identity] = (
                requested_reagent_counts.get(identity, 0) + reagent.coefficient
            )

        for required_reagent in rule.required_reagents:
            canonical_required = self._reagent_identity(required_reagent.canonical_smiles)
            available_count = requested_reagent_counts.get(
                canonical_required,
                0,
            )

            if available_count < required_reagent.coefficient:
                return False

        return True

    def _reagent_identity(self, smiles: str) -> str:
        """Treat common diatomic reagent notations as the same molecule."""
        formula = self.reaction_engine.rdkit_service.molecular_formula(smiles)
        if formula in {"H2", "Cl2", "Br2"}:
            return formula
        return self.reaction_engine.rdkit_service.canonicalise_molecule(smiles)

    def _deduplicate_product_sets(
        self,
        product_sets: list[ReactionProductSet],
    ) -> list[ReactionProductSet]:
        """Remove duplicate candidate product sets."""

        unique_product_sets: list[ReactionProductSet] = []
        seen_product_sets: set[tuple[tuple[str, int], ...]] = set()

        for product_set in product_sets:
            product_key = tuple(
                sorted(
                    (
                        product.canonical_smiles,
                        product.coefficient,
                    )
                    for product in product_set.products
                )
            )

            if product_key in seen_product_sets:
                continue

            seen_product_sets.add(product_key)
            unique_product_sets.append(product_set)

        return unique_product_sets
