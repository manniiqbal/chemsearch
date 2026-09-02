from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.domain.default_reaction_rules import build_default_registry
from app.domain.errors import ReactionError, SearchError
from app.integrations.pubchem_client import PubChemClient
from app.services.prediction_service import ReactionPredictionService
from app.services.rdkit_service import RDKitService
from app.services.reaction_engine import ReactionEngine
from app.services.reaction_mapping_service import ReactionMappingService
from app.services.reaction_service import ReactionService
from app.services.reaction_t5_engine import ReactionT5Engine
from app.services.search_service import SearchService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Shared infrastructure/services
    pubchem_client = PubChemClient()
    rdkit_service = RDKitService()

    # Molecule search
    search_service = SearchService(
        pubchem_client,
        rdkit_service,
    )

    # Reaction simulation
    reaction_rule_registry = build_default_registry()

    reaction_engine = ReactionEngine(
        rdkit_service,
    )

    reaction_service = ReactionService(
        reaction_engine,
        reaction_rule_registry,
    )

    reaction_mapping_service = ReactionMappingService(
        rdkit_service,
    )

    # Reaction prediction
    reaction_t5_engine = ReactionT5Engine(rdkit_service)

    reaction_prediction_service = ReactionPredictionService(
        reaction_t5_engine,
        rdkit_service,
    )

    # Make services available to API routes
    app.state.pubchem_client = pubchem_client
    app.state.rdkit_service = rdkit_service
    app.state.search_service = search_service

    app.state.reaction_rule_registry = reaction_rule_registry
    app.state.reaction_engine = reaction_engine
    app.state.reaction_service = reaction_service
    app.state.reaction_mapping_service = reaction_mapping_service

    app.state.reaction_t5_engine = reaction_t5_engine
    app.state.reaction_prediction_service = reaction_prediction_service

    yield

    await pubchem_client.close()


app = FastAPI(
    lifespan=lifespan,
    title="ChemSearch API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_origin_regex=settings.frontend_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "category": "validation_error",
            "message": "The request contains invalid or missing fields.",
            "details": {"errors": jsonable_encoder(exc.errors())},
        },
    )


@app.exception_handler(SearchError)
@app.exception_handler(ReactionError)
async def domain_error_handler(request: Request, exc: SearchError | ReactionError):
    status_code = 503 if exc.category == "prediction_unavailable" else 400
    return JSONResponse(
        status_code=status_code,
        content={"category": exc.category, "message": exc.message, "details": None},
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(api_router, prefix="/api")
