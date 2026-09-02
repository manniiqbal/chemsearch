from dataclasses import dataclass, field


@dataclass(frozen=True)
class BondChange:
    """A change in a bond during a reaction."""

    atom1_idx: int
    atom2_idx: int
    new_bond_order: float | None = None  # None indicates bond removal
    old_bond_order: float | None = None  # None indicates bond creation


@dataclass(frozen=True)
class AtomMappingRecord:
    """Mapping of an atom from reactant to product."""

    reactant_atom_idx: int
    product_atom_idx: int


@dataclass(frozen=True)
class ReactionMappingResult:
    """A bond change that results from a reaction."""

    atom_mappings: list[AtomMappingRecord]
    broken_bonds: list[BondChange] = field(default_factory=list)
    formed_bonds: list[BondChange] = field(default_factory=list)
    changed_bonds: list[BondChange] = field(default_factory=list)
