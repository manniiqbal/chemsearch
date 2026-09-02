from app.domain.reaction_rule import ReactionRule


class ReactionRuleRegistry:
    """In-memory store of reaction rules."""

    def __init__(self) -> None:
        self._rules: dict[str, ReactionRule] = {}

    def register(self, rule: ReactionRule) -> None:
        """Register a rule using its unique rule ID."""
        if rule.rule_id in self._rules:
            raise ValueError(f"Rule '{rule.rule_id}' is already registered")

        self._rules[rule.rule_id] = rule

    def get_by_id(self, rule_id: str) -> ReactionRule | None:
        """Return one specific rule by its unique ID."""
        return self._rules.get(rule_id)

    def get_by_reaction_type(
        self,
        reaction_type: str,
    ) -> list[ReactionRule]:
        """Return all rules belonging to a reaction type."""
        return [rule for rule in self._rules.values() if rule.reaction_type == reaction_type]

    def list_all(self) -> list[ReactionRule]:
        """Return every rule in stable registration order."""
        return list(self._rules.values())
