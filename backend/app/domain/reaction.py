from dataclasses import dataclass, field
from enum import Enum


class ReactionStatus(str, Enum):
    PENDING = "pending"
    SIMULATED = "simulated"
    NO_REACTION = "no_reaction"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ReactionParticipant:
    """One molecule participating in a reaction."""

    canonical_smiles: str
    coefficient: int = 1

    def __post_init__(self) -> None:
        if self.coefficient <= 0:
            raise ValueError("Reaction coefficient must be positive")


@dataclass(frozen=True)
class ReactionConditions:
    """Optional conditions under which a reaction occurs."""

    temperature_c: float | None = None
    pressure_bar: float | None = None
    duration_minutes: float | None = None
    ph: float | None = None
    solvent: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ReactionRequest:
    """A reaction to simulate: what goes in and under what conditions."""

    reactants: list[ReactionParticipant]
    reagents: list[ReactionParticipant] = field(default_factory=list)
    reaction_type: str | None = None
    conditions: ReactionConditions | None = None


@dataclass(frozen=True)
class ReactionProductSet:
    """One possible set of products from a reaction."""

    products: list[ReactionParticipant]
    rule_id: str | None = None
    rule_name: str | None = None


@dataclass(frozen=True)
class ReactionResult:
    """Outcome of a simulated reaction."""

    status: ReactionStatus
    reaction_type: str | None = None
    product_sets: list[ReactionProductSet] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status == ReactionStatus.SIMULATED and not self.product_sets:
            raise ValueError("SIMULATED requires at least one product set")

        if self.status == ReactionStatus.NO_REACTION and self.product_sets:
            raise ValueError("NO_REACTION must not contain product sets")
