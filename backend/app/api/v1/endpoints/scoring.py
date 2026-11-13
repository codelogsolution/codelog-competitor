
from fastapi import APIRouter, HTTPException

from app.schemas.scoring import ScoreRequest, ScoreResponse
from app.services.scoring_service import ScoringService

router = APIRouter()


@router.post("/score", response_model=ScoreResponse)
def score_competitors(payload: ScoreRequest):
    try:
        return ScoringService.score_competitors(payload.records)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Competitor scoring failed: {str(exc)}",
        ) from exc
