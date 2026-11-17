import logging


from fastapi import APIRouter, HTTPException

from app.schemas.scoring import ScoreRequest, ScoreResponse
from app.services.scoring_service import ScoringService
from app.services.validation_service import ValidationService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/score", response_model=ScoreResponse)
def score_competitors(payload: ScoreRequest):
    try:
        validation = ValidationService.validate_records(payload.records)
        return ScoringService.score_competitors(validation["records"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Competitor scoring endpoint failed")
        raise HTTPException(
            status_code=500,
            detail="Competitor scoring failed. Check application logs for details.",
        ) from exc
