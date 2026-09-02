from rdkit.Chem import rdChemReactions

from app.domain.errors import InvalidReactionRuleError
from app.domain.reaction import ReactionParticipant
from app.domain.reaction_mapping import (
    AtomMappingRecord,
    BondChange,
    ReactionMappingResult,
)
from app.domain.reaction_rule import ReactionRule
from app.services.rdkit_service import RDKitService


class ReactionMappingService:
    """Detects atom mappings and structural bond changes in reactions."""

    def __init__(self, rdkit_service: RDKitService):
        self.rdkit_service = rdkit_service

    def map_reaction(
        self,
        rule: ReactionRule,
        reactants: list[ReactionParticipant],
        products: list[ReactionParticipant],
    ) -> ReactionMappingResult:
        """Analyse atom correspondence and bond changes."""

        try:
            reaction = rdChemReactions.ReactionFromSmarts(rule.smarts)
        except Exception as exc:
            raise InvalidReactionRuleError(
                f"Invalid SMARTS for reaction rule '{rule.rule_id}'."
            ) from exc

        if reaction is None:
            raise InvalidReactionRuleError(f"Invalid SMARTS for reaction rule '{rule.rule_id}'.")

        reactant_mols = [
            self.rdkit_service.validate_molecule(reactant.canonical_smiles)
            for reactant in reactants
        ]

        for reactant_idx, reactant_mol in enumerate(reactant_mols):
            for atom in reactant_mol.GetAtoms():
                atom.SetIntProp("reactant_idx", reactant_idx)

        raw_product_sets = reaction.RunReactants(tuple(reactant_mols))

        selected_products = self._find_matching_product_set(
            raw_product_sets,
            products,
        )

        atom_map_to_reactant = self._build_atom_map_to_reactant(reaction)

        reactant_offsets = self._build_atom_offsets(reactant_mols)
        product_offsets = self._build_atom_offsets(selected_products)

        product_to_reactant_atom: dict[
            tuple[int, int],
            int,
        ] = {}

        atom_mappings: list[AtomMappingRecord] = []

        for product_idx, product_mol in enumerate(selected_products):
            for product_atom in product_mol.GetAtoms():
                source = self._get_source_atom(
                    product_atom,
                    atom_map_to_reactant,
                )

                if source is None:
                    continue

                source_reactant_idx, source_atom_idx = source

                reactant_global_idx = reactant_offsets[source_reactant_idx] + source_atom_idx

                product_global_idx = product_offsets[product_idx] + product_atom.GetIdx()

                product_to_reactant_atom[(product_idx, product_atom.GetIdx())] = reactant_global_idx

                atom_mappings.append(
                    AtomMappingRecord(
                        reactant_atom_idx=reactant_global_idx,
                        product_atom_idx=product_global_idx,
                    )
                )

        reactant_bonds = self._collect_reactant_bonds(
            reactant_mols,
            reactant_offsets,
        )

        product_bonds = self._collect_product_bonds(
            selected_products,
            product_to_reactant_atom,
        )

        broken_bonds: list[BondChange] = []
        formed_bonds: list[BondChange] = []
        changed_bonds: list[BondChange] = []

        all_bond_keys = set(reactant_bonds) | set(product_bonds)

        for atom_pair in all_bond_keys:
            old_order = reactant_bonds.get(atom_pair)
            new_order = product_bonds.get(atom_pair)

            if old_order is not None and new_order is None:
                broken_bonds.append(
                    BondChange(
                        atom1_idx=atom_pair[0],
                        atom2_idx=atom_pair[1],
                        old_bond_order=old_order,
                        new_bond_order=None,
                    )
                )

            elif old_order is None and new_order is not None:
                formed_bonds.append(
                    BondChange(
                        atom1_idx=atom_pair[0],
                        atom2_idx=atom_pair[1],
                        old_bond_order=None,
                        new_bond_order=new_order,
                    )
                )

            elif old_order is not None and new_order is not None and old_order != new_order:
                changed_bonds.append(
                    BondChange(
                        atom1_idx=atom_pair[0],
                        atom2_idx=atom_pair[1],
                        old_bond_order=old_order,
                        new_bond_order=new_order,
                    )
                )

        return ReactionMappingResult(
            atom_mappings=atom_mappings,
            broken_bonds=broken_bonds,
            formed_bonds=formed_bonds,
            changed_bonds=changed_bonds,
        )

    def _find_matching_product_set(
        self,
        raw_product_sets,
        requested_products: list[ReactionParticipant],
    ):
        """Find the RDKit product set matching the supplied products."""

        requested_smiles = sorted(product.canonical_smiles for product in requested_products)

        for product_set in raw_product_sets:
            candidate_smiles = sorted(
                self.rdkit_service.mol_to_canonical_smiles(product) for product in product_set
            )

            if candidate_smiles == requested_smiles:
                return product_set

        raise ValueError(
            "The supplied products do not match any product set generated by the reaction rule."
        )

    def _build_atom_map_to_reactant(
        self,
        reaction,
    ) -> dict[int, int]:
        """Map SMARTS atom-map numbers to their reactant template."""

        atom_map_to_reactant: dict[int, int] = {}

        for reactant_idx in range(reaction.GetNumReactantTemplates()):
            template = reaction.GetReactantTemplate(reactant_idx)

            for atom in template.GetAtoms():
                map_number = atom.GetAtomMapNum()

                if map_number != 0:
                    atom_map_to_reactant[map_number] = reactant_idx

        return atom_map_to_reactant

    def _get_source_atom(
        self,
        product_atom,
        atom_map_to_reactant: dict[int, int],
    ) -> tuple[int, int] | None:
        """Find the reactant molecule and atom that produced a product atom."""

        if not product_atom.HasProp("react_atom_idx"):
            return None

        reactant_atom_idx = product_atom.GetIntProp("react_atom_idx")

        if product_atom.HasProp("old_mapno"):
            map_number = product_atom.GetIntProp("old_mapno")

            reactant_idx = atom_map_to_reactant.get(map_number)

            if reactant_idx is None:
                return None

            return reactant_idx, reactant_atom_idx

        if product_atom.HasProp("reactant_idx"):
            return (
                product_atom.GetIntProp("reactant_idx"),
                reactant_atom_idx,
            )

        return None

    def _build_atom_offsets(
        self,
        molecules,
    ) -> list[int]:
        """Build offsets used to create globally unique atom indices."""

        offsets: list[int] = []
        current_offset = 0

        for molecule in molecules:
            offsets.append(current_offset)
            current_offset += molecule.GetNumAtoms()

        return offsets

    def _collect_reactant_bonds(
        self,
        reactant_mols,
        reactant_offsets: list[int],
    ) -> dict[tuple[int, int], float]:
        """Collect bonds from all reactants using global atom indices."""

        bonds: dict[tuple[int, int], float] = {}

        for reactant_idx, molecule in enumerate(reactant_mols):
            offset = reactant_offsets[reactant_idx]

            for bond in molecule.GetBonds():
                atom1 = offset + bond.GetBeginAtomIdx()
                atom2 = offset + bond.GetEndAtomIdx()

                key = tuple(sorted((atom1, atom2)))

                bonds[key] = float(bond.GetBondTypeAsDouble())

        return bonds

    def _collect_product_bonds(
        self,
        product_mols,
        product_to_reactant_atom: dict[
            tuple[int, int],
            int,
        ],
    ) -> dict[tuple[int, int], float]:
        """
        Collect product bonds using the corresponding reactant atom identities.
        """

        bonds: dict[tuple[int, int], float] = {}

        for product_idx, molecule in enumerate(product_mols):
            for bond in molecule.GetBonds():
                atom1_key = (
                    product_idx,
                    bond.GetBeginAtomIdx(),
                )
                atom2_key = (
                    product_idx,
                    bond.GetEndAtomIdx(),
                )

                if (
                    atom1_key not in product_to_reactant_atom
                    or atom2_key not in product_to_reactant_atom
                ):
                    continue

                atom1 = product_to_reactant_atom[atom1_key]
                atom2 = product_to_reactant_atom[atom2_key]

                key = tuple(sorted((atom1, atom2)))

                bonds[key] = float(bond.GetBondTypeAsDouble())

        return bonds
