from app.domain.default_reaction_rules import ALKENE_HYDROGENATION
from app.domain.reaction import ReactionParticipant
from app.services.rdkit_service import RDKitService
from app.services.reaction_mapping_service import ReactionMappingService


def test_hydrogenation_detects_bond_order_change():
    rdkit_service = RDKitService()
    mapping_service = ReactionMappingService(rdkit_service)

    reactants = [ReactionParticipant(canonical_smiles="C=C")]

    products = [ReactionParticipant(canonical_smiles="CC")]

    result = mapping_service.map_reaction(
        ALKENE_HYDROGENATION,
        reactants,
        products,
    )

    assert len(result.atom_mappings) == 2
    assert result.broken_bonds == []
    assert result.formed_bonds == []

    assert len(result.changed_bonds) == 1

    bond_change = result.changed_bonds[0]

    assert bond_change.old_bond_order == 2.0
    assert bond_change.new_bond_order == 1.0
