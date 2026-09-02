from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.schemas.error_response import ErrorResponse
from app.api.schemas.search_request import MoleculeSearchRequest
from app.api.schemas.search_response import MoleculeResponse, MoleculeSearchResponse
from app.domain.errors import (
    InvalidInputError,
    MoleculeNotFoundError,
    PubChemRateLimitError,
    SearchError,
    TemporaryPubChemError,
)

router = APIRouter()


@router.post("/molecule-search", response_model=MoleculeSearchResponse)
async def molecule_search(request: MoleculeSearchRequest, req: Request):
    try:
        search_service = req.app.state.search_service
        outcome = await search_service.search(request.query, request.input_type)

        molecule_response = MoleculeResponse(
            canonical_smiles=outcome.molecule.canonical_smiles,
            cid=outcome.molecule.cid,
            name=outcome.molecule.name,
            molecular_formula=outcome.molecule.molecular_formula,
            molecular_weight=outcome.molecule.molecular_weight,
            structure_svg=outcome.molecule.structure_svg,
        )

        return MoleculeSearchResponse(
            query=outcome.query,
            requested_input_type=outcome.requested_input_type,
            resolved_input_type=outcome.resolved_input_type,
            warnings=outcome.warnings,
            molecule=molecule_response,
        )

    except InvalidInputError as e:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                category=e.category,
                message=e.message,
                details=None,
            ).model_dump(),
        )

    except MoleculeNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                category=e.category,
                message=e.message,
                details=None,
            ).model_dump(),
        )

    except PubChemRateLimitError as e:
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(
                category=e.category,
                message=e.message,
                details=None,
            ).model_dump(),
        )

    except TemporaryPubChemError as e:
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                category=e.category,
                message=e.message,
                details=None,
            ).model_dump(),
        )

    except SearchError as e:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                category=e.category,
                message=e.message,
                details=None,
            ).model_dump(),
        )
