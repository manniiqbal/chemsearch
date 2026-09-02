from fastapi import APIRouter, Request

from app.api.schemas.molecule_render import (
    MoleculeRenderRequest,
    MoleculeRenderResponse,
    ReactionRuleResponse,
)

router = APIRouter()


@router.post("/molecules/render", response_model=MoleculeRenderResponse)
async def render_molecule(payload: MoleculeRenderRequest, request: Request):
    rdkit_service = request.app.state.rdkit_service
    canonical = rdkit_service.canonicalise_molecule(payload.smiles)
    return MoleculeRenderResponse(
        canonical_smiles=canonical,
        svg=rdkit_service.render_molecule_svg(
            canonical,
            size=(payload.width, payload.height),
        ),
    )


@router.get("/reactions/rules", response_model=list[ReactionRuleResponse])
async def list_reaction_rules(request: Request):
    return [
        ReactionRuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            reaction_type=rule.reaction_type,
            reactant_count=rule.reactant_count,
            description=rule.description,
        )
        for rule in request.app.state.reaction_rule_registry.list_all()
    ]
