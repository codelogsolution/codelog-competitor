from fastapi import APIRouter

from app.api.v1.endpoints import health, uploads
from app.api.v1.endpoints.scoring import router as scoring_router

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(uploads.router)
api_router.include_router(
    scoring_router,
    prefix="/scoring",
    tags=["Scoring"],
)