from fastapi import APIRouter, Request

from app.api.schemas.reaction_request import ReactionSimulationRequest
from app.api.schemas.reaction_response import (
    AtomMappingResponse,
    BondChangeResponse,
    ReactionMappingResponse,
    ReactionParticipantResponse,
    ReactionProductSetResponse,
    ReactionSimulationResponse,
)
from app.domain.reaction import (
    ReactionConditions,
    ReactionParticipant,
    ReactionRequest,
)

router = APIRouter()


@router.post(
    "/reactions/simulate",
    response_model=ReactionSimulationResponse,
)
async def simulate_reaction(
    request: ReactionSimulationRequest,
    req: Request,
):
    reaction_service = req.app.state.reaction_service
    reaction_mapping_service = req.app.state.reaction_mapping_service
    rule_registry = req.app.state.reaction_rule_registry

    domain_request = ReactionRequest(
        reactants=[
            ReactionParticipant(
                canonical_smiles=participant.canonical_smiles,
                coefficient=participant.coefficient,
            )
            for participant in request.reactants
        ],
        reagents=[
            ReactionParticipant(
                canonical_smiles=reagent.canonical_smiles,
                coefficient=reagent.coefficient,
            )
            for reagent in request.reagents
        ],
        reaction_type=request.reaction_type,
        conditions=(
            ReactionConditions(
                temperature_c=request.conditions.temperature_c,
                pressure_bar=request.conditions.pressure_bar,
                duration_minutes=request.conditions.duration_minutes,
                ph=request.conditions.ph,
                solvent=request.conditions.solvent,
                notes=request.conditions.notes,
            )
            if request.conditions is not None
            else None
        ),
    )

    result = reaction_service.simulate_reaction(domain_request)

    product_set_responses = [
        ReactionProductSetResponse(
            products=[
                ReactionParticipantResponse(
                    canonical_smiles=product.canonical_smiles,
                    coefficient=product.coefficient,
                )
                for product in product_set.products
            ],
            rule_id=product_set.rule_id,
            rule_name=product_set.rule_name,
        )
        for product_set in result.product_sets
    ]

    mapping_responses: list[ReactionMappingResponse] = []

    if result.product_sets:
        for product_set in result.product_sets:
            mapping_rule = (
                rule_registry.get_by_id(product_set.rule_id)
                if product_set.rule_id is not None
                else None
            )
            if mapping_rule is not None:
                mapping = reaction_mapping_service.map_reaction(
                    mapping_rule,
                    domain_request.reactants,
                    product_set.products,
                )

                mapping_responses.append(
                    ReactionMappingResponse(
                        atom_mappings=[
                            AtomMappingResponse(
                                reactant_atom_idx=atom_mapping.reactant_atom_idx,
                                product_atom_idx=atom_mapping.product_atom_idx,
                            )
                            for atom_mapping in mapping.atom_mappings
                        ],
                        broken_bonds=[
                            BondChangeResponse(
                                atom1_idx=bond.atom1_idx,
                                atom2_idx=bond.atom2_idx,
                                old_bond_order=bond.old_bond_order,
                                new_bond_order=bond.new_bond_order,
                            )
                            for bond in mapping.broken_bonds
                        ],
                        formed_bonds=[
                            BondChangeResponse(
                                atom1_idx=bond.atom1_idx,
                                atom2_idx=bond.atom2_idx,
                                old_bond_order=bond.old_bond_order,
                                new_bond_order=bond.new_bond_order,
                            )
                            for bond in mapping.formed_bonds
                        ],
                        changed_bonds=[
                            BondChangeResponse(
                                atom1_idx=bond.atom1_idx,
                                atom2_idx=bond.atom2_idx,
                                old_bond_order=bond.old_bond_order,
                                new_bond_order=bond.new_bond_order,
                            )
                            for bond in mapping.changed_bonds
                        ],
                    )
                )

    return ReactionSimulationResponse(
        status=result.status.value,
        reaction_type=result.reaction_type,
        product_sets=product_set_responses,
        warnings=result.warnings,
        mappings=mapping_responses,
    )
