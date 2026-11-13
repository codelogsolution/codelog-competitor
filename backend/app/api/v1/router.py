from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.uploads import router as uploads_router
from app.api.v1.endpoints.scoring import router as scoring_router
from app.api.v1.endpoints.research import router as research_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])

api_router.include_router(
    uploads_router,
    prefix="/uploads",
    tags=["Uploads"],
)

api_router.include_router(
    scoring_router,
    prefix="/scoring",
    tags=["Scoring"],
)

api_router.include_router(
    research_router,
    prefix="/research",
    tags=["Research"],
)