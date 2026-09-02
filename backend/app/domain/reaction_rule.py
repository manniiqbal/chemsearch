from dataclasses import dataclass, field

from app.domain.reaction import ReactionParticipant


@dataclass(frozen=True)
class RuleConstraints:
    """Optional environmental and condition constraints for a reaction rule."""

    min_temperature_c: float | None = None
    max_temperature_c: float | None = None

    min_pressure_bar: float | None = None
    max_pressure_bar: float | None = None

    min_duration_minutes: float | None = None
    max_duration_minutes: float | None = None

    min_ph: float | None = None
    max_ph: float | None = None

    allowed_solvents: list[str] | None = None


@dataclass(frozen=True)
class ReactionRule:
    rule_id: str
    name: str
    reaction_type: str
    smarts: str
    reactant_count: int

    required_reagents: list[ReactionParticipant] = field(default_factory=list)
    constraints: RuleConstraints | None = None

    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reactant_count, int):
            raise TypeError("reactant_count must be an integer")

        if self.reactant_count <= 0:
            raise ValueError("reactant_count must be at least 1")
