from fastapi import APIRouter

from app.api.routes.molecule_rendering import router as molecule_rendering_router
from app.api.routes.reaction_prediction import router as reaction_prediction_router
from app.api.routes.reaction_simulation import router as reaction_simulation_router
from app.api.routes.search import router as search_router

api_router = APIRouter()

api_router.include_router(
    search_router,
    prefix="/search",
    tags=["search"],
)

api_router.include_router(
    reaction_simulation_router,
    tags=["reactions"],
)

api_router.include_router(
    reaction_prediction_router,
    tags=["reactions"],
)

api_router.include_router(
    molecule_rendering_router,
    tags=["chemistry"],
)
